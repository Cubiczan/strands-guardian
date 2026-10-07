"""Bedrock model selection: Nova Pro default and Anthropic rejection."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import strands_guardian.agent as agent_mod
from strands_guardian.agent import (
    DEFAULT_BEDROCK_REGION,
    DEFAULT_MODEL_ID,
    AnthropicModelRejected,
    create_guardian_agent,
    main,
    resolve_model_id,
    run_guardian,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_CLAUDE_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514"


def test_default_model_is_nova_pro(monkeypatch):
    monkeypatch.delenv("STRANDS_MODEL_ID", raising=False)
    assert DEFAULT_MODEL_ID == "us.amazon.nova-pro-v1:0"
    assert DEFAULT_BEDROCK_REGION == "us-east-1"
    assert resolve_model_id() == DEFAULT_MODEL_ID
    assert resolve_model_id(None) == DEFAULT_MODEL_ID


def test_blank_env_uses_nova_pro(monkeypatch):
    monkeypatch.setenv("STRANDS_MODEL_ID", "   ")
    assert resolve_model_id() == DEFAULT_MODEL_ID
    assert resolve_model_id("  ") == DEFAULT_MODEL_ID


def test_env_override(monkeypatch):
    monkeypatch.setenv("STRANDS_MODEL_ID", "us.amazon.nova-lite-v1:0")
    assert resolve_model_id() == "us.amazon.nova-lite-v1:0"


def test_argument_wins_over_env(monkeypatch):
    monkeypatch.setenv("STRANDS_MODEL_ID", "us.amazon.nova-lite-v1:0")
    assert resolve_model_id("us.amazon.nova-micro-v1:0") == "us.amazon.nova-micro-v1:0"


@pytest.mark.parametrize(
    "model_id",
    [
        "us.anthropic.claude-sonnet-4-20250514",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "global.anthropic.claude-sonnet-4-20250514",
        "US.Anthropic.Claude-Sonnet-4-20250514",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
    ],
)
def test_resolve_rejects_anthropic_ids(model_id):
    with pytest.raises(AnthropicModelRejected) as exc:
        resolve_model_id(model_id)
    message = str(exc.value)
    assert model_id in message
    assert DEFAULT_MODEL_ID in message


def test_env_anthropic_id_is_rejected(monkeypatch):
    monkeypatch.setenv("STRANDS_MODEL_ID", "global.anthropic.claude-sonnet-4-20250514")
    with pytest.raises(AnthropicModelRejected) as exc:
        resolve_model_id()
    assert "global.anthropic.claude-sonnet-4-20250514" in str(exc.value)
    assert DEFAULT_MODEL_ID in str(exc.value)


def test_mock_run_rejects_anthropic_before_pipeline(monkeypatch):
    def _boom(**kwargs):
        raise AssertionError("pipeline should not run")

    monkeypatch.setattr(agent_mod, "_run_standalone", _boom)
    with pytest.raises(AnthropicModelRejected):
        run_guardian(
            "scan",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            mock=True,
        )


def _install_model_fakes(monkeypatch):
    captured: dict = {"constructed": False}

    class FakeBedrockModel:
        def __init__(self, **kwargs):
            captured["constructed"] = True
            captured["model_kwargs"] = kwargs
            self.kwargs = kwargs

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["agent_kwargs"] = kwargs

    fake_strands = types.ModuleType("strands")
    fake_models = types.ModuleType("strands.models")
    fake_models.BedrockModel = FakeBedrockModel
    fake_strands.models = fake_models
    monkeypatch.setitem(sys.modules, "strands", fake_strands)
    monkeypatch.setitem(sys.modules, "strands.models", fake_models)
    monkeypatch.setattr(agent_mod, "STRANDS_AVAILABLE", True)
    monkeypatch.setattr(agent_mod, "Agent", FakeAgent, raising=False)
    monkeypatch.setattr(agent_mod, "_wrap_tool", lambda fn, mock: fn)
    return captured


def test_create_agent_uses_nova_pro_in_us_east_1(monkeypatch):
    monkeypatch.delenv("STRANDS_MODEL_ID", raising=False)
    captured = _install_model_fakes(monkeypatch)

    create_guardian_agent()

    assert captured["model_kwargs"] == {
        "model_id": "us.amazon.nova-pro-v1:0",
        "region_name": "us-east-1",
    }
    assert captured["agent_kwargs"]["model"].kwargs["model_id"] == DEFAULT_MODEL_ID


def test_create_agent_honors_override(monkeypatch):
    monkeypatch.setenv("STRANDS_MODEL_ID", "us.amazon.nova-lite-v1:0")
    captured = _install_model_fakes(monkeypatch)

    create_guardian_agent(model_id="amazon.nova-micro-v1:0")

    assert captured["model_kwargs"]["model_id"] == "amazon.nova-micro-v1:0"
    assert captured["model_kwargs"]["region_name"] == "us-east-1"


def test_create_agent_rejects_anthropic_before_client(monkeypatch):
    captured = _install_model_fakes(monkeypatch)
    with pytest.raises(AnthropicModelRejected) as exc:
        create_guardian_agent(model_id=OLD_CLAUDE_MODEL_ID)
    assert captured["constructed"] is False
    assert OLD_CLAUDE_MODEL_ID in str(exc.value)
    assert DEFAULT_MODEL_ID in str(exc.value)


def test_create_agent_rejects_anthropic_without_sdk(monkeypatch):
    monkeypatch.setattr(agent_mod, "STRANDS_AVAILABLE", False)
    with pytest.raises(AnthropicModelRejected):
        create_guardian_agent(model_id="anthropic.claude-3-haiku-20240307-v1:0")


def test_cli_rejects_anthropic_model(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["strands-guardian", "--model", OLD_CLAUDE_MODEL_ID, "Full southeast scan"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert OLD_CLAUDE_MODEL_ID in err
    assert DEFAULT_MODEL_ID in err


def test_cli_help_example_is_nova_pro(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["strands-guardian", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "us.amazon.nova-pro-v1:0" in out
    assert "anthropic." not in out.lower()


def test_operator_docs_default_to_nova_pro():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    agent_source = (REPO_ROOT / "src" / "strands_guardian" / "agent.py").read_text(encoding="utf-8")

    assert "us.amazon.nova-pro-v1:0" in readme
    assert "bedrock:Converse" in readme
    assert "bedrock:ConverseStream" in readme
    assert "anthropic." not in readme.lower()
    assert "claude" not in readme.lower()

    assert "us.amazon.nova-pro-v1:0" in env_example
    assert "anthropic." not in env_example.lower()

    assert f'DEFAULT_MODEL_ID = "{DEFAULT_MODEL_ID}"' in agent_source
    assert OLD_CLAUDE_MODEL_ID not in agent_source

    production_roots = [
        REPO_ROOT / "src",
        REPO_ROOT / "README.md",
        REPO_ROOT / ".env.example",
        REPO_ROOT / "assets",
    ]
    offenders = []
    for root in production_roots:
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file():
                continue
            allowed = {".py", ".md", ".example", ".txt", ".yml", ".yaml"}
            if path.suffix.lower() not in allowed and path.name != ".env.example":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if OLD_CLAUDE_MODEL_ID in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []
