# SPDX-License-Identifier: BSD-3-Clause
"""Characterization tests for the public ``soju`` CLI surface.

Pins ``--help`` text / exit codes and cheap dry-runs so CLI flag/defaults
regressions are caught.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

# Exact Typer help baselines. Capture with OLLAMA_* unset for stable defaults.
HELP_CASES: list[tuple[list[str], str]] = [
    (
        ["soju", "import", "--help"],
        """\
Usage: soju import [OPTIONS] COMMAND [ARGS]...

  Import vocabulary into Soju data files.

Options:
  -h, --help  Show this message and exit.

Commands:
  words  Import words into a topic.
  verbs  Import verbs.
""",
    ),
    (
        ["soju", "import", "words", "--help"],
        """\
Usage: soju import words [OPTIONS]

  Import words into a topic.

Options:
  --topic <str>          Topic id from topics manifest  [required]
  --dry-run
  --section <str>        Section id within the topic (required if multiple)
  --file <path>          Plain-text word list file
  --stdin-json           Read JSON records from stdin
  --from-staging <path>  Staging YAML file path
  --level <str>          Course level id from levels.yaml (omit to leave new
                         words unassigned; per-record level wins)
  -h, --help             Show this message and exit.
""",
    ),
    (
        ["soju", "import", "verbs", "--help"],
        """\
Usage: soju import verbs [OPTIONS]

  Import verbs.

Options:
  --dry-run
  --file <path>  Not supported without --stdin-json
  --stdin-json   Read JSON records from stdin
  --level <str>  Course level id from levels.yaml (omit to leave new words
                 unassigned; per-record level wins)
  -h, --help     Show this message and exit.
""",
    ),
    (
        ["soju", "promote", "--help"],
        """\
Usage: soju promote [OPTIONS]

  Promote local topic entries to registry.

Options:
  --topic <str>  Topic id (e.g. family)  [required]
  --dry-run
  -h, --help     Show this message and exit.
""",
    ),
    (
        ["soju", "fill-verbs", "--help"],
        """\
Usage: soju fill-verbs [OPTIONS]

  Generate verb forms and examples for registry verbs.

Options:
  --dry-run
  --fill-empty  Only fill missing forms/examples; leave existing entries
                unchanged
  --strict      Exit non-zero when no verbs were updated (useful in
                automation)
  -h, --help    Show this message and exit.
""",
    ),
    (
        ["soju", "fill-examples", "--help"],
        """\
Usage: soju fill-examples [OPTIONS]

  Generate noun and verb example sentences via Ollama.

