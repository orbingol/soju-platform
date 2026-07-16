# SPDX-License-Identifier: BSD-3-Clause
"""YAML load/dump helpers and id generation."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    """Load a YAML file with :func:`yaml.safe_load`.

    Args:
        path: Path to a YAML file.

    Returns:
        The deserialized Python object.
    """
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class _LiteralStr(str):
    """Marker type: emit YAML literal block scalars (|) for example sentences."""


class _ExamplesDumper(yaml.SafeDumper):
    pass


def _literal_str_representer(dumper: yaml.SafeDumper, data: _LiteralStr) -> Any:
    """Represent ``_LiteralStr`` as a literal block scalar."""
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        str(data),
        style="|",
    )


_ExamplesDumper.add_representer(_LiteralStr, _literal_str_representer)


def _annotate_example_literal_strings(data: Any) -> Any:
    """Wrap hangul/english example strings so they dump as literal blocks."""
    if isinstance(data, dict):
        annotated: dict[Any, Any] = {}
        for key, value in data.items():
            if key in ("hangul", "english") and isinstance(value, str):
                annotated[key] = _LiteralStr(value)
            else:
                annotated[key] = _annotate_example_literal_strings(value)
        return annotated
    if isinstance(data, list):
        return [_annotate_example_literal_strings(item) for item in data]
    return data


def write_examples_yaml_with_schema_comment(path: Path, schema_rel: str, data: Any) -> None:
    """Write an examples YAML file with a schema comment and literal-block strings.

    Args:
        path: Destination path.
        schema_rel: Relative ``$schema`` path for the language-server comment.
        data: Examples store mapping to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# yaml-language-server: $schema={schema_rel}\n\n")
        yaml.dump(
            _annotate_example_literal_strings(data),
            handle,
            Dumper=_ExamplesDumper,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=10_000,
        )


def write_yaml_with_schema_comment(path: Path, schema_rel: str, data: Any) -> None:
    """Write a YAML file with a leading yaml-language-server schema comment.

    Args:
        path: Destination path.
        schema_rel: Relative ``$schema`` path for the language-server comment.
        data: Object to serialize with :func:`yaml.safe_dump`.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# yaml-language-server: $schema={schema_rel}\n\n")
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


def new_id() -> str:
    """Return a new random UUID4 string."""
    return str(uuid.uuid4())
