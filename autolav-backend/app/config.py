"""
Configuração da aplicação AutoLav Backend
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env"""
    
    # Servidor
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Segurança
    api_token: str = "change_me_in_production"
    
    # Diretórios
    storage_dir: Path = Path("./storage")
    log_dir: Path = Path("./logs")
    reports_dir: Path = Path("./reports")
    
    # Scraping
    max_concurrency: int = 4
    nav_timeout: int = 30
    nav_delay: int = 500
    max_retries: int = 2
    
    # Portal
    portal_url: str = ""
    unit_url_template: str = ""
    
    # Credenciais (armazenadas temporariamente, sobrescritas pelo frontend)
    login_username: str = ""
    login_password: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global de configuração
settings = Settings()

# Criar diretórios necessários
settings.storage_dir.mkdir(parents=True, exist_ok=True)
settings.log_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
