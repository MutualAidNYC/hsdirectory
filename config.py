"""
Configuration management for the HSDS API application.

Loads settings from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Airtable Configuration
    airtable_api_key: str
    airtable_base_id: str
    
    # Sync Settings
    sync_interval_minutes: int = 15
    
    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8080
    
    # API Metadata. `profile` points at the UK profile pending a profile of our own.
    api_version: str = "HSDS-3.0"
    api_profile: str = "https://github.com/OpenReferralUK/uk-profile/blob/main/docs/index.md"
    
    # Filtering Configuration
    # Only show services with status matching this value (case-sensitive)
    # Set to empty string to disable filtering
    published_status_value: str = "Published"
    
    # If True, also hide organizations that have no published services
    filter_orgs_without_published_services: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
