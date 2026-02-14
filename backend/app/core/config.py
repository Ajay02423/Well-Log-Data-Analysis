from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Well Log Analyzer"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    HF_API_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

