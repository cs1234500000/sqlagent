from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    openai_api_key: str
    db_connection_string: str
    model_name: str = "gpt-4o-mini"
    max_tokens: int = 1000
    query_timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        protected_namespaces=('settings_',),
        env_prefix="",
        case_sensitive=False
    )

    @property
    def connection_string(self) -> str:
        """Alias for db_connection_string for backward compatibility"""
        return self.db_connection_string 