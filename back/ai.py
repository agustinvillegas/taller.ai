from back.config import client
import json
import re
import requests
from ddgs import DDGS


def mejorar_prompt(prompt_usuario: str, tipo: str) -> str:
    tipo_str = "Excel con datos tabulares" if tipo == "1" else "Word con definiciones"

    sistema = f"""You are an assistant that improves prompts for generating {tipo_str}.
Take the user input and rewrite it clearly, specifically and in detail.
Add missing context, specify number of columns/terms if not mentioned.
Always request detailed descriptions regardless of what the user says.
The final output (Excel/Word content) must be in Spanish.
Return ONLY the improved prompt, no explanations or comments.
"""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.3
    )
    return completion.choices[0].message.content


def generacion_json(prompt: str, instrucciones: str) -> str:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return completion.choices[0].message.content


def parsear_json(texto: str) -> dict | None:
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def buscar_datos_web(prompt_original: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": (
                "Extract the main product, brand, or topic names from the text. "
                "Return them separated by commas, nothing else. "
                "Example output: televisores samsung, LG, electrodomesticos argentina"
            )},
            {"role": "user", "content": prompt_original}
        ],
        temperature=0,
        max_tokens=50
    )
    keywords = completion.choices[0].message.content.strip()

    resultados = []
    for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
        try:
            results = DDGS().text(f"{kw} Argentina", max_results=2)
            for r in results:
                titulo = r.get("title", "")
                cuerpo = r.get("body", "")
                if titulo and cuerpo:
                    resultados.append(f"{titulo}: {cuerpo}")
                else:
                    resultados.append(titulo or cuerpo)
        except Exception:
            pass

    return "\n".join(resultados[:6]) if resultados else "No se encontraron datos."


def editar_json(json_anterior: str, pedido_usuario: str, instrucciones: str) -> str:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": f"Este es el documento actual:\n{json_anterior}\n\nModificación pedida:\n{pedido_usuario}"}
        ],
        temperature=0
    )
    return completion.choices[0].message.content


def interpretar_fin(respuesta_usuario: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": (
                "The user was asked if they want to modify a document. "
                "Based on their response, return ONLY 'si' if they want to make changes, "
                "or 'no' if they are done. Nothing else."
            )},
            {"role": "user", "content": respuesta_usuario}
        ],
        temperature=0,
        max_tokens=15
    )
    return completion.choices[0].message.content.strip().lower()


def analizar_datos_web(prompt_mejorado: str, datos_web: str, tipo_str: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"""
You are analyzing web search results to extract reliable DESCRIPTIVE information for generating a {tipo_str}.
Focus on preserving descriptive content: product features, characteristics, typical uses, origin, and other factual details that could be used to fill description cells in the document.
Think step by step:
1. What descriptive information from the search results is reliable and specific?
2. What facts (features, specs, origin, typical use) could be used to describe each item?
3. What should NOT be included because it's uncertain or contradictory?
Summarize the verified descriptive facts. Be informative but concise — keep the actual descriptions, features and characteristics in the summary so they can be used as descriptions.
Keep the summary flat and simple. Do not organize by brand or category. Just list the key descriptive facts found.
"""},
            {"role": "user", "content": f"Prompt: {prompt_mejorado}\n\nSearch results:\n{datos_web}"}
        ],
        temperature=0,
        max_tokens=300
    )
    return completion.choices[0].message.content
