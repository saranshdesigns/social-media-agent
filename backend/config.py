from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"  # cheapest model with vision

    # Google Drive
    google_credentials_path: str = Field("credentials.json", env="GOOGLE_CREDENTIALS_PATH")
    google_credentials_json: str = Field("", env="GOOGLE_CREDENTIALS_JSON")  # Railway: paste credentials.json content
    google_portfolio_folder_id: str = Field(..., env="GOOGLE_PORTFOLIO_FOLDER_ID")

    # Server public URL (used to serve temp images — your Railway URL)
    server_base_url: str = Field("http://localhost:8000", env="SERVER_BASE_URL")
    frontend_url: str = Field("", env="FRONTEND_URL")  # Railway frontend URL for CORS

    # Facebook / Instagram
    facebook_page_access_token: str = Field(..., env="FACEBOOK_PAGE_ACCESS_TOKEN")
    facebook_page_id: str = Field(..., env="FACEBOOK_PAGE_ID")
    instagram_account_id: str = Field(..., env="INSTAGRAM_ACCOUNT_ID")

    # Schedule
    schedule_hour: int = Field(10, env="SCHEDULE_HOUR")
    schedule_minute: int = Field(0, env="SCHEDULE_MINUTE")
    post_interval_minutes: int = Field(5, env="POST_INTERVAL_MINUTES")
    max_posts_per_day: int = Field(3, env="MAX_POSTS_PER_DAY")

    # Telegram Bot (optional — leave empty to disable)
    telegram_bot_token: str = Field("", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field("", env="TELEGRAM_CHAT_ID")

    # App
    app_env: str = Field("production", env="APP_ENV")
    secret_key: str = Field(..., env="SECRET_KEY")
    database_path: str = Field("../data/database.db", env="DATABASE_PATH")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
