from pathlib import Path

from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.models import (
    BillingClass,
    Capability,
    ModelCandidate,
    ProviderConfig,
    SubscriptionStatus,
)
from lwa_mcp.service import RouterService


def test_model_tiers_are_ranked_by_free_plan_tokens(tmp_path: Path):
    service = RouterService(
        LoadedConfig(
            settings=RouterSettings(
                providers={
                    "gemini": ProviderConfig(
                        name="gemini",
                        subscription_plan="Gemini Pro",
                        subscription_status=SubscriptionStatus.ACTIVE,
                        subscription_monthly_token_limit=1_000_000,
                    ),
                    "openai": ProviderConfig(
                        name="openai",
                        subscription_plan="ChatGPT Plus",
                        subscription_status=SubscriptionStatus.ACTIVE,
                    ),
                },
                models=[
                ModelCandidate(
                    provider="openai",
                    model="small",
                    billing_class=BillingClass.PAID,
                    capabilities={Capability.TEXT},
                    free_plan_max_tokens=100,
                    service_tiers=["priority"],
                    supported_parameters={"response_format"},
                ),
                ModelCandidate(
                    provider="gemini",
                    model="large",
                    billing_class=BillingClass.FREE_QUOTA,
                    capabilities={Capability.TEXT},
                    free_plan_max_tokens=900,
                    pro_plan_max_tokens=5_000,
                    service_tiers=["standard", "turbo"],
                ),
                ],
            ),
            config_path=tmp_path / "router.yaml",
            env_path=tmp_path / "lwa.env",
            db_path=tmp_path / "lwa.sqlite3",
            tool_library_path=tmp_path / "tools",
        )
    )
    rows = service.model_tiers()
    assert [row["model"] for row in rows] == ["large", "small"]
    assert rows[0]["subscription_plan"] == "Gemini Pro"
    assert rows[0]["subscription_status"] == "active"
    assert rows[0]["service_tiers"] == ["standard", "turbo"]
    assert rows[0]["capabilities"] == ["text"]
    assert rows[0]["source"] == "seed"
    assert rows[0]["enabled"] is True
    assert rows[1]["supported_parameters"] == ["response_format"]


def test_model_tiers_put_unknown_free_limits_after_declared_limits(tmp_path: Path):
    service = RouterService(
        LoadedConfig(
            settings=RouterSettings(
                providers={"p": ProviderConfig(name="p")},
                models=[
                    ModelCandidate(provider="p", model="unknown", free_plan_max_tokens=None),
                    ModelCandidate(provider="p", model="known", free_plan_max_tokens=1),
                ],
            ),
            config_path=tmp_path / "router.yaml",
            env_path=tmp_path / "lwa.env",
            db_path=tmp_path / "lwa.sqlite3",
            tool_library_path=tmp_path / "tools",
        )
    )
    assert [row["model"] for row in service.model_tiers()] == ["known", "unknown"]
