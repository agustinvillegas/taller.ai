import requests

def obtener_precios_meli(prompt_original):
    palabras = [p.strip(",.") for p in prompt_original.split() if len(p) > 3]
    
    resultados = []
    for termino in palabras:
        try:
            url = f"https://api.mercadolibre.com/sites/MLA/search?q=yerba+{termino}&limit=1"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data["results"]:
                item = data["results"][0]
                resultados.append(f"{item['title']}: ${item['price']}")
        except Exception:
            pass

    return "\n".join(resultados) if resultados else "No se encontraron precios."