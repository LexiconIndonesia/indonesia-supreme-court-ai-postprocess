import urllib.parse
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    db_addr: str
    db_user: str
    db_pass: str

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache
def get_settings():
    settings = Settings()
    settings.db_user = urllib.parse.quote(settings.db_user)
    settings.db_pass = urllib.parse.quote(settings.db_pass)

    return settings
