from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Database
    database_url: str = ""
    database_url_sync: str = ""

    # LLM
    llm_base_url: str = ""
    llm_model: str = "deepseek"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7
    llm_timeout: int = 120

    # WordPress
    wp_api_url: str = ""
    wp_username: str = ""
    wp_app_password: SecretStr = SecretStr("")

    # Image Search
    unsplash_access_key: SecretStr | None = None
    pexels_api_key: SecretStr | None = None

    # App
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()
