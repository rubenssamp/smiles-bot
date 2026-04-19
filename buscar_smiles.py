import asyncio
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright
import os

GMAIL_USER = "rubenssamp@gmail.com"
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]

async def buscar_milhas():
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://www.smiles.com.br/home")
        await page.wait_for_timeout(5000)

        # Aceitar cookies
        try:
            await page.get_by_text("Aceitar").click()
            await page.wait_for_timeout(1000)
        except:
            pass

        # Buscas: ida 21/01, retorno 25/01 e 26/01
        buscas = [
            {"ida": "2027-01-21", "volta": "2027-01-25", "label": "Retorno 25/jan"},
            {"ida": "2027-01-21", "volta": "2027-01-26", "label": "Retorno 26/jan"},
        ]

        for busca in buscas:
            url = (
                "https://www.smiles.com.br/passagem-de-aviao"
                f"?originAirportCode=FOR"
                f"&destinationAirportCode=GRU"
                f"&departureDate={busca['ida']}"
                f"&returnDate={busca['volta']}"
                f"&adults=1&children=0&infants=0"
                f"&tripType=2&cabinType=economic&currencyCode=BRL"
            )

            await page.goto(url)
            await page.wait_for_timeout(8000)

            # Tentar ordenar por menor preço
            try:
                await page.get_by_text("Ordenar").first.click()
                await page.wait_for_timeout(1000)
                await page.get_by_text("Menor preço").first.click()
                await page.wait_for_timeout(4000)
            except:
                pass

            # Capturar milhas
            page_text = await page.inner_text("body")
            milhas = None
            for linha in page_text.split("\n"):
                if "milhas" in linha.lower() and "partir" in linha.lower():
                    milhas = linha.strip()
                    break

            resultados.append(f"{busca['label']}: {milhas or 'Não encontrado'}")
            print(resultados[-1])

        await browser.close()

    return resultados

def enviar_email(resultados):
    corpo = "\n".join(resultados)
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
