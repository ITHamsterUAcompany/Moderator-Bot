import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DISCORD_WEBHOOK_URL: str = ""

    DATA_FILE: str = "Bot_data.json"
    FAQ_FILE: str = "faq.xlsx"
    BAD_WORDS_FILE: str = "bad_words.txt"
    ANTI_BEGGER_FILE: str = "AntiBegger_list.txt"

    CHAT_RULES_URL: str = ""
    ADMIN_APPLICATION_URL: str = "https://forms.gle/FYfZNa3LYrCYtNnd8"

    # AntiMat settings
    ANTI_MAT_USE_FUZZY: bool = True
    BAD_FUZZY_THRESHOLD: int = 85


settings = Settings()
