from __future__ import annotations

from typing import List, Dict, Any
try:
    from .models import GatewayConfig
except Exception:
    from models import GatewayConfig


def _severity_for_missing(key: str) -> str:
    return "critical" if key == "api_key" else "warning"


def advise(config: GatewayConfig, providers: List[Dict[str, Any]] | None = None) -> List[Dict[str, str]]:
    """Return a list of explainable advisory hints.

    Each hint is a dict with keys: `id`, `severity`, `message` so the UI
    can render it with appropriate prominence.
    """
    hints: List[Dict[str, str]] = []

    # Temperature rule
    if config.temperature is not None and config.temperature > 1.2:
        hints.append({
            "id": "temperature_high",
            "severity": "warning",
            "message": "Temperature is unusually high; consider lowering for deterministic responses.",
        })

    # Model list rules
    if not config.model_list:
        hints.append({
            "id": "no_models",
            "severity": "critical",
            "message": "No models configured; add at least one provider/model.",
        })
    else:
        names = [m.model_name for m in config.model_list]
        for item in config.model_list:
            p = item.litellm_params
            if not p.api_key:
                hints.append({
                    "id": "missing_api_key",
                    "severity": _severity_for_missing("api_key"),
                    "message": f"Missing API key for model '{item.model_name}'.",
                })
            if not p.api_base:
                hints.append({
                    "id": "missing_api_base",
                    "severity": "warning",
                    "message": f"Missing api_base for model '{item.model_name}'.",
                })

        # Fallback check
        if len(config.model_list) < 2:
            hints.append({
                "id": "no_fallback",
                "severity": "warning",
                "message": "No fallback provider configured; consider adding a second model/provider.",
            })

        # Primary provider exists in list?
        if config.provider and config.provider not in names:
            hints.append({
                "id": "unknown_provider",
                "severity": "warning",
                "message": "Primary provider is not defined in model_list; check `provider` value.",
            })

    # Provider runtime hints (if topology snapshot provided)
    if providers:
        for p in providers:
            if p.get("status") and p.get("status") != "Healthy":
                hints.append({
                    "id": "provider_unhealthy",
                    "severity": "warning",
                    "message": f"Provider {p.get('name')} reports status {p.get('status')}.",
                })

    return hints


__all__ = ["advise"]
