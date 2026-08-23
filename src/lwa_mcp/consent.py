from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time

from .models import PendingRoute, RouteDecision, RouteRequest


class ConsentGate:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._secret = os.getenv("CASTOR_POLLUX_CONFIRMATION_SECRET", secrets.token_hex(32)).encode()
        self._pending: dict[str, PendingRoute] = {}

    def issue(self, request: RouteRequest, decision: RouteDecision) -> str:
        nonce = secrets.token_urlsafe(18)
        material = json.dumps(
            {
                "nonce": nonce,
                "provider": decision.candidate.provider,
                "model": decision.candidate.model,
                "task": request.task.value,
                "expires": int(time.time() + self.ttl_seconds),
            },
            sort_keys=True,
        )
        signature = hmac.new(self._secret, material.encode(), hashlib.sha256).hexdigest()[:24]
        token = f"{nonce}.{signature}"
        self._pending[token] = PendingRoute(
            token=token,
            request=request,
            decision=decision,
            expires_at_epoch=time.time() + self.ttl_seconds,
        )
        return token

    def consume(self, token: str) -> PendingRoute:
        pending = self._pending.pop(token, None)
        if not pending:
            raise ValueError("Unknown or already-used confirmation token")
        if pending.expires_at_epoch < time.time():
            raise ValueError("Confirmation token expired")
        return pending

    def purge(self) -> None:
        now = time.time()
        for token in [t for t, p in self._pending.items() if p.expires_at_epoch < now]:
            self._pending.pop(token, None)
