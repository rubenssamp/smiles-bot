import smtplib
import os
import re
import time
from email.mime.text import MIMEText
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

GMAIL_USER = "rubenssamp@gmail.com"
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]

BUSCAS = [
    {
        "label": "Retorno 25/jan",
        "url": "https://www.smiles.com.br/mfe/emissao-passagem/?adults=1&cabin=ECONOMIC&children=0&departureDate=1800500400000&infants=0&isElegible=false&isFlexibleDateChecked=false&returnDate=1800846000000&searchType=g3&segments=1&tripType=1&originAirport=FOR&originCity=&originCountry=&originAirportIsAny=false&destinationAirport=SAO&destinCity=&destinCountry=&destinAirportIsAny=true&novo-resultado-voos=true"
    },
    {
        "label": "Retorno 26/jan",
        "url": "https://www.smiles.com.br/mfe/emissao-passagem/?adults=1&cabin=ECONOMIC&children=0&departureDate=1800500400000&infants=0&isEligible=false&isFlexibleDateChecked=false&returnDate=1800932400000&searchType=g3&segments=1&tripType=1&originAirport=FOR&originCity=&originCountry=&originAirportIsAny=false&destinationAirport=SAO&destinCity=&destinCountry=&destinAirportIsAny=true&novo-resultado-voos=true"
    },
]

def buscar_milhas():
    resultados = []
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)

    for busca in BUSCAS:
        print(f"Buscando: {busca['label']}")
        driver.get(busca["url"])
        time.sleep(15)

        try:
            btn = driver.find_element(By.XPATH, "//*[contains(text(),'Aceitar')]")
            btn.click()
            time.sleep(2)
        except:
            pass

        time.sleep(10)

        texto = driver.find_element(By.TAG_NAME, "body").text
        print(texto[:2000])

        milhas = None
        for linha in texto.split("\n"):
            if "partir" in linha.lower() and "milhas" in linha.lower():
                milhas = linha.strip()
                break

        if not milhas:
            nums = re.findall(r'[\d\.]+\s*milhas', texto, re.IGNORECASE)
            if nums:
                milhas = f"A partir de {nums[0]}"

        resultado = f"{busca['label']}: {milhas or 'Não encontrado'}"
        print(resultado)
        resultados.append(resultado)

    driver.quit()
    return resultados

def enviar_email(resultados):
    corpo = "Resultado da busca FOR → SAO em milhas:\n\n"
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

resultados = buscar_milhas()
enviar_email(resultados)
