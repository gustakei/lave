#!/usr/bin/env python3
"""
Script para gerar storage_state.json fazendo login manual no portal

Uso:
    python save_session.py --url <URL_DO_PORTAL> --username <USUARIO> --password <SENHA>
"""
import asyncio
import argparse
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def save_session(url: str, username: str, password: str, output_path: str = "./storage/storage_state.json"):
    """
    Faz login no portal e salva o storage_state
    
    Args:
        url: URL do portal
        username: Nome de usuário
        password: Senha
        output_path: Caminho para salvar o storage_state.json
    """
    print(f"Iniciando navegador para {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False para ver o navegador
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("Navegando para o portal...")
        await page.goto(url, wait_until='networkidle')
        
        print("\nProcurando campos de login...")
        
        # Tenta encontrar e preencher campos de login
        try:
            # Campo de usuário
            username_selectors = [
                'input[name="username"]', 'input[name="user"]', 'input[id="username"]',
                'input[type="text"]', 'input[placeholder*="usuário"]'
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = await page.wait_for_selector(selector, timeout=2000)
                    if username_field:
                        print(f"Campo de usuário encontrado: {selector}")
                        break
                except:
                    continue
            
            if username_field:
                await username_field.fill(username)
                print(f"Usuário preenchido: {username}")
            
            # Campo de senha
            password_selectors = [
                'input[name="password"]', 'input[id="password"]', 'input[type="password"]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=2000)
                    if password_field:
                        print(f"Campo de senha encontrado: {selector}")
                        break
                except:
                    continue
            
            if password_field:
                await password_field.fill(password)
                print("Senha preenchida")
            
            # Botão de submit
            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                'button:has-text("Entrar")', 'button:has-text("Login")'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = await page.wait_for_selector(selector, timeout=2000)
                    if submit_btn:
                        print(f"Botão de login encontrado: {selector}")
                        await submit_btn.click()
                        print("Login submetido, aguardando...")
                        break
                except:
                    continue
            
            # Aguarda navegação após login
            await page.wait_for_load_state('networkidle', timeout=30000)
            print("Login concluído!")
            
        except Exception as e:
            print(f"Aviso: {e}")
            print("\nSe o login automático falhou, faça login manualmente no navegador.")
            print("Pressione ENTER após fazer login...")
            input()
        
        # Salva storage_state
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        storage_state = await context.storage_state()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(storage_state, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Storage state salvo em: {output_path}")
        print("\nVocê pode fechar o navegador agora.")
        
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="Gera storage_state.json fazendo login no portal")
    parser.add_argument('--url', required=True, help='URL do portal')
    parser.add_argument('--username', required=True, help='Nome de usuário')
    parser.add_argument('--password', required=True, help='Senha')
    parser.add_argument('--output', default='./storage/storage_state.json', help='Caminho de saída')
    
    args = parser.parse_args()
    
    asyncio.run(save_session(args.url, args.username, args.password, args.output))


if __name__ == "__main__":
    main()
