"""
AutoLav Backend - API FastAPI
"""
import asyncio
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .logger import logger
from .models import (
    ScrapeRequest, ScrapeResponse, UnitResult, RowData,
    DiscoverUnitsResponse, UnitInfo, LoginCredentials, HealthResponse
)
from .scraper import LavanderiaPortalScraper
from .parser import validate_date_range

# Versão da aplicação
VERSION = "1.0.0"

# Criar app FastAPI
app = FastAPI(
    title="AutoLav API",
    description="API para automação de coleta de dados de lavanderia hospitalar",
    version=VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Armazenamento temporário de credenciais (em produção, usar banco de dados seguro)
_credentials_store = {
    'username': settings.login_username,
    'password': settings.login_password
}


def verify_token(x_api_token: Optional[str] = Header(None)):
    """Verifica token de autenticação"""
    if not x_api_token or x_api_token != settings.api_token:
        raise HTTPException(status_code=401, detail="Token de API inválido")
    return x_api_token


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de health check"""
    return HealthResponse(
        status="ok",
        version=VERSION
    )


@app.post("/api/login", dependencies=[Depends(verify_token)])
async def update_login(credentials: LoginCredentials):
    """
    Atualiza credenciais de login
    """
    try:
        _credentials_store['username'] = credentials.username
        _credentials_store['password'] = credentials.password
        
        logger.info("Credenciais de login atualizadas")
        
        return {"message": "Credenciais atualizadas com sucesso"}
    
    except Exception as e:
        logger.error(f"Erro ao atualizar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/login", dependencies=[Depends(verify_token)])
async def get_login_status():
    """
    Verifica se credenciais estão configuradas
    """
    has_credentials = bool(_credentials_store.get('username') and _credentials_store.get('password'))
    
    return {
        "has_credentials": has_credentials,
        "username": _credentials_store.get('username', '') if has_credentials else None
    }


@app.post("/api/upload-storage", dependencies=[Depends(verify_token)])
async def upload_storage_state(file: UploadFile = File(...)):
    """
    Faz upload do arquivo storage_state.json
    """
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser JSON")
        
        # Salva arquivo
        storage_path = settings.storage_dir / "storage_state.json"
        content = await file.read()
        
        # Valida JSON
        try:
            json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="JSON inválido")
        
        with open(storage_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Storage state salvo em {storage_path}")
        
        return {"message": "Storage state salvo com sucesso", "path": str(storage_path)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao salvar storage state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/discover_units", response_model=DiscoverUnitsResponse, dependencies=[Depends(verify_token)])
async def discover_units():
    """
    Descobre automaticamente todas as unidades disponíveis
    """
    try:
        logger.info("Iniciando descoberta de unidades...")
        
        # Obtém credenciais
        username = _credentials_store.get('username')
        password = _credentials_store.get('password')
        
        # Cria scraper
        async with LavanderiaPortalScraper() as scraper:
            units = await scraper.discover_units(username, password)
        
        # Filtra unidades sem dados (opcional - pode ser refinado)
        # Por enquanto, retorna todas as unidades descobertas
        
        logger.info(f"Descoberta concluída: {len(units)} unidades")
        
        return DiscoverUnitsResponse(
            units=[UnitInfo(**unit) for unit in units],
            total=len(units)
        )
    
    except Exception as e:
        logger.error(f"Erro ao descobrir unidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def scrape_unit_with_retry(
    scraper: LavanderiaPortalScraper,
    unit_id: str,
    start_date: Optional[str],
    end_date: Optional[str],
    username: Optional[str],
    password: Optional[str],
    date_selector: str,
    kg_selector: str,
    max_retries: int = 2
) -> UnitResult:
    """
    Faz scraping de uma unidade com retry
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(f"Tentativa {attempt + 1} para unidade {unit_id}")
                await asyncio.sleep(settings.nav_delay / 1000)
            
            result = await scraper.scrape_unit(
                unit_id=unit_id,
                start_date=start_date,
                end_date=end_date,
                username=username,
                password=password
            )
            
            # Se não houve erro, retorna resultado
            if not result.get('error'):
                return UnitResult(**result)
            
            last_error = result.get('error')
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"Erro na tentativa {attempt + 1} para unidade {unit_id}: {e}")
    
    # Se chegou aqui, todas as tentativas falharam
    return UnitResult(
        unit_id=unit_id,
        rows=[],
        total=0.0,
        error=last_error or "Falha após múltiplas tentativas"
    )


@app.post("/api/scrape", response_model=ScrapeResponse, dependencies=[Depends(verify_token)])
async def scrape_units(
    payload: Optional[str] = Form(None),
    storage: Optional[UploadFile] = File(None),
    request_body: Optional[ScrapeRequest] = None
):
    """
    Faz scraping de múltiplas unidades
    
    Aceita tanto JSON direto quanto multipart/form-data com storage_state.json
    """
    try:
        # Parse request
        if payload:
            # Multipart form data
            request_data = json.loads(payload)
            request_obj = ScrapeRequest(**request_data)
            
            # Salva storage state se fornecido
            if storage:
                storage_path = settings.storage_dir / "storage_state.json"
                content = await storage.read()
                with open(storage_path, 'wb') as f:
                    f.write(content)
                logger.info("Storage state recebido via multipart")
        
        elif request_body:
            # JSON direto
            request_obj = request_body
        
        else:
            raise HTTPException(status_code=400, detail="Request inválido")
        
        # Valida e normaliza datas
        start_date, end_date = validate_date_range(request_obj.start_date, request_obj.end_date)
        
        # Obtém credenciais (usa as do request ou as armazenadas)
        username = request_obj.username or _credentials_store.get('username')
        password = request_obj.password or _credentials_store.get('password')
        
        logger.info(f"Iniciando scraping de {len(request_obj.units)} unidades")
        logger.info(f"Período: {start_date} a {end_date}")
        
        # Cria scraper
        async with LavanderiaPortalScraper() as scraper:
            # Processa unidades com concorrência limitada
            semaphore = asyncio.Semaphore(settings.max_concurrency)
            
            async def scrape_with_semaphore(unit_id: str):
                async with semaphore:
                    result = await scrape_unit_with_retry(
                        scraper=scraper,
                        unit_id=unit_id,
                        start_date=start_date,
                        end_date=end_date,
                        username=username,
                        password=password,
                        date_selector=request_obj.date_selector,
                        kg_selector=request_obj.kg_selector,
                        max_retries=settings.max_retries
                    )
                    
                    # Delay entre unidades
                    await asyncio.sleep(settings.nav_delay / 1000)
                    
                    return result
            
            # Executa scraping de todas as unidades
            tasks = [scrape_with_semaphore(unit_id) for unit_id in request_obj.units]
            results = await asyncio.gather(*tasks)
        
        # Calcula estatísticas
        successful = sum(1 for r in results if not r.error)
        failed = len(results) - successful
        
        logger.info(f"Scraping concluído: {successful} sucesso, {failed} falhas")
        
        return ScrapeResponse(
            results=results,
            total_units=len(results),
            successful_units=successful,
            failed_units=failed
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação"""
    logger.info(f"AutoLav Backend v{VERSION} iniciado")
    logger.info(f"Porta: {settings.port}")
    logger.info(f"Max concurrency: {settings.max_concurrency}")
    logger.info(f"Nav timeout: {settings.nav_timeout}s")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a aplicação"""
    logger.info("AutoLav Backend encerrado")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
