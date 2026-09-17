from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from importlib.resources import files
from pathlib import Path

from .config import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_ENV_FILE,
    DEFAULT_TOOL_LIBRARY_DIR,
    install_default_config,
    load_config,
)
from .credentials import run_credential_wizard
from .models import TaskKind
from .service import RouterService, rank_model_tiers
from .terminal_ui import (
    get_codex_identity,
    render_execution_telemetry,
    render_ledger_telemetry,
    render_preflight,
    render_result,
)
from .tool_library import ToolLibrary


def init_files(force: bool = False, run_wizard: bool = True) -> None:
    install_default_config(overwrite=force)
    DEFAULT_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_ENV_FILE.exists():
        template = files("lwa_mcp").joinpath("defaults/env.example")
        DEFAULT_ENV_FILE.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    DEFAULT_ENV_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    library = ToolLibrary(DEFAULT_TOOL_LIBRARY_DIR)
    print(f"Config: {DEFAULT_CONFIG_FILE}")
    print(f"Secrets: {DEFAULT_ENV_FILE} (mode 0600)")
    print(f"Tool library: {library.root}")
    print(f"Tool catalog: {library.catalog_path}")
    if run_wizard:
        run_credential_wizard(DEFAULT_ENV_FILE, first_run=True)


def _dashboard_executable() -> Path | None:
    executable = shutil.which("lwa-dashboard")
    if executable:
        return Path(executable)
    candidate = Path(sys.executable).with_name("lwa-dashboard")
    return candidate if candidate.exists() else None


