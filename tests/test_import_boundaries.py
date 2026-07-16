# SPDX-License-Identifier: BSD-3-Clause
"""Import-boundary guard for the modular ``soju`` package layout.

Walks ``src/soju/**/*.py`` with :mod:`ast` and encodes the dependency rules from
the modularization plan (§3): layering must hold as code lands in the new
packages. Current flat modules (``db``, ``intake``, …) are ignored until moved.
"""

from __future__ import annotations

import ast
from pathlib import Path

SOJU_SRC = Path(__file__).resolve().parents[1] / "src" / "soju"

# Top-level packages introduced by the modularization (Phase 0 scaffolding).
LAYER_PACKAGES = frozenset(
    {
        "core",
        "base",
        "registry",
        "levels",
        "llm",
        "languages",
        "prompts",
        "services",
        "cli",
    }
)

# (importer module-prefix, forbidden import-prefixes)
#
# Matches plan §3 / §12:
# - core depends on nothing in soju except _version (pure leaf; no plugin
#   resolvers). Plugin-aware key builders live in soju.services.keys.
# - base depends on core only (not languages/registry/services/cli/…)
# - registry must not import languages or base
# - languages must not import services or cli
# - services must not import concrete plugins or cli
# - nothing imports cli
# - generic layers must not import soju.languages.korean / soju.base.english
_FORBIDDEN: list[tuple[str, tuple[str, ...]]] = [
    (
        "soju.core",
        (
            "soju.base",
            "soju.languages",
            "soju.registry",
            "soju.levels",
            "soju.llm",
            "soju.prompts",
            "soju.services",
            "soju.cli",
        ),
    ),
    (
        "soju.base",
        (
            "soju.languages",
            "soju.registry",
            "soju.services",
            "soju.cli",
            "soju.levels",
            "soju.llm",
            "soju.prompts",
        ),
    ),
    (
        "soju.registry",
        (
            "soju.languages",
            "soju.base",
            "soju.services",
            "soju.cli",
            "soju.levels",
            "soju.llm",
            "soju.prompts",
        ),
    ),
    (
        "soju.levels",
        (
            "soju.languages",
            "soju.base",
            "soju.services",
            "soju.cli",
            "soju.llm",
            "soju.prompts",
        ),
    ),
    (
        "soju.llm",
        (
            "soju.languages",
            "soju.base",
            "soju.registry",
            "soju.services",
            "soju.cli",
            "soju.levels",
            "soju.prompts",
        ),
    ),
    (
        "soju.prompts",
        (
            "soju.languages",
            "soju.base",
            "soju.registry",
            "soju.services",
            "soju.cli",
            "soju.llm",
        ),
    ),
    (
        "soju.languages",
        (
            "soju.services",
            "soju.cli",
            # Target plugins reach base only via soju.base.get_base_language(),
            # never a concrete base package (e.g. soju.base.english).
            "soju.base.english",
        ),
    ),
    (
        "soju.services",
        (
            "soju.cli",
            "soju.languages.korean",
            "soju.base.english",
        ),
    ),
    (
        "soju.cli",
        (
            "soju.languages.korean",
            "soju.base.english",
        ),
    ),
]

# Concrete plugins may only be imported from within their own package (or, for
# Korean, from the languages package root/plugins for registration bootstrap).
_CONCRETE_PLUGIN_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("soju.base.english", ("soju.base.english", "soju.base", "soju.core")),
    ("soju.languages.korean", ("soju.languages.korean", "soju.languages", "soju.core")),
]


def _module_name(path: Path) -> str:
    rel = path.relative_to(SOJU_SRC)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return "soju." + ".".join(parts) if parts else "soju"


def _iter_soju_modules() -> list[tuple[str, Path]]:
    modules: list[tuple[str, Path]] = []
    for path in sorted(SOJU_SRC.rglob("*.py")):
        if path.name == "_version.py":
            continue
        modules.append((_module_name(path), path))
    return modules


def _imported_modules(tree: ast.AST) -> set[str]:
    """Return fully-qualified ``soju…`` module names referenced by import nodes."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "soju" or alias.name.startswith("soju."):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            if node.module == "soju" or node.module.startswith("soju."):
                found.add(node.module)
                # Also record child modules for ``from soju.x import y`` when y
                # is a submodule name used as a package path elsewhere.
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    child = f"{node.module}.{alias.name}"
                    found.add(child)
    return found


def _is_under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def _layer_of(module: str) -> str | None:
    """Return the top-level layer package for a modular module, else None."""
    if not module.startswith("soju."):
        return None
    rest = module[len("soju.") :]
    top = rest.split(".", 1)[0]
    return top if top in LAYER_PACKAGES else None


def test_scaffolded_layer_packages_exist() -> None:
    """Phase-0 empty packages are present under ``src/soju/``."""
    for name in sorted(LAYER_PACKAGES):
        init = SOJU_SRC / name / "__init__.py"
        assert init.is_file(), f"missing package {name}: {init}"
    assert (SOJU_SRC / "base" / "english" / "__init__.py").is_file()
    assert (SOJU_SRC / "languages" / "korean" / "__init__.py").is_file()
    assert (SOJU_SRC / "services" / "validation" / "__init__.py").is_file()


def test_import_boundaries() -> None:
    """Static imports among modular packages obey the §3 dependency rules."""
    violations: list[str] = []

    for module, path in _iter_soju_modules():
        layer = _layer_of(module)
        if layer is None:
            # Flat legacy modules are out of scope until moved into layers.
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(f"{module}: syntax error: {exc}")
            continue

        imported = _imported_modules(tree)

        # Universal: nothing imports cli.
        for imp in sorted(imported):
            if _is_under(imp, "soju.cli") and not _is_under(module, "soju.cli"):
                violations.append(f"{module} imports {imp} (nothing may import cli)")

        # Layer forbidden-prefix rules.
        for importer_prefix, forbidden in _FORBIDDEN:
            if not _is_under(module, importer_prefix):
                continue
            for imp in sorted(imported):
                for bad in forbidden:
                    if _is_under(imp, bad):
                        violations.append(f"{module} imports {imp} (forbidden by {importer_prefix} → {bad})")

        # Concrete plugin isolation (generic layers already covered; also block
        # cross-imports from unrelated language packages later).
        for plugin, allowed_prefixes in _CONCRETE_PLUGIN_RULES:
            for imp in sorted(imported):
                if not _is_under(imp, plugin):
                    continue
                if any(_is_under(module, allowed) for allowed in allowed_prefixes):
                    continue
                violations.append(f"{module} imports concrete plugin {imp} (only {allowed_prefixes} may)")

    assert not violations, "Import boundary violations:\n" + "\n".join(f"  - {v}" for v in violations)


def test_core_does_not_import_other_soju_packages() -> None:
    """``soju.core`` is a pure leaf: only itself and ``_version`` are allowed."""
    allowed_prefixes = (
        "soju.core",
        "soju._version",
    )
    violations: list[str] = []
    for module, path in _iter_soju_modules():
        if not _is_under(module, "soju.core"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imp in sorted(_imported_modules(tree)):
            if imp == "soju":
                continue
            if any(_is_under(imp, allowed) for allowed in allowed_prefixes):
                continue
            if imp.startswith("soju."):
                violations.append(f"{module} imports {imp}")
    assert not violations, "core import violations:\n" + "\n".join(f"  - {v}" for v in violations)
