"""Конфигурация бота."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str
    admin_ids: str

    # S-UI Panel
    sui_url: str
    sui_token: str

    @property
    def admin_list(self) -> list[int]:
        """Список ID администраторов."""
        return [int(uid.strip()) for uid in self.admin_ids.split(",") if uid.strip()]


settings = Settings()

