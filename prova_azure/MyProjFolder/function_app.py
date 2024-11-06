import azure.functions as func
import logging
import requests
from bs4 import BeautifulSoup
import pypdf
import re
import json
import os

app = func.FunctionApp()

# Incorpora le funzioni del tuo progetto di scraping
def fetch_ingredient_data(url):
    response1 = requests.get(url + "FetchCIRReports/")
    response1.raise_for_status()
    documento1 = response1.json()["results"]
    cookie = response1.json()["pagingcookie"] + "&page=2"
    response2 = requests.get(response1.url + "?&pagingcookie=" + cookie)
    response2.raise_for_status()
    documento2 = response2.json()["results"]
    return documento1 + documento2

def find(ingredienti, ingrediente_richiesto):
    for record in ingredienti:
        if ingrediente_richiesto == record["pcpc_ingredientname"]:
            return record["pcpc_ingredientid"]
    return None

def extract_link_pdf(ID_ingrediente, url_base):
    if ID_ingrediente is None:
        return None
    response = requests.get(url_base + "cir-ingredient-status-report/?id=" + ID_ingrediente)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    link = soup.find('table').find('a', href=True, string=lambda s: s and not s.startswith('javascript:alert'))
    return url_base + link['href'][3:] if link else None

def download_and_extract_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    response.raise_for_status()

    temp_pdf_path = '/tmp/report.pdf'
    with open(temp_pdf_path, 'wb') as f:
        f.write(response.content)

    with open(temp_pdf_path, 'rb') as pdf_file:
        reader = pypdf.PdfReader(pdf_file)
        full_text = ''.join([page.extract_text().replace('\n', ' ') for page in reader.pages])

    os.remove(temp_pdf_path)
    
    return full_text

@app.route(route="MyScraperFunction", auth_level=func.AuthLevel.ANONYMOUS)
def MyScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing ingredient request in MyScraperFunction.")

    ingrediente_richiesto = req.params.get('ingrediente')
    if not ingrediente_richiesto:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            ingrediente_richiesto = req_body.get('ingrediente')

    if not ingrediente_richiesto:
        return func.HttpResponse(
            "Per favore specifica un ingrediente nella query string o nel corpo della richiesta.",
            status_code=400
        )

    suffisso_url = "https://cir-reports.cir-safety.org/"

    try:
        ingredienti_cir = fetch_ingredient_data(suffisso_url)
        ID_ingrediente = find(ingredienti_cir, ingrediente_richiesto)
        pdf_link = extract_link_pdf(ID_ingrediente, suffisso_url)
        
        if pdf_link:
            full_text = download_and_extract_pdf_text(pdf_link)
            return func.HttpResponse(
                json.dumps({"testo": full_text[:500]}),
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                f"Report PDF per l'ingrediente '{ingrediente_richiesto}' non trovato.",
                status_code=404
            )
    except Exception as e:
        logging.error("Errore nello scraping", exc_info=True)
        return func.HttpResponse(
            f"Si è verificato un errore: {str(e)}",
            status_code=500
        )
