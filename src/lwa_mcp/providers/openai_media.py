from __future__ import annotations

import base64
import time
from pathlib import Path

import httpx

from ..config import STATE_DIR
from ..models import Capability, CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderError, redact_error
from .openai_compatible import OpenAICompatibleAdapter


class OpenAIMediaAdapter(OpenAICompatibleAdapter):
    """Official OpenAI image and asynchronous video generation endpoints."""

    def _media_key(self) -> str:
        _, value = self.credential()
        return value

    def _media_headers(self) -> dict[str, str]:
        key = self._media_key()
        if not key:
            raise ProviderError("openai: missing API key")
        return {"Authorization": f"Bearer {key}"}

    @staticmethod
    def _media_dir() -> Path:
        path = STATE_DIR / "generated"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        if Capability.VIDEO in candidate.capabilities:
            return await self._video(candidate, request)
        if Capability.IMAGE in candidate.capabilities:
            return await self._image(candidate, request)
        return await super().complete(candidate, request)

    async def _image(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        aspect = request.metadata.get("aspect_ratio", "1:1")
        size = {"1:1": "1024x1024", "16:9": "1536x1024", "9:16": "1024x1536"}.get(
            aspect, "1024x1024"
        )
        payload = {
            "model": candidate.model,
            "prompt": request.prompt,
            "size": size,
            "output_format": request.metadata.get("output_format", "png"),
        }
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                self._base() + "/images/generations",
                headers={**self._media_headers(), "Content-Type": "application/json"},
                json=payload,
            )
        if response.status_code >= 400:
            raise ProviderError(
                f"openai image HTTP {response.status_code}: {redact_error(response.text[:1000])}"
            )
        item = (response.json().get("data") or [{}])[0]
        path = self._media_dir() / f"openai-image-{int(time.time())}.{payload['output_format']}"
        if item.get("b64_json"):
            path.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                media = await client.get(item["url"])
            media.raise_for_status()
            path.write_bytes(media.content)
        else:
            raise ProviderError("openai image response contained neither image data nor URL")
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=str(path),
            latency_ms=int((time.perf_counter() - started) * 1000),
            response_id=item.get("revised_prompt"),
        )

    async def _video(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        seconds = str(request.metadata.get("seconds", "4"))
        size = str(request.metadata.get("size", "1280x720"))
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                self._base() + "/videos",
                headers=self._media_headers(),
                data={"model": candidate.model, "prompt": request.prompt, "seconds": seconds, "size": size},
            )
            if response.status_code >= 400:
                raise ProviderError(
                    f"openai video HTTP {response.status_code}: {redact_error(response.text[:1000])}"
                )
            job = response.json()
            job_id = job.get("id")
            if not job_id:
                raise ProviderError("openai video response did not contain a job id")
            deadline = time.monotonic() + self.config.timeout_seconds
            while job.get("status") not in {"completed", "failed", "cancelled"}:
                if time.monotonic() >= deadline:
                    raise ProviderError("openai video generation timed out")
                await __import__("asyncio").sleep(2)
                status_response = await client.get(
                    f"{self._base()}/videos/{job_id}", headers=self._media_headers()
                )
                if status_response.status_code >= 400:
                    raise ProviderError(
                        f"openai video status HTTP {status_response.status_code}: "
                        f"{redact_error(status_response.text[:1000])}"
                    )
                job = status_response.json()
            if job.get("status") != "completed":
                raise ProviderError(f"openai video job {job_id} ended with {job.get('status')}")
            media = await client.get(
                f"{self._base()}/videos/{job_id}/content", headers=self._media_headers()
            )
            if media.status_code >= 400:
                raise ProviderError(
                    f"openai video content HTTP {media.status_code}: "
                    f"{redact_error(media.text[:1000])}"
                )
        path = self._media_dir() / f"openai-video-{job_id}.mp4"
        path.write_bytes(media.content)
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=str(path),
            latency_ms=int((time.perf_counter() - started) * 1000),
            response_id=job_id,
            raw_usage={"status": job.get("status"), "seconds": seconds, "size": size},
        )
