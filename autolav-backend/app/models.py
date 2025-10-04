"""
Modelos de dados da API
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request para scraping de unidades"""
    units: List[str] = Field(..., description="Lista de IDs de unidades")
    start_date: Optional[str] = Field(None, description="Data inicial (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Data final (YYYY-MM-DD)")
    username: Optional[str] = Field(None, description="Nome de usuário para login")
    password: Optional[str] = Field(None, description="Senha para login")
    date_selector: Optional[str] = Field("td:nth-child(1)", description="Seletor CSS para célula de data")
    kg_selector: Optional[str] = Field("td:nth-child(2)", description="Seletor CSS para célula de kg")


class RowData(BaseModel):
    """Dados de uma linha da tabela"""
    date: str = Field(..., description="Data normalizada (YYYY-MM-DD)")
    kg: float = Field(..., description="Kg parseado")
    raw_date: Optional[str] = Field(None, description="Data original da tabela")
    raw_kg: Optional[str] = Field(None, description="Kg original da tabela")


class UnitResult(BaseModel):
    """Resultado do scraping de uma unidade"""
    unit_id: str = Field(..., description="ID da unidade")
    rows: List[RowData] = Field(default_factory=list, description="Linhas extraídas")
    total: float = Field(0.0, description="Total de kg")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class ScrapeResponse(BaseModel):
    """Response do endpoint de scraping"""
    results: List[UnitResult] = Field(..., description="Resultados por unidade")
    total_units: int = Field(..., description="Total de unidades processadas")
    successful_units: int = Field(..., description="Unidades processadas com sucesso")
    failed_units: int = Field(..., description="Unidades com erro")


class UnitInfo(BaseModel):
    """Informação de uma unidade descoberta"""
    unit_id: str = Field(..., description="ID da unidade")
    unit_name: str = Field(..., description="Nome da unidade")


class DiscoverUnitsResponse(BaseModel):
    """Response do endpoint de descoberta de unidades"""
    units: List[UnitInfo] = Field(..., description="Lista de unidades descobertas")
    total: int = Field(..., description="Total de unidades")


class LoginCredentials(BaseModel):
    """Credenciais de login"""
    username: str = Field(..., description="Nome de usuário")
    password: str = Field(..., description="Senha")


class HealthResponse(BaseModel):
    """Response do endpoint de health check"""
    status: str = Field(..., description="Status do serviço")
    version: str = Field(..., description="Versão da aplicação")
