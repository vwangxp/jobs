"""Configuration management for jobs pipeline."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


def get_project_root() -> Path:
    """Get the project root directory."""
    # Use current working directory as project root
    return Path.cwd()


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Paths (relative to project root)
    DATA_DIR: Path = get_project_root() / "data"
    HTML_DIR: Path = get_project_root() / "data" / "html"
    PAGES_DIR: Path = get_project_root() / "data" / "pages"
    SITE_DIR: Path = get_project_root() / "site"
    RAW_DIR: Path = get_project_root() / "data" / "raw"
    PROCESSED_DIR: Path = get_project_root() / "data" / "processed"

    # API Configuration
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "google/gemini-3-flash-preview"
    LLM_TEMPERATURE: float = 0.2
    LLM_DELAY: float = 0.5

    # Scraping Configuration
    SCRAPE_DELAY: float = 1.0
    REQUEST_TIMEOUT: int = 15000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
