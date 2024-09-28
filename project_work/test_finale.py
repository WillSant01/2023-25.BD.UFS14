from jsonschema import validate
import json
from main import fetch_ingredient_data, find, extract_link_pdf
from main import trova_valori

url = "https://cir-reports.cir-safety.org/"

ingredient_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "pcpc_ingredientid": {
      "type": "string",
      "format": "uuid"
    },
    "pcpc_ingredientname": {
      "type": "string"
    },
    "pcpc_ciringredientid": {
      "type": "string",
      "format": "uuid"
    },
    "pcpc_ciringredientname": {
      "type": "string"
    },
    "pcpc_cirreportname": {
      "type": "string"
    }
  },
  "required": [
    "pcpc_ingredientid",
    "pcpc_ingredientname",
    "pcpc_ciringredientid",
    "pcpc_ciringredientname",
    "pcpc_cirreportname"
  ]
}



def validate_wrapper(instance, schema):
    try:
        validate(instance=instance, schema=schema)
        return True
    except Exception as e:
        print(f"Schema validation error: {e}")
        return False
    
def test_fetch_ingredient_data():
    ingrediente = fetch_ingredient_data(url, testing = True)

    assert validate_wrapper(ingrediente, ingredient_schema), "Non soddisfa i requisiti per ingrediente CIR"


# Test per la ricerca di un ingrediente specifico
def test_find_ingredient(snapshot):
    snapshot.snapshot_dir = "/workspaces/2023-25.BD.UFS14/project_work"

    # Carica il catalogo una volta sola per questo test
    with open(str(snapshot.snapshot_dir) + "/ingredienti.json", "r") as file:
        catalogo = json.load(file)

    ingrediente = find(catalogo, "1,10-Decanediol")

    # Verifica se l'ingrediente è presente nel catalogo
    assert ingrediente in catalogo, "Ingrediente non presente in ingredienti.json"


def test_extract_link_pdf(snapshot):
    snapshot.snapshot_dir = "/workspaces/2023-25.BD.UFS14/project_work"

    with open(str(snapshot.snapshot_dir) + "/tabella_ingrediente.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    link = extract_link_pdf("940af697-52b5-4a3a-90a6-b9db30ef4a7e", url, html_content)

    assert link == "https://cir-reports.cir-safety.org/view-attachment/?id=94742a1a-c561-614f-9f89-14ce58abfc0b", "link sbagliato o non trovato"


def test_trova_valori(snapshot):
    snapshot.snapshot_dir = "/workspaces/2023-25.BD.UFS14/project_work"

    # Carica il catalogo una volta sola per questo test
    with open(str(snapshot.snapshot_dir) + "/report.txt", "r") as file:
        text = file.read()

    result = trova_valori(text, "NOAEL")

    

    snapshot.assert_match(str(result), "risultati_noael.csv")