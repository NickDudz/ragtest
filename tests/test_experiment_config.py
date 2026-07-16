from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from ragtoolkit.evaluation.runner import EvaluationConfigError, load_experiment_config


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "evaluation" / "experiments.yaml"


def _write_config(tmp_path: Path, config: dict[str, Any]) -> Path:
    path = tmp_path / "experiments.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def _duplicate_experiment(config: dict[str, Any]) -> None:
    config["experiments"].append(deepcopy(config["experiments"][0]))


def _invalid_overlap(config: dict[str, Any]) -> None:
    chunking = config["experiments"][0]["chunking"]
    chunking["overlap"] = chunking["size"]


def _enable_reranking(config: dict[str, Any]) -> None:
    config["retrieval"]["rerank"] = True


def _enable_score_filter(config: dict[str, Any]) -> None:
    config["retrieval"]["min_score"] = 0.5


def _insufficient_top_k(config: dict[str, Any]) -> None:
    config["retrieval"]["top_k"] = 4


def _unsupported_provider(config: dict[str, Any]) -> None:
    config["models"]["embedding"]["provider"] = "paid-api"


def _unknown_experiment_variable(config: dict[str, Any]) -> None:
    config["experiments"][0]["reranker"] = "cross-encoder"


def test_checked_in_experiment_config_is_valid_and_small() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config["version"] == 1
    assert config["retrieval"] == {"top_k": 6, "min_score": None, "rerank": False}
    assert [experiment["id"] for experiment in config["experiments"]] == [
        "baseline_900_150",
        "focused_500_80",
    ]
    assert config["models"]["embedding"]["provider"] == "ollama"
    assert config["models"]["generation"]["provider"] == "ollama"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (_duplicate_experiment, "duplicate experiment id"),
        (_invalid_overlap, "0 <= overlap < size"),
        (_enable_reranking, "requires rerank: false"),
        (_enable_score_filter, "requires min_score: null"),
        (_insufficient_top_k, "top_k must be at least 5"),
        (_unsupported_provider, "must specify an Ollama model"),
        (_unknown_experiment_variable, "unsupported experiment fields"),
    ],
)
def test_experiment_config_rejects_uncontrolled_variables(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    config = load_experiment_config(CONFIG_PATH)
    mutation(config)

    with pytest.raises(EvaluationConfigError, match=message):
        load_experiment_config(_write_config(tmp_path, config))


def test_experiment_config_requires_all_top_level_sections(tmp_path: Path) -> None:
    config = load_experiment_config(CONFIG_PATH)
    config.pop("prompt")

    with pytest.raises(EvaluationConfigError, match="missing experiment fields: prompt"):
        load_experiment_config(_write_config(tmp_path, config))


def test_experiment_config_requires_two_comparable_experiments(tmp_path: Path) -> None:
    config = load_experiment_config(CONFIG_PATH)
    config["experiments"] = config["experiments"][:1]

    with pytest.raises(EvaluationConfigError, match="at least two experiments"):
        load_experiment_config(_write_config(tmp_path, config))
