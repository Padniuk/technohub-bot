from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    debug: int
    admins_id: str
    electricity_chat_id: int
    plumbing_chat_id: int
    channel_id: int
    electricity_url: str
    plumbing_url: str
    db_host: str
    db_name: str
    db_user: str
    db_pass: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()