Options:
  --model <str>                   [default: gemma4:e4b]
  --base-url <str>                [default: http://localhost:11434]
  --temperature <float>           [default: 0.4]
  --verb-batch-size <int>         Verbs per Ollama request  [default: 4]
  --noun-batch-size <int>         Nouns per Ollama request  [default: 6]
  --verbs-only
  --nouns-only
  --clean-only                    Strip (formal)/(casual) notes from example
                                  English only
  --local                         Generate examples with local Korean 1A/1B
                                  templates (no Ollama)
  --level <str>                   Course level (default: SOJU_LANGUAGE_LEVEL
                                  or 1A; see data/content/levels.yaml)
  --examples N                    Example sentences per verb tense/variant and
                                  per noun (default: 1)  [default: 1]
  --max-attempts N                Ollama attempts per verb batch before giving
                                  up (default: 3)  [default: 3]
  --mode <fill-empty|refresh-all>
                                  fill-empty: only entries missing examples
                                  (default); refresh-all: regenerate every
                                  entry  [default: fill-empty]
  --verbose
  --limit <int>                   Process only the first N entries (testing)
  --dry-run
  --strict                        Exit non-zero when any generation warnings
                                  were produced
  -h, --help                      Show this message and exit.
""",
    ),
    (
        ["soju", "translate-words", "--help"],
        """\
Usage: soju translate-words [OPTIONS]

  Translate a plain-text word list into soju import JSON via Ollama.

Options:
  -f, --file <path>      Plain-text word list file  [required]
  -o, --output <path>    Write JSON to this file instead of stdout
  --model <str>          Ollama model name  [default: gemma4:e4b]
  --base-url <str>       Ollama base URL  [default: http://localhost:11434]
  --batch-size <int>     Lines per Ollama request  [default: 8]
  --temperature <float>  Sampling temperature  [default: 0.3]
  --skip-existing        Omit entries already in the registry
  --level <str>          Course level (default: SOJU_LANGUAGE_LEVEL or 1A; see
                         data/content/levels.yaml)
  --dry-run              Parse input and print summary without calling Ollama
  -h, --help             Show this message and exit.
""",
    ),
    (
        ["soju", "embed-index", "--help"],
        """\
Usage: soju embed-index [OPTIONS]

  Build the Ollama embedding cache for Practice retrieval
  (data/cache/embeddings/).

Options:
  --base-url <str>     Ollama base URL  [default: http://localhost:11434]
  --embed-model <str>  Ollama embedding model (default: SOJU_EMBED_MODEL or
                       nomic-embed-text)  [default: nomic-embed-text]
  --batch-size <int>   Documents per Ollama /api/embed batch request
                       [default: 32]
  --dry-run            Count documents to embed without calling Ollama
  -h, --help           Show this message and exit.
""",
    ),
    (
        ["soju", "levels", "--help"],
        """\
Usage: soju levels [OPTIONS] COMMAND [ARGS]...

  List and assign vocabulary and grammar course levels.

Options:
  -h, --help  Show this message and exit.

Commands:
  list-unassigned  List entries with no course level tag.
  set              Assign a course level to selected vocabulary or...
""",
    ),
    (
        ["soju", "levels", "list-unassigned", "--help"],
        """\
Usage: soju levels list-unassigned [OPTIONS]

  List entries with no course level tag.

Options:
  --format <str>  Output format: table (default) or ids  [default: table]
  --kind <str>    Target kind: vocabulary (default) or grammar  [default:
                  vocabulary]
  --type <str>    Filter by vocabulary type id (e.g. noun, verb)
  -h, --help      Show this message and exit.
""",
    ),
    (
        ["soju", "levels", "set", "--help"],
        """\
Usage: soju levels set [OPTIONS]

  Assign a course level to selected vocabulary or grammar entries.

Options:
  --level <str>      Course level id from levels.yaml  [required]
  --kind <str>       Target kind: vocabulary (default) or grammar  [default:
                     vocabulary]
  --all-unassigned   Assign every unassigned entry of the chosen kind
  --id <str>         Vocabulary UUID or grammar pattern id (repeatable)
  --ids-file <path>  File of ids (one per line); use - for stdin
  --dry-run
  --force            Allow overwriting an existing level tag
  -h, --help         Show this message and exit.
""",
    ),
]


def _run_script(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the installed ``soju`` console script."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=full_env,
        input=stdin,
        check=False,
    )


@pytest.mark.parametrize(
    ("args", "expected_stdout"),
    HELP_CASES,
    ids=[" ".join(args) for args, _ in HELP_CASES],
)
def test_cli_help_baseline(args: list[str], expected_stdout: str) -> None:
    """Each CLI ``--help`` matches the Typer baseline byte-for-byte."""
    full_env = os.environ.copy()
    full_env.pop("OLLAMA_MODEL", None)
    full_env.pop("OLLAMA_HOST", None)
    result = subprocess.run(args, capture_output=True, text=True, env=full_env, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == expected_stdout


@pytest.mark.parametrize(
    ("args", "expected_stdout"),
    [
        (["soju", "align"], "Verb data alignment OK.\n"),
        (["soju", "registry"], "Registry validation OK.\n"),
        (["soju", "validate-schemas"], "Schema validation passed.\n"),
    ],
    ids=["soju align", "soju registry", "soju validate-schemas"],
)
def test_validator_cli_ok_on_repo_data(args: list[str], expected_stdout: str) -> None:
    """No-arg validator CLIs succeed against the checked-in ``data/`` tree.

    Success message + exit code against the checked-in ``data/`` tree.
    """
    repo_data = Path(__file__).resolve().parents[2] / "data"
    result = _run_script(args, env={"DATA_DIR": str(repo_data)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected_stdout
    assert result.stderr == ""


def test_promote_dry_run(data_root: Path) -> None:
    result = _run_script(
        ["soju", "promote", "--topic", "family", "--dry-run"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "would promote 0 entries; skipped 0.\n"
    assert result.stderr == ""


def test_fill_verbs_dry_run(data_root: Path) -> None:
    result = _run_script(
        ["soju", "fill-verbs", "--dry-run"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "would fill forms/examples for 1/1 verbs (examples=1, skipped=0).\n"
    assert result.stderr == ""


def test_fill_examples_dry_run_local(data_root: Path) -> None:
    result = _run_script(
        ["soju", "fill-examples", "--dry-run", "--local", "--limit", "1"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "Would generate 1 example(s) per variant for 1 verbs" in result.stderr
    assert "Fill mode: fill-empty" in result.stderr


def test_translate_words_dry_run(data_root: Path, tmp_path: Path) -> None:
    word_list = tmp_path / "words.txt"
    word_list.write_text("사과\n", encoding="utf-8")
    result = _run_script(
        ["soju", "translate-words", "--file", str(word_list), "--dry-run"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "Parsed 1 translatable lines from" in result.stderr
    assert "사과" in result.stderr


def test_import_words_dry_run(data_root: Path) -> None:
    payload = '[{"hangul":"책","romanization":"chaek","english":"book"}]'
    result = _run_script(
        [
            "soju",
            "import",
            "words",
            "--topic",
            "family",
            "--section",
            "general",
            "--stdin-json",
            "--dry-run",
        ],
        env={"DATA_DIR": str(data_root)},
        stdin=payload,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "[dry-run] added=1 merged_examples=0 add_ref=0 skipped=0 errors=0\n"
    assert result.stderr == ""


def test_import_verbs_dry_run(data_root: Path) -> None:
    payload = (
        '[{"hangul":"가다","romanization":"ga-da","english":"to go",'
        '"forms":{"present":{"casual_polite":"가요","formal_polite":"갑니다"},'
        '"past":{"casual_polite":"갔어요","formal_polite":"갔습니다"},'
        '"future":{"casual_polite":"갈 거예요","formal_polite":"가겠습니다"}}}]'
    )
    result = _run_script(
        ["soju", "import", "verbs", "--stdin-json", "--dry-run"],
        env={"DATA_DIR": str(data_root)},
        stdin=payload,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "[dry-run] added=1 merged_examples=0 add_ref=0 skipped=0 errors=0\n"
    assert result.stderr == ""


def test_embed_index_dry_run(data_root: Path) -> None:
    result = _run_script(
        ["soju", "embed-index", "--dry-run"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "Would embed" in result.stderr
    assert "vocabulary entries" in result.stderr


def test_levels_set_all_unassigned_dry_run(data_root: Path) -> None:
    from soju.registry.vocabulary import load_vocabulary, save_vocabulary

    vocab = load_vocabulary(data_root)
    for entry in vocab:
        entry.pop("level", None)
    save_vocabulary(vocab, data_root)

    result = _run_script(
        ["soju", "levels", "set", "--level", "1A", "--all-unassigned", "--dry-run"],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "would set level=1A on 2 vocabulary entries.\n"
    assert result.stderr == ""
    assert all("level" not in e for e in load_vocabulary(data_root))


def test_levels_set_grammar_all_unassigned_dry_run(data_root: Path) -> None:
    from soju.registry.grammar import load_grammar_pattern, save_grammar_pattern

    pattern = load_grammar_pattern("do", data_root)
    pattern.pop("level", None)
    save_grammar_pattern("do", pattern, data_root)

    result = _run_script(
        [
            "soju",
            "levels",
            "set",
            "--kind",
            "grammar",
            "--level",
            "1A",
            "--all-unassigned",
            "--dry-run",
        ],
        env={"DATA_DIR": str(data_root)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "would set level=1A on 1 grammar entry.\n"
    assert result.stderr == ""
    assert "level" not in load_grammar_pattern("do", data_root)


def test_backend_help_smoke() -> None:
    """``soju backend --help`` exits cleanly (not pinned byte-for-byte; needs backend extras)."""
    pytest.importorskip("fastapi")
    result = _run_script(["soju", "backend", "--help"])
    assert result.returncode == 0, result.stderr
    assert "backend" in result.stdout.lower()
    assert "--config" in result.stdout
