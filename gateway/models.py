from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, SecretStr


class LiteLLMParams(BaseModel):
    model: str
    api_base: Optional[HttpUrl] = None
    api_key: Optional[SecretStr] = None

    """Low-level transport/auth configuration for a single LiteLLM provider.

    Notes:
    - `api_base` is validated as a URL when present.
    - `api_key` is stored as `SecretStr` so it is hidden from plain repr.
    """


class ModelItem(BaseModel):
    model_name: str = Field(..., description="Logical provider name, e.g. 'openai' or 'anthropic'")
    litellm_params: LiteLLMParams

    """A single model/provider entry in the gateway configuration."""


class GatewayConfig(BaseModel):
    """Trusted gateway configuration object (Pydantic-v2).

    This model represents the application boundary: all YAML uploaded by
    users is parsed by `yaml.safe_load()` and then validated into this
    structure. Downstream components must only trust values that come from
    `GatewayConfig` instances.
    """

    alias: Optional[str] = Field(None, description="Human-friendly alias for this gateway")
    provider: Optional[str] = Field(None, description="Primary provider alias used for routing")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature for LLMs")
    model_list: List[ModelItem] = Field(..., min_length=1, description="Non-empty list of model/provider entries")

    model_config = {
        "extra": "forbid",
        "frozen": False,
    }


__all__ = ["LiteLLMParams", "ModelItem", "GatewayConfig"]