def _ensure_dashboard_running(svc: RouterService, timeout_seconds: float = 30.0) -> tuple[bool, str]:
    host = svc.config.settings.dashboard_host
    port = svc.config.settings.dashboard_port
    url = f"http://{host}:{port}"
    if RouterService._dashboard_running(host, port):
        return False, url

    executable = _dashboard_executable()
    if executable is None:
        raise RuntimeError("Unable to locate the lwa-dashboard executable.")

    log_dir = Path(tempfile.gettempdir()) / "lwa-mcp-codex" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "dashboard-launch.log"
    with log_path.open("ab") as log_file:
        subprocess.Popen(
            [str(executable)],
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if RouterService._dashboard_running(host, port):
            return True, url
        time.sleep(0.1)
    raise RuntimeError(f"Dashboard did not become reachable at {url}; see {log_path}")


async def doctor(show_dashboard_url: bool = False) -> int:
    svc = RouterService(load_config())
    dashboard_started = False
    dashboard_url = f"http://{svc.config.settings.dashboard_host}:{svc.config.settings.dashboard_port}"
    if show_dashboard_url:
        dashboard_started, dashboard_url = _ensure_dashboard_running(svc)
    await svc.initialize()
    result = await svc.catalog.refresh(force=True)
    print(f"Catalog models: {result['models']} ({result['refreshed']} live refreshes)")
    for row in svc.providers_json():
        if row["experimental"]:
            state = "EXPERIMENTAL"
        elif row["enabled"] and row["configured"]:
            state = "READY"
        else:
            state = "MISSING/DISABLED"
        print(
            f"{state:16} {row['name']:14} adapter={row['adapter']} "
            f"billing={row['billing_class']}"
        )
        if row["disabled_reason"]:
            print(f"                 reason={row['disabled_reason']}")
    library = svc.library.summary()
    print(
        f"Tool library: {library['root']} "
        f"({library['active']} active, {library['draft']} draft, {library['generated']} generated)"
    )
    print(f"Detected workflow patterns: {len(svc.db.list_workflow_patterns(500))}")
    if show_dashboard_url:
        state = "started" if dashboard_started else "already running"
        print(f"Dashboard URL: {dashboard_url} ({state})")
    return 0


def print_model_tiers(limit: int = 100) -> int:
    config = load_config()
    print(
        json.dumps(
            rank_model_tiers(config.settings.models, config.settings.providers, limit),
            indent=2,
        )
    )
    return 0


def print_telemetry(codex_model: str | None = None, codex_reasoning: str | None = None) -> int:
    status = RouterService().status()
    print(render_ledger_telemetry(status, get_codex_identity(codex_model, codex_reasoning)))
    return 0


async def _finish_preflight_cli(
    svc: RouterService,
    prepared: dict,
    *,
    structured: bool = False,
    codex_model: str | None = None,
    codex_reasoning: str | None = None,
) -> dict:
    """Print preflight first; emit Working only after the plan is approved and locked."""
    identity = get_codex_identity(codex_model, codex_reasoning)
    print(
        render_preflight(prepared, identity) if structured else json.dumps(prepared, indent=2),
        flush=True,
    )
    if prepared.get("phase") != "preflight_complete":
        return prepared
    preflight = prepared.get("preflight") or {}
    if prepared.get("status") == "confirmation_required":
        if not sys.stdin.isatty():
            return prepared
        answer = input("[LWA] Approve this locked preflight? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            return prepared
        approved = svc.approve_preflight(preflight["confirmation_token"])
        print(
            render_preflight(approved, identity) if structured else json.dumps(approved, indent=2),
            flush=True,
        )
        preflight = approved["preflight"]
    if not preflight.get("working_may_begin"):
        return prepared
    print("[LWA] WORKING · provider execution started", flush=True) if structured else print("Working...", flush=True)
    result = await svc.run_prepared_task(preflight["plan_token"])
    if structured and result.get("status") == "completed":
        print(render_execution_telemetry(result, identity), flush=True)
        print(render_result(result, identity), flush=True)
    return result


async def run_task(args: argparse.Namespace) -> int:
    svc = RouterService()
    request = svc.build_request(
        TaskKind(args.task),
        args.prompt,
        quality=args.quality,
        reasoning_effort=args.reasoning_effort,
        allow_paid=args.allow_paid,
        allow_user_pays=args.allow_user_pays,
        metadata={
            "workflow_name": args.workflow_name,
            "workflow_description": args.workflow_description,
            "project": args.project,
            "workflow_tags": args.tag or [],
        },
    )
    prepared = await svc.prepare_task(request)
    result = await _finish_preflight_cli(
        svc,
        prepared,
        structured=not args.json,
        codex_model=args.codex_model,
        codex_reasoning=args.codex_reasoning,
    )
    if result is not prepared and args.json:
        print(json.dumps(result, indent=2))
    return 0


def _read_input(value: str) -> str:
    return sys.stdin.read() if value == "-" else value


async def library_command(args: argparse.Namespace) -> int:
    svc = RouterService()
    await svc.initialize()
    command = args.library_command
    if command == "list":
        payload = svc.list_library_tools(args.status or None)
    elif command == "search":
        payload = svc.library.search(
            args.query,
            task=TaskKind(args.task) if args.task else None,
            limit=args.limit,
            active_only=not args.include_inactive,
        )
    elif command == "show":
        payload = svc.read_library_tool(args.slug)
    elif command == "run":
        payload = await svc.run_library_tool(
            args.slug,
            _read_input(args.input),
            quality=args.quality,
            reasoning_effort=args.reasoning_effort,
            allow_paid=args.allow_paid,
            allow_user_pays=args.allow_user_pays,
        )
        if payload.get("phase") == "preflight_complete":
            result = await _finish_preflight_cli(svc, payload)
            if result is not payload:
                payload = result
    elif command == "observe":
        payload = svc.observe_workflow(
            workflow_name=args.name,
            description=args.description,
            task=TaskKind(args.task),
            sample=args.sample,
            project=args.project or None,
            success=not args.failed,
            tags=args.tag or [],
        )
    elif command == "analyze":
        payload = svc.analyze_workflow_patterns(args.limit)
    elif command == "catalog":
        payload = {"catalog": str(svc.library.rebuild_catalog())}
    elif command == "disable":
        payload = svc.set_library_tool_status(args.slug, "disabled")
    elif command == "approve":
        payload = svc.set_library_tool_status(args.slug, "active", approved=True)
    else:  # pragma: no cover - argparse prevents this
        raise ValueError(command)
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lwa-router")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser(
        "init",
        help="Install config, protected key file, tool library, and first-run key wizard",
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="Replace router config; never erases the secret file",
    )
    init.add_argument(
        "--no-key-wizard",
        action="store_true",
        help="Skip the interactive first-run credential wizard",
    )
    keys = sub.add_parser(
        "keys", help="Run the visible-input credential discovery and setup wizard"
    )
    keys.add_argument(
        "--retry-configured",
        action="store_true",
        help="Re-enter existing credentials to replace a rejected or rotated key",
    )
    doctor_cmd = sub.add_parser("doctor", help="Probe configured providers, catalogs, patterns, and library")
    doctor_cmd.add_argument(
        "--show-dashboard-url",
        action="store_true",
        help="Start the dashboard if needed and print its URL",
    )
    tiers = sub.add_parser("tiers", help="List models ranked by declared free-plan token capacity")
    tiers.add_argument("--limit", type=int, default=100)
    telemetry = sub.add_parser("telemetry", help="Show recent Lwa routing, token, spend, and quota telemetry")
    telemetry.add_argument("--codex-model", help="Primary Codex model label for terminal display")
    telemetry.add_argument("--codex-reasoning", help="Primary Codex reasoning level for terminal display")

    task = sub.add_parser("run", help="Run one routed task")
    task.add_argument("task", choices=[item.value for item in TaskKind])
    task.add_argument("prompt")
    task.add_argument("--quality", choices=["economy", "balanced", "high"], default="balanced")
    task.add_argument("--reasoning-effort", choices=["instant", "medium", "high"])
    task.add_argument("--allow-paid", action=argparse.BooleanOptionalAction, default=True)
    task.add_argument("--allow-user-pays", action=argparse.BooleanOptionalAction, default=True)
    task.add_argument("--workflow-name")
    task.add_argument("--workflow-description")
    task.add_argument("--project")
    task.add_argument("--tag", action="append")
    task.add_argument("--codex-model", help="Primary Codex model label for terminal display")
    task.add_argument("--codex-reasoning", help="Primary Codex reasoning level for terminal display")
    task.add_argument("--json", action="store_true", help="Use the legacy machine-readable JSON output")

    library = sub.add_parser("library", help="Access the persistent cross-project tool library")
    library_sub = library.add_subparsers(dest="library_command", required=True)

    listing = library_sub.add_parser("list", help="List reusable tools")
    listing.add_argument("--status", choices=["active", "draft", "disabled", "archived"])

    search = library_sub.add_parser(
        "search", help="Search tools by context, task, tags, or triggers"
    )
    search.add_argument("query")
    search.add_argument("--task", choices=[item.value for item in TaskKind])
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--include-inactive", action="store_true")

    show = library_sub.add_parser("show", help="Read a tool manifest and README")
    show.add_argument("slug")

    run = library_sub.add_parser("run", help="Execute an active library tool")
    run.add_argument("slug")
    run.add_argument("--input", required=True, help="Input text, or '-' to read standard input")
    run.add_argument("--quality", choices=["economy", "balanced", "high"], default="balanced")
    run.add_argument("--reasoning-effort", choices=["instant", "medium", "high"])
    run.add_argument("--allow-paid", action=argparse.BooleanOptionalAction, default=True)
    run.add_argument("--allow-user-pays", action=argparse.BooleanOptionalAction, default=True)

    observe = library_sub.add_parser("observe", help="Record one repeated workflow occurrence")
    observe.add_argument("--name", required=True)
    observe.add_argument("--description", required=True)
    observe.add_argument("--task", required=True, choices=[item.value for item in TaskKind])
    observe.add_argument("--sample", default="")
    observe.add_argument("--project", default="")
    observe.add_argument("--tag", action="append")
    observe.add_argument("--failed", action="store_true")

    analyze = library_sub.add_parser("analyze", help="Detect eligible patterns and scaffold tools")
    analyze.add_argument("--limit", type=int, default=100)

    library_sub.add_parser("catalog", help="Rebuild CATALOG.md")
    approve = library_sub.add_parser("approve", help="Approve and activate a reviewed tool")
    approve.add_argument("slug")
    disable = library_sub.add_parser("disable", help="Disable a tool without deleting it")
    disable.add_argument("slug")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "init":
        init_files(args.force, not args.no_key_wizard)
    elif args.command == "keys":
        run_credential_wizard(DEFAULT_ENV_FILE, retry_configured=args.retry_configured)
    elif args.command == "doctor":
        raise SystemExit(asyncio.run(doctor(args.show_dashboard_url)))
    elif args.command == "tiers":
        raise SystemExit(print_model_tiers(args.limit))
    elif args.command == "telemetry":
        raise SystemExit(print_telemetry(args.codex_model, args.codex_reasoning))
    elif args.command == "run":
        raise SystemExit(asyncio.run(run_task(args)))
    elif args.command == "library":
        raise SystemExit(asyncio.run(library_command(args)))


if __name__ == "__main__":
    main()
