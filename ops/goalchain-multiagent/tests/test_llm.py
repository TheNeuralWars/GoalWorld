import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("goalworld_MA_MOCK_LLM", "1")

from goalworld_multiagent import llm  # noqa: E402
from goalworld_multiagent.config import Settings  # noqa: E402
from goalworld_multiagent.graph import run_objective  # noqa: E402


def test_llm_not_available_when_mock():
    s = Settings(goalworld_ma_mock_llm=True, anthropic_api_key="sk-test")
    assert llm.llm_available(s) is False


def test_llm_available_with_key():
    s = Settings(goalworld_ma_mock_llm=False, anthropic_api_key="sk-test")
    assert llm.resolve_provider(s) == "anthropic"
    assert llm.llm_available(s) is True


def test_llm_nvidia_resolves_with_key():
    s = Settings(
        goalworld_ma_mock_llm=False,
        goalworld_ma_provider="nvidia",
        nvidia_nim_api_key="nvapi-test",
    )
    assert llm.resolve_provider(s) == "nvidia"
    assert llm.llm_available(s) is True
    
    # Test instantiation of the chat model
    model = llm.get_chat_model(s)
    assert model is not None
    assert model.model_name == "nvidia/nemotron-3-super-120b-a12b"



def test_llm_auto_uses_fcc_openrouter(tmp_path, monkeypatch):
    fcc = tmp_path / ".fcc.env"
    fcc.write_text('OPENROUTER_API_KEY="sk-or-test"\n', encoding="utf-8")
    monkeypatch.setattr(
        "goalworld_multiagent.fcc_env.fcc_env_path", lambda: fcc
    )
    s = Settings(
        goalworld_ma_mock_llm=False,
        goalworld_ma_provider="auto",
        goalworld_ma_use_fcc_keys=True,
    )
    assert llm.resolve_provider(s) == "openrouter"
    assert llm.llm_available(s) is True


@patch("goalworld_multiagent.llm.get_chat_model")
def test_ceo_delegate_llm(mock_get_model):
    mock_model = MagicMock()
    mock_model.invoke.return_value = MagicMock(
        content='{"agent": "dev", "reason": "webapp API work"}'
    )
    mock_get_model.return_value = mock_model

    agent = llm.ceo_delegate_llm(
        {"objective": "fix webapp routing"},
        Settings(goalworld_ma_mock_llm=False, anthropic_api_key="sk-test"),
    )
    assert agent == "dev"


@patch("goalworld_multiagent.llm.ceo_synthesize_llm")
@patch("goalworld_multiagent.llm.ceo_delegate_llm")
def test_graph_uses_llm_when_enabled(mock_delegate, mock_synth):
    mock_delegate.return_value = "dev"
    mock_synth.return_value = "Resumen ejecutivo LLM."

    os.environ["goalworld_MA_MOCK_LLM"] = "0"
    with patch(
        "goalworld_multiagent.agents.ceo.get_settings",
        return_value=Settings(
            goalworld_ma_mock_llm=False,
            anthropic_api_key="sk-test",
            goalworld_ma_max_hops=6,
        ),
    ):
        with patch("goalworld_multiagent.llm.llm_available", return_value=True):
            result = run_objective("Refactor webapp coach API")

    assert result.get("summary") == "Resumen ejecutivo LLM."
    mock_delegate.assert_called()
    mock_synth.assert_called()
