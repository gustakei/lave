"""
Módulo de scraping usando Playwright
"""
import asyncio
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from .config import settings
from .logger import logger
from .parser import parse_kg, parse_date, filter_rows_by_date, calculate_total


class LavanderiaPortalScraper:
    """Scraper para o portal da lavanderia hospitalar"""
    
    def __init__(self, storage_state_path: Optional[Path] = None):
        self.storage_state_path = storage_state_path or (settings.storage_dir / "storage_state.json")
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def start(self):
        """Inicia o browser"""
        logger.info("Iniciando Playwright...")
        self.playwright = await async_playwright().start()
        
        # Configurações do browser
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled'
        ]
        
        # Tenta carregar storage_state se existir
        storage_state = None
        if self.storage_state_path.exists():
            try:
                with open(self.storage_state_path, 'r') as f:
                    storage_state = json.load(f)
                logger.info(f"Storage state carregado de {self.storage_state_path}")
            except Exception as e:
                logger.warning(f"Erro ao carregar storage_state: {e}")
        
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        logger.info("Browser iniciado com sucesso")
    
    async def close(self):
        """Fecha o browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser fechado")
        if self.playwright:
            await self.playwright.stop()
    
    async def login(self, page: Page, username: str, password: str) -> bool:
        """
        Realiza login no portal
        
        Args:
            page: Página do Playwright
            username: Nome de usuário
            password: Senha
        
        Returns:
            True se login bem-sucedido
        """
        try:
            logger.info("Detectando tela de login...")
            
            # Detecta campos de login comuns
            login_selectors = [
                'input[name="username"]', 'input[name="user"]', 'input[id="username"]',
                'input[type="text"]', 'input[placeholder*="usuário"]', 'input[placeholder*="user"]'
            ]
            
            password_selectors = [
                'input[name="password"]', 'input[id="password"]', 
                'input[type="password"]', 'input[placeholder*="senha"]'
            ]
            
            # Tenta encontrar campo de usuário
            username_field = None
            for selector in login_selectors:
                try:
                    username_field = await page.wait_for_selector(selector, timeout=2000)
                    if username_field:
                        break
                except:
                    continue
            
            if not username_field:
                logger.warning("Campo de usuário não encontrado")
                return False
            
            # Tenta encontrar campo de senha
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=2000)
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                logger.warning("Campo de senha não encontrado")
                return False
            
            logger.info("Campos de login detectados, preenchendo...")
            
            # Preenche credenciais
            await username_field.fill(username)
            await password_field.fill(password)
            
            # Procura botão de submit
            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                'button:has-text("Entrar")', 'button:has-text("Login")',
                'button:has-text("Acessar")'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = await page.wait_for_selector(selector, timeout=2000)
                    if submit_btn:
                        await submit_btn.click()
                        logger.info("Login submetido")
                        break
                except:
                    continue
            
            # Aguarda navegação após login
            await page.wait_for_load_state('networkidle', timeout=settings.nav_timeout * 1000)
            
            # Salva storage_state após login bem-sucedido
            storage_state = await page.context.storage_state()
            with open(self.storage_state_path, 'w') as f:
                json.dump(storage_state, f)
            logger.info(f"Storage state salvo em {self.storage_state_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            return False
    
    async def check_login_required(self, page: Page) -> bool:
        """
        Verifica se a página atual requer login
        
        Args:
            page: Página do Playwright
        
        Returns:
            True se login é necessário
        """
        try:
            # Procura por indicadores de tela de login
            login_indicators = [
                'input[type="password"]',
                'text=usuário',
                'text=senha',
                'text=login',
                'text=entrar'
            ]
            
            for indicator in login_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        logger.info("Tela de login detectada")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Erro ao verificar login: {e}")
            return False
    
    async def select_month_year(self, page: Page, target_date: str) -> bool:
        """
        Seleciona mês/ano no dropdown do portal
        
        Args:
            page: Página do Playwright
            target_date: Data alvo no formato YYYY-MM-DD
        
        Returns:
            True se seleção bem-sucedida
        """
        try:
            from datetime import datetime
            dt = datetime.strptime(target_date, '%Y-%m-%d')
            target_month = dt.month
            target_year = dt.year
            
            logger.info(f"Selecionando mês/ano: {target_month}/{target_year}")
            
            # Procura por select de mês/ano
            select_selectors = [
                'select[name*="mes"]', 'select[name*="month"]',
                'select[id*="mes"]', 'select[id*="month"]',
                'select[name*="periodo"]', 'select[name*="data"]'
            ]
            
            for selector in select_selectors:
                try:
                    select = await page.wait_for_selector(selector, timeout=2000)
                    if select:
                        # Tenta selecionar por valor
                        month_str = f"{target_month:02d}"
                        year_str = str(target_year)
                        
                        # Tenta várias combinações
                        options = [
                            f"{year_str}-{month_str}",
                            f"{month_str}/{year_str}",
                            f"{month_str}-{year_str}",
                            month_str
                        ]
                        
                        for option in options:
                            try:
                                await select.select_option(value=option)
                                logger.info(f"Mês/ano selecionado: {option}")
                                await page.wait_for_load_state('networkidle', timeout=5000)
                                return True
                            except:
                                continue
                except:
                    continue
            
            logger.warning("Não foi possível selecionar mês/ano automaticamente")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao selecionar mês/ano: {e}")
            return False
    
    async def extract_table_data(
        self, 
        page: Page,
        date_selector: str = "td:nth-child(1)",
        kg_selector: str = "td:nth-child(2)"
    ) -> List[Dict[str, Any]]:
        """
        Extrai dados da tabela de uma unidade
        
        Args:
            page: Página do Playwright
            date_selector: Seletor CSS para célula de data
            kg_selector: Seletor CSS para célula de kg
        
        Returns:
            Lista de dicionários com date, kg, raw_date, raw_kg
        """
        try:
            logger.info("Extraindo dados da tabela...")
            
            # Aguarda tabela carregar
            await page.wait_for_load_state('networkidle', timeout=settings.nav_timeout * 1000)
            
            # Tenta encontrar tabela
            table_selectors = [
                'table', 'table#report', 'table.data-table',
                'div[role="table"]', '.table', '#data-table'
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = await page.wait_for_selector(selector, timeout=5000)
                    if table:
                        logger.info(f"Tabela encontrada com seletor: {selector}")
                        break
                except:
                    continue
            
            if not table:
                logger.warning("Nenhuma tabela encontrada na página")
                return []
            
            # Extrai linhas
            rows_data = []
            
            # Tenta extrair via JavaScript
            rows = await page.evaluate("""
                (dateSelector, kgSelector) => {
                    const rows = [];
                    const tableRows = document.querySelectorAll('table tbody tr, table tr');
                    
                    tableRows.forEach(row => {
                        try {
                            const dateCells = row.querySelectorAll(dateSelector);
                            const kgCells = row.querySelectorAll(kgSelector);
                            
                            if (dateCells.length > 0 && kgCells.length > 0) {
                                rows.push({
                                    raw_date: dateCells[0].textContent.trim(),
                                    raw_kg: kgCells[0].textContent.trim()
                                });
                            }
                        } catch (e) {
                            console.error('Erro ao extrair linha:', e);
                        }
                    });
                    
                    return rows;
                }
            """, date_selector, kg_selector)
            
            # Processa cada linha
            for row in rows:
                raw_date = row.get('raw_date', '')
                raw_kg = row.get('raw_kg', '')
                
                parsed_date = parse_date(raw_date)
                parsed_kg = parse_kg(raw_kg)
                
                # Só adiciona se conseguiu parsear ambos
                if parsed_date and parsed_kg is not None:
                    rows_data.append({
                        'date': parsed_date,
                        'kg': parsed_kg,
                        'raw_date': raw_date,
                        'raw_kg': raw_kg
                    })
            
            logger.info(f"Extraídas {len(rows_data)} linhas válidas")
            return rows_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da tabela: {e}")
            return []
    
    async def scrape_unit(
        self,
        unit_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz scraping de uma unidade específica
        
        Args:
            unit_id: ID da unidade
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            username: Nome de usuário para login
            password: Senha para login
        
        Returns:
            Dicionário com unit_id, rows, total, error
        """
        result = {
            'unit_id': unit_id,
            'rows': [],
            'total': 0.0,
            'error': None
        }
        
        context = None
        page = None
        
        try:
            logger.info(f"Iniciando scraping da unidade: {unit_id}")
            
            # Cria contexto com ou sem storage_state
            storage_state = None
            if self.storage_state_path.exists():
                with open(self.storage_state_path, 'r') as f:
                    storage_state = json.load(f)
            
            context = await self.browser.new_context(
                storage_state=storage_state,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # Monta URL da unidade
            if settings.unit_url_template and '{unit_id}' in settings.unit_url_template:
                unit_url = settings.unit_url_template.replace('{unit_id}', str(unit_id))
            else:
                unit_url = f"{settings.portal_url}?unit={unit_id}"
            
            logger.info(f"Navegando para: {unit_url}")
            await page.goto(unit_url, wait_until='networkidle', timeout=settings.nav_timeout * 1000)
            
            # Verifica se precisa fazer login
            if await self.check_login_required(page):
                if not username or not password:
                    raise Exception("Login necessário mas credenciais não fornecidas")
                
                login_success = await self.login(page, username, password)
                if not login_success:
                    raise Exception("Falha no login")
                
                # Navega novamente após login
                await page.goto(unit_url, wait_until='networkidle', timeout=settings.nav_timeout * 1000)
            
            # Seleciona mês/ano se data fornecida
            if start_date:
                await self.select_month_year(page, start_date)
            
            # Extrai dados da tabela
            rows = await self.extract_table_data(page)
            
            # Filtra por data se necessário
            if start_date or end_date:
                rows = filter_rows_by_date(rows, start_date, end_date)
            
            # Calcula total
            total = calculate_total(rows)
            
            result['rows'] = rows
            result['total'] = total
            
            logger.info(f"Unidade {unit_id}: {len(rows)} linhas, total {total} kg")
            
        except PlaywrightTimeout:
            error_msg = f"Timeout ao acessar unidade {unit_id}"
            logger.error(error_msg)
            result['error'] = error_msg
            
        except Exception as e:
            error_msg = f"Erro ao processar unidade {unit_id}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
        
        return result
    
    async def discover_units(self, username: Optional[str] = None, password: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Descobre automaticamente todas as unidades disponíveis
        
        Args:
            username: Nome de usuário para login
            password: Senha para login
        
        Returns:
            Lista de dicionários com unit_id e unit_name
        """
        context = None
        page = None
        units = []
        
        try:
            logger.info("Descobrindo unidades disponíveis...")
            
            # Cria contexto
            storage_state = None
            if self.storage_state_path.exists():
                with open(self.storage_state_path, 'r') as f:
                    storage_state = json.load(f)
            
            context = await self.browser.new_context(
                storage_state=storage_state,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # Navega para página principal
            logger.info(f"Navegando para: {settings.portal_url}")
            await page.goto(settings.portal_url, wait_until='networkidle', timeout=settings.nav_timeout * 1000)
            
            # Verifica login
            if await self.check_login_required(page):
                if not username or not password:
                    raise Exception("Login necessário mas credenciais não fornecidas")
                
                login_success = await self.login(page, username, password)
                if not login_success:
                    raise Exception("Falha no login")
                
                await page.goto(settings.portal_url, wait_until='networkidle', timeout=settings.nav_timeout * 1000)
            
            # Extrai lista de unidades via JavaScript
            units = await page.evaluate("""
                () => {
                    const units = [];
                    
                    // Tenta vários seletores comuns para links de unidades
                    const selectors = [
                        'a[href*="unidade"]',
                        'a[href*="unit"]',
                        '.unit-link',
                        '.unidade-link',
                        'table tbody tr a',
                        'ul.units li a'
                    ];
                    
                    for (const selector of selectors) {
                        const links = document.querySelectorAll(selector);
                        if (links.length > 0) {
                            links.forEach(link => {
                                const text = link.textContent.trim();
                                const href = link.getAttribute('href');
                                
                                // Extrai ID da unidade do href ou texto
                                let unitId = '';
                                if (href) {
                                    const match = href.match(/unidade[=\/]([^&\/]+)|unit[=\/]([^&\/]+)/i);
                                    if (match) {
                                        unitId = match[1] || match[2];
                                    }
                                }
                                
                                if (!unitId && text) {
                                    // Tenta extrair número do texto
                                    const numMatch = text.match(/\\d+/);
                                    if (numMatch) {
                                        unitId = numMatch[0];
                                    }
                                }
                                
                                if (unitId && text) {
                                    units.push({
                                        unit_id: unitId,
                                        unit_name: text
                                    });
                                }
                            });
                            
                            if (units.length > 0) break;
                        }
                    }
                    
                    return units;
                }
            """)
            
            logger.info(f"Descobertas {len(units)} unidades")
            
        except Exception as e:
            logger.error(f"Erro ao descobrir unidades: {e}")
        
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
        
        return units
