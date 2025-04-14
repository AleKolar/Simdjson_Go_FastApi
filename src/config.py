import os
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

__all__ = ['Settings', 'settings']

load_dotenv()

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    class Config:
        env_file = ".env"

    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")


try:
    settings = Settings()
except ValidationError as e:
    print(f"Validation errors: {e}")
    exit(1)