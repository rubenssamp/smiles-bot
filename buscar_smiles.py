import asyncio
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright
import os
import re

GMAIL_USER = "rubenssamp@gmail.com"
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]

BUSCAS = [
    {
        "label": "Retorno 25/jan",
        "url": "https://www.smiles.com.br/mfe/emissao-passagem/?adults=1&cabin=ECONOMIC&children=0&departureDate=1800500400000&infants=0&isElegible=false&isFlexibleDateChecked=false&returnDate=1800846000000&searchType=g3&segments=1&tripType=1&originAirport=FOR&originCity=&originCountry=&originAirportIsAny=false&destinationAirport=SAO&destinCity=&destinCountry=&destinAirportIsAny=true&novo-resultado-voos=true"
    },
    {
        "label": "Retorno 26/jan",
        "url": "https://www.smiles.com.br/mfe/emissao-passagem/?adults=1&cabin=ECONOMIC&children=0&departureDate=1800500400000&infants=0&isElegible=false&isFlexibleDateChecked=false&returnDate=1800932400000&searchType=g3&segments=1&tripType=1&originAirport=FOR&originCity=&originCountry=&originAirportIsAny=false&destinationAirport=SAO&destinCity=&destinCountry=&destinAirportIsAny=true&novo-resultado-voos=true"
    },
]

async def buscar_milhas():
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for busca in BUSCAS:
            print(f"Buscando: {busca['label']}")
            await page.goto(busca["url"])
            await page.wait_for_timeout(10000)

            # Tentar aceitar cookies
            try:
                await page.get_by_text("Aceitar").click()
                await page.wait_for_timeout(2000)
            except:
                pass

            # Aguardar mais o carregamento
            await page.wait_for_timeout(8000)

            # Tentar ordenar por menor preço
            try:
                await page.get_by_text("Ordenar").first.click()
                await page.wait_for_timeout(1000)
                await page.get_by_text("Menor preço").first.click()
                await page.wait_for_timeout(5000)
            except:
                print("Botão ordenar não encontrado")

            # Capturar milhas
            page_text = await page.inner_text("body")
            milhas = None

            for linha in page_text.split("\n"):
                linha = linha.strip()
                if "partir" in linha.lower() and "milhas" in linha.lower():
                    milhas = linha
                    break

            # Tentar capturar por regex se não achou
            if not milhas:
                numeros = re.findall(r'[\d\.]+\s*milhas', page_text, re.IGNORECASE)
                if numeros:
                    milhas = f"A partir de {numeros[0]}"

            resultado = f"{busca['label']}: {milhas or 'Não encontrado'}"
            print(resultado)
            resultados.append(resultado)

        await browser.close()

    return resultados

def enviar_email(resultados):
    corpo = "Resultado da busca de passagens FOR → SAO em milhas:\n\n"
    corpo += "\n".join(resultados)
    corpo += "\n\nhttps://www.smiles.com.br"

    msg = MIMEText(corpo)
    msg["Subject"] = "✈️ Smiles | FOR → SAO | Menor preço em milhas"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASS)
        smtp.send_message(msg)
        print("Email enviado!")

async def main():
    resultados = await buscar_milhas()
    enviar_email(resultados)

asyncio.run(main())
