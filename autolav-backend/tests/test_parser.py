"""
Testes unitários para funções de parsing
"""
import pytest
from app.parser import parse_kg, parse_date, filter_rows_by_date, calculate_total, normalize_unit_id


class TestParseKg:
    """Testes para parse_kg"""
    
    def test_parse_kg_simple(self):
        assert parse_kg("123.45") == 123.45
        assert parse_kg("123,45") == 123.45
        assert parse_kg("123") == 123.0
    
    def test_parse_kg_with_unit(self):
        assert parse_kg("123.45 kg") == 123.45
        assert parse_kg("123,45kg") == 123.45
        assert parse_kg("123 KG") == 123.0
    
    def test_parse_kg_with_thousands(self):
        assert parse_kg("1.234,56") == 1234.56
        assert parse_kg("1,234.56") == 1234.56
    
    def test_parse_kg_invalid(self):
        assert parse_kg("") is None
        assert parse_kg("abc") is None
        assert parse_kg("-123") is None
        assert parse_kg(None) is None


class TestParseDate:
    """Testes para parse_date"""
    
    def test_parse_date_iso(self):
        assert parse_date("2025-01-15") == "2025-01-15"
    
    def test_parse_date_brazilian(self):
        assert parse_date("15/01/2025") == "2025-01-15"
        assert parse_date("15-01-2025") == "2025-01-15"
    
    def test_parse_date_with_text(self):
        assert parse_date("Data: 15/01/2025") == "2025-01-15"
    
    def test_parse_date_invalid(self):
        assert parse_date("") is None
        assert parse_date("invalid") is None
        assert parse_date(None) is None


class TestFilterRowsByDate:
    """Testes para filter_rows_by_date"""
    
    def test_filter_no_dates(self):
        rows = [
            {'date': '2025-01-10', 'kg': 100},
            {'date': '2025-01-11', 'kg': 200},
            {'date': '2025-01-12', 'kg': 300}
        ]
        result = filter_rows_by_date(rows)
        assert len(result) == 3
    
    def test_filter_start_date(self):
        rows = [
            {'date': '2025-01-10', 'kg': 100},
            {'date': '2025-01-11', 'kg': 200},
            {'date': '2025-01-12', 'kg': 300}
        ]
        result = filter_rows_by_date(rows, start_date='2025-01-11')
        assert len(result) == 2
        assert result[0]['date'] == '2025-01-11'
    
    def test_filter_end_date(self):
        rows = [
            {'date': '2025-01-10', 'kg': 100},
            {'date': '2025-01-11', 'kg': 200},
            {'date': '2025-01-12', 'kg': 300}
        ]
        result = filter_rows_by_date(rows, end_date='2025-01-11')
        assert len(result) == 2
        assert result[-1]['date'] == '2025-01-11'
    
    def test_filter_date_range(self):
        rows = [
            {'date': '2025-01-10', 'kg': 100},
            {'date': '2025-01-11', 'kg': 200},
            {'date': '2025-01-12', 'kg': 300},
            {'date': '2025-01-13', 'kg': 400}
        ]
        result = filter_rows_by_date(rows, start_date='2025-01-11', end_date='2025-01-12')
        assert len(result) == 2
        assert result[0]['date'] == '2025-01-11'
        assert result[1]['date'] == '2025-01-12'


class TestCalculateTotal:
    """Testes para calculate_total"""
    
    def test_calculate_total_simple(self):
        rows = [
            {'kg': 100.5},
            {'kg': 200.3},
            {'kg': 50.2}
        ]
        assert calculate_total(rows) == 351.0
    
    def test_calculate_total_empty(self):
        assert calculate_total([]) == 0.0
    
    def test_calculate_total_with_none(self):
        rows = [
            {'kg': 100},
            {'kg': None},
            {'kg': 200}
        ]
        assert calculate_total(rows) == 300.0


class TestNormalizeUnitId:
    """Testes para normalize_unit_id"""
    
    def test_normalize_simple(self):
        assert normalize_unit_id("101") == "101"
        assert normalize_unit_id("ABC") == "abc"
    
    def test_normalize_with_spaces(self):
        assert normalize_unit_id(" 101 ") == "101"
        assert normalize_unit_id("Unit 101") == "unit101"
    
    def test_normalize_with_special_chars(self):
        assert normalize_unit_id("Unit-101") == "unit-101"
        assert normalize_unit_id("Unit@101") == "unit101"
    
    def test_normalize_empty(self):
        assert normalize_unit_id("") == ""
        assert normalize_unit_id(None) == ""
