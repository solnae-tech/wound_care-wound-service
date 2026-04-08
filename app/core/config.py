from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    DATABASE_URL : str = Field(
        default="" , description="optional override for full DB URL"
    )

    model_config = SettingsConfigDict(
        env_file = ".env",extra="allow"
    )

settings = Settings()