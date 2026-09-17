"""Read-only firewall and network diagnostics for local host handshakes."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socket
import ssl
import subprocess
import time
from pathlib import Path
from typing import Any


def run_command(command: list[str], timeout: float) -> dict[str, Any]:
    """Run a bounded diagnostic command and retain only a capped text sample."""
    if not shutil.which(command[0]):
        return {"status": "unsupported", "command": command}
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": command}
    except OSError as exc:
        return {"status": "error", "command": command, "error": str(exc)}
    output = (completed.stdout or completed.stderr).strip()
    return {
        "status": "ok" if completed.returncode == 0 else "nonzero",
        "returncode": completed.returncode,
        "command": command,
        "sample": output[:4000],
        "truncated": len(output) > 4000,
    }


def firewall_snapshot(timeout: float) -> dict[str, Any]:
    """Inspect available firewall frontends without changing their state."""
    candidates = {
        "ufw": ["ufw", "status", "verbose"],
        "nftables": ["nft", "list", "ruleset"],
        "firewalld": ["firewall-cmd", "--state"],
        "iptables": ["iptables", "-S"],
        "windows": ["netsh", "advfirewall", "show", "allprofiles"],
        "mac_pf": ["pfctl", "-s", "info"],
    }
    return {name: run_command(command, timeout) for name, command in candidates.items()}


def system_snapshot(timeout: float) -> dict[str, Any]:
    """Collect bounded interface, route, DNS, and listener diagnostics."""
    system = platform.system().lower()
    commands: dict[str, list[str]] = {
        "interfaces": ["ip", "-brief", "address"] if system == "linux" else ["ifconfig"],
        "routes": ["ip", "route"] if system == "linux" else ["route", "-n", "get", "default"],
        "listeners": ["ss", "-ltnp"] if system == "linux" else ["netstat", "-an"],
    }
    if system == "windows":
        commands = {
            "interfaces": ["ipconfig", "/all"],
            "routes": ["route", "print"],
            "listeners": ["netstat", "-ano"],
        }
    return {name: run_command(command, timeout) for name, command in commands.items()}


def probe_target(host: str, port: int, timeout: float, tls_probe: bool = False) -> dict[str, Any]:
    """Resolve and optionally connect to one host without sending application data."""
    started = time.monotonic()
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return {"host": host, "port": port, "status": "dns_error", "error": str(exc)}
    address_families = sorted({address[0].name for address in addresses})
    connected = False
    error = None
    for family, _, _, _, sockaddr in addresses:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as connection:
                connection.settimeout(timeout)
                connection.connect(sockaddr)
                if tls_probe:
                    context = ssl.create_default_context()
                    with context.wrap_socket(connection, server_hostname=host):
                        pass
                connected = True
                break
        except OSError as exc:
            error = str(exc)
    return {
        "host": host,
        "port": port,
        "status": "reachable" if connected else "unreachable",
        "address_families": address_families,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
        **({"error": error} if error else {}),
    }


def collect(timeout: float, targets: list[str], tls_probe: bool) -> dict[str, Any]:
    """Build a redaction-free, bounded diagnostic snapshot."""
    probes = []
    for target in targets:
        host, separator, port_text = target.rpartition(":")
        if not separator or not host or not port_text.isdigit():
            probes.append({"target": target, "status": "invalid_target", "expected": "host:port"})
            continue
        port = int(port_text)
        probes.append(probe_target(host, port, timeout, tls_probe))
    return {
        "status": "ok",
        "platform": platform.platform(),
        "system": platform.system(),
        "cwd": str(Path.cwd()),
        "network": system_snapshot(timeout),
        "firewall": firewall_snapshot(timeout),
        "probes": probes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", default=[], help="Bounded reachability target, e.g. chatgpt.com:443")
    parser.add_argument("--tls", action="store_true", help="Complete a TLS handshake for each target")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--json", action="store_true", help="Retained for explicit machine-readable invocation")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    print(json.dumps(collect(args.timeout, args.target, args.tls), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
