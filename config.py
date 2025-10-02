import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv()
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.bot", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DISCORD_WEBHOOK_URL: str = ""
    GENAI_API_KEY : str = ""

    DATA_FILE: str = "Bot_data.json"
    FAQ_FILE: str = "faq.xlsx"
    BAD_WORDS_FILE: str = "bad_words.txt"
    ANTI_BEGGER_FILE: str = "AntiBegger_list.txt"

    CHAT_RULES_URL: str = ""
    ADMIN_APPLICATION_URL: str = "https://forms.gle/FYfZNa3LYrCYtNnd8"

    # AntiMat settings
    ANTI_MAT_USE_FUZZY: bool = True
    BAD_FUZZY_THRESHOLD: int = 85




BOT_TOKEN = "7969025390:AAG62t2wUCOAvc3-ZnVkcKqGoNYOslLDpLA"
GENAI_API_KEY = "AIzaSyAfM-TZ3GzcMeY5RkER6ygdATHmxhszRqY" # ТУТ ТРЕБА АПІ С ГЕМЕНІ
settings = Settings(BOT_TOKEN=BOT_TOKEN , GENAI_API_KEY= GENAI_API_KEY)
