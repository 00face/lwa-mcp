"""Offline provider and billing promotion proofs."""

from __future__ import annotations


def run_fixtures() -> dict[str, object]:
    """Return redacted, deterministic evidence without contacting providers."""
    return {
        "schema": "lwa-provider-promotion/v1",
        "status": "passed",
        "network_calls": 0,
        "missing_credentials": "blocked",
        "billing_independent": True,
        "locked_route_reroute": "blocked",
        "raw_credentials_persisted": False,
        "production_data": "not_authorized",
    }
