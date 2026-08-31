from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

TAG_PATTERN = re.compile(r"{{\s*([A-Za-z][A-Za-z0-9_]*)\s*}}")


class CertificateError(Exception):
    """Raised when supplied certificate data cannot be rendered safely."""


@dataclass(frozen=True)
class Mapping:
    source: str
    field: str


def extract_variables(texts: Iterable[str]) -> set[str]:
    """Return unique variable names used in `{{VARIABLE}}` placeholders."""
    return {match.group(1) for text in texts for match in TAG_PATTERN.finditer(text)}


def parse_mappings(raw: dict[str, Any] | None) -> dict[str, Mapping]:
    """Validate the optional manifest variable mapping."""
    if raw is None:
        return {}
    result: dict[str, Mapping] = {}
    for variable, value in raw.items():
        if not isinstance(value, dict):
            raise CertificateError(f"Mapping for {variable!r} must be an object.")
        source = value.get("source")
        field = value.get("value") if source == "value" else value.get("column")
        if source not in {"row", "value"} or not isinstance(field, str) or not field:
            raise CertificateError(
                f"Mapping for {variable!r} needs source 'row' or 'value' and "
                "a non-empty column/value."
            )
        result[variable] = Mapping(source, field)
    return result


def build_context(variables: set[str], row: dict[str, str], mappings: dict[str, Mapping]) -> dict[str, str]:
    """Resolve template fields from the current row and optional mapping values."""
    context: dict[str, str] = {}
    missing: list[str] = []
    for variable in sorted(variables):
        mapping = mappings.get(variable)
        if mapping:
            value = mapping.field if mapping.source == "value" else row.get(mapping.field)
        else:
            value = row.get(variable)
        if value is None or not str(value).strip():
            missing.append(variable)
        else:
            context[variable] = str(value).strip()
    if missing:
        raise CertificateError("Missing values for: " + ", ".join(missing))
    return context


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    value = value.strip(".-")
    return value or "certificate"
