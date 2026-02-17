from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from bifrost.shared.errors import ConfigError


def as_mapping(value: Any, *, what: str) -> Mapping[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise ConfigError(f"{what} must be a mapping")

    return cast(Mapping[str, Any], value)


def require_str(data: Mapping[str, Any], key: str, *, what: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{what} must have '{key}'")

    return value


def require_int(data: Mapping[str, Any], key: str, *, what: str) -> int:
    value = data.get(key)
    if value is None:
        raise ConfigError(f"{what} must have '{key}'")

    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ConfigError(f"{what} '{key}' must be an int") from e
