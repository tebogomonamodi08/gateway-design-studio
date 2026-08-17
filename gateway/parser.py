from __future__ import annotations

import yaml
from typing import Any, Dict, Tuple, List
from pydantic import ValidationError

try:
    from .models import GatewayConfig
except Exception:
    from models import GatewayConfig


def parse_yaml_bytes(yaml_bytes: bytes) -> Any:
    data = yaml.safe_load(yaml_bytes)
    return data


def validate_config(data: Any) -> Tuple[GatewayConfig | None, List[Dict[str, str]]]:
    try:
        cfg = GatewayConfig.model_validate(data)
        return cfg, []
    except ValidationError as exc:  # pydantic v2
        errors = []
        for e in exc.errors():
            errors.append({
                "loc": ".".join(map(str, e.get("loc", []))),
                "msg": e.get("msg", ""),
                "type": e.get("type", ""),
            })
        return None, errors


def parse_and_validate(yaml_bytes: bytes) -> Tuple[GatewayConfig | None, List[Dict[str, str]]]:
    data = parse_yaml_bytes(yaml_bytes)
    return validate_config(data)


__all__ = ["parse_and_validate", "parse_yaml_bytes"]

