import os
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DB_USER: str = Field(default=os.getenv('DB_USER'))
    DB_PASSWORD: str = Field(default=os.getenv('DB_PASSWORD'))
    DB_HOST: str = Field(default=os.getenv('DB_HOST'))
    DB_PORT: str = Field(default=os.getenv('DB_PORT'))
    DB_NAME: str = Field(default=os.getenv('DB_NAME'))
    REDIS_URL: str = Field(default="redis://localhost:6379")
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost/")
    DATABASE_URL: str = Field(default=os.getenv('DATABASE_URL'))

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

    @property
    def get_db_url(self) -> str:
        # return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self.DATABASE_URL

try:
    settings = Settings()
except ValidationError as e:
    print(f"Configuration validation error: {e}")
    exit(1)

