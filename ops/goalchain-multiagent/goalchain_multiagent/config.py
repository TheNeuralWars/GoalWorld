import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    paths: list[str] = []
    ma_env = os.environ.get("goalworld_MA_ENV")
    if ma_env:
        paths.append(ma_env)
    else:
        default = Path.home() / ".config" / "goalworld-multiagent.env"
        if default.is_file():
            paths.append(str(default))
    local = Path(".env")
    if local.is_file():
        paths.append(str(local))
    return tuple(paths)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    goalworld_multiagent_enabled: bool = False
    goalworld_ma_host: str = "127.0.0.1"
    goalworld_ma_port: int = 8790
    goalworld_ma_token: str = ""
    goalworld_ma_mock_llm: bool = True
    # auto | openrouter | anthropic | openai — auto uses FCC OpenRouter when enabled
    goalworld_ma_provider: str = "auto"
    goalworld_ma_use_fcc_keys: bool = True
    goalworld_ma_model: str = "claude-sonnet-4-20250514"
    goalworld_ma_openai_model: str = "gpt-4o-mini"
    goalworld_ma_openrouter_model: str = "openai/gpt-4o-mini"
    goalworld_ma_openrouter_base_url: str = "https://openrouter.ai/api/v1"
    goalworld_ma_nvidia_model: str = "nvidia/nemotron-3-super-120b-a12b"
    goalworld_ma_nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    goalworld_ma_max_hops: int = 6
    goalworld_ma_ops_live: bool = True
    goalworld_ma_dev_write_github: bool = False
    goalworld_ma_twenty_api_key: str = ""
    goalworld_ma_twenty_url: str = "https://crm.goalworld.fun"
    goalworld_ma_slack_webhook: str = ""
    goalworld_ma_slack_bot_token: str = ""
    goalworld_ma_slack_app_token: str = ""
    goalworld_ma_mattermost_url: str = ""
    goalworld_ma_mattermost_bot_token: str = ""
    goalworld_ma_mattermost_webhook: str = ""
    github_repo: str = "TheNeuralWars/goalworld"
    hermes_home: str = "/home/goalworld/hermes"





    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    nvidia_nim_api_key: str = ""
    stripe_api_key: str = ""


def get_settings() -> Settings:

    return Settings()

