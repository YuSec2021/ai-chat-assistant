"""Configuration management using pydantic-settings"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URL")
    database_name: str = Field(default="ai_chat_assistant", description="Database name")

    # LLM API
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="OpenAI API base URL")
    api_key: str = Field(default="", description="OpenAI API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    default_llm_provider: str = Field(default="openai", description="Default LLM provider")
    default_model: str = Field(default="qwen3-max", description="Default model name")

    # File Upload
    max_upload_size: int = Field(default=10485760, description="Max upload size in bytes (10MB)")
    allowed_file_types: str = Field(
        default="image/png,image/jpeg,image/gif,image/webp,video/mp4,video/webp,application/pdf",
        description="Allowed MIME types"
    )

    # Temp File Cleanup
    temp_file_cleanup_interval: int = Field(default=24, description="Cleanup interval in hours")

    @property
    def allowed_mime_types(self) -> List[str]:
        """Parse allowed file types into a list"""
        return [t.strip() for t in self.allowed_file_types.split(",")]


# Global settings instance
settings = Settings()
