"""
Funções de parsing e processamento de dados
"""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dateutil import parser as date_parser
from .logger import logger


def parse_kg(text: str) -> Optional[float]:
    """
    Extrai valor numérico de kg de uma string
    
    Args:
        text: String contendo o valor (ex: "123,45 kg", "123.45", "123,45")
    
    Returns:
        Valor float ou None se não conseguir parsear
    """
    if not text:
        return None
    
    try:
        # Remove espaços e converte para string
        text = str(text).strip()
        
        # Remove unidades comuns
        text = re.sub(r'\s*(kg|KG|Kg|quilos?|kilos?)\s*', '', text, flags=re.IGNORECASE)
        
        # Remove caracteres não numéricos exceto vírgula, ponto e sinal negativo
        text = re.sub(r'[^\d,.\-]', '', text)
        
        if not text or text in ['-', '.', ',']:
            return None
        
        # Substitui vírgula por ponto (formato brasileiro)
        text = text.replace(',', '.')
        
        # Remove pontos extras (separadores de milhar)
        parts = text.split('.')
        if len(parts) > 2:
            # Se tem mais de um ponto, os primeiros são separadores de milhar
            text = ''.join(parts[:-1]) + '.' + parts[-1]
        
        value = float(text)
        return value if value >= 0 else None
        
    except (ValueError, AttributeError) as e:
        logger.debug(f"Erro ao parsear kg '{text}': {e}")
        return None


def parse_date(text: str, fuzzy: bool = True) -> Optional[str]:
    """
    Extrai e normaliza data de uma string
    
    Args:
        text: String contendo a data (vários formatos aceitos)
        fuzzy: Se True, tenta extrair data de texto com outras informações
    
    Returns:
        Data no formato ISO (YYYY-MM-DD) ou None
    """
    if not text:
        return None
    
    try:
        text = str(text).strip()
        
        # Tenta parsear com dateutil (aceita vários formatos)
        dt = date_parser.parse(text, fuzzy=fuzzy, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
        
    except (ValueError, AttributeError) as e:
        logger.debug(f"Erro ao parsear data '{text}': {e}")
        return None


def filter_rows_by_date(
    rows: List[Dict[str, Any]], 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filtra linhas por intervalo de datas
    
    Args:
        rows: Lista de dicionários com chave 'date'
        start_date: Data inicial (formato ISO)
        end_date: Data final (formato ISO)
    
    Returns:
        Lista filtrada
    """
    if not rows:
        return []
    
    filtered = []
    
    for row in rows:
        date_str = row.get('date')
        if not date_str:
            continue
        
        # Verifica se está no intervalo
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        
        filtered.append(row)
    
    return filtered


def calculate_total(rows: List[Dict[str, Any]]) -> float:
    """
    Calcula total de kg de uma lista de linhas
    
    Args:
        rows: Lista de dicionários com chave 'kg'
    
    Returns:
        Soma total
    """
    total = 0.0
    
    for row in rows:
        kg = row.get('kg')
        if kg is not None and isinstance(kg, (int, float)):
            total += kg
    
    return round(total, 2)


def normalize_unit_id(unit_id: str) -> str:
    """
    Normaliza ID de unidade (remove espaços, caracteres especiais)
    
    Args:
        unit_id: ID original
    
    Returns:
        ID normalizado
    """
    if not unit_id:
        return ""
    
    # Remove espaços e caracteres especiais, mantém apenas alfanuméricos e hífen
    normalized = re.sub(r'[^\w\-]', '', str(unit_id).strip())
    return normalized.lower()


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Valida e normaliza intervalo de datas
    
    Args:
        start_date: Data inicial
        end_date: Data final
    
    Returns:
        Tupla (start_date, end_date) normalizada
    """
    if start_date:
        start_date = parse_date(start_date, fuzzy=False)
    
    if end_date:
        end_date = parse_date(end_date, fuzzy=False)
    
    # Se apenas uma data foi fornecida, usar a mesma para início e fim
    if start_date and not end_date:
        end_date = start_date
    elif end_date and not start_date:
        start_date = end_date
    
    # Garantir que start <= end
    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date
    
    return start_date, end_date
