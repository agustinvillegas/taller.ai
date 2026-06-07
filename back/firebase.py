import os
import json
import base64
from datetime import datetime
from urllib.parse import quote
import requests
from back.config import FIREBASE_DATABASE_URL

FIREBASE_URL = FIREBASE_DATABASE_URL.rstrip("/")


def _url(ruta: str) -> str:
    return f"{FIREBASE_URL}/{ruta}.json"


def _g(codigo: str) -> str:
    return f"grupos/{quote(codigo, safe='')}"


def crear_grupo(nombre: str, password: str = "") -> dict | None:
    if not FIREBASE_URL:
        return None

    nombre = nombre.strip()
    if not nombre:
        return None

    check = requests.get(_url(_g(nombre)))
    if check.ok and check.json() is not None:
        return None

    datos = {
        "nombre": nombre,
        "password": password,
        "empresa": {},
        "documentos": {}
    }

    resp = requests.put(_url(_g(nombre)), json=datos)
    if resp.ok:
        return {"codigo": nombre, "nombre_grupo": nombre}
    return None


def unirse_grupo(nombre: str, password: str = "") -> dict | None:
    if not FIREBASE_URL:
        return None

    nombre = nombre.strip()
    if not nombre:
        return None

    resp = requests.get(_url(_g(nombre)))
    if not resp.ok or resp.json() is None:
        return None

    datos = resp.json()

    if datos.get("password"):
        if password != datos["password"]:
            return None

    return {
        "codigo": nombre,
        "nombre_grupo": datos.get("nombre", nombre),
        "empresa": datos.get("empresa") or {}
    }


def guardar_empresa(codigo: str, datos_empresa: dict) -> bool:
    if not FIREBASE_URL:
        return False
    resp = requests.put(_url(f"{_g(codigo)}/empresa"), json=datos_empresa)
    return resp.ok


def cargar_empresa(codigo: str) -> dict:
    if not FIREBASE_URL:
        return {}
    resp = requests.get(_url(f"{_g(codigo)}/empresa"))
    if resp.ok and resp.json():
        return resp.json()
    return {}


def guardar_documento(codigo: str, nombre: str, tipo: str,
                      json_data: dict, archivo_bytes: bytes,
                      doc_id: str = None) -> str | None:
    if not FIREBASE_URL:
        return None

    if not doc_id:
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archivo_b64 = base64.b64encode(archivo_bytes).decode("utf-8")

    datos = {
        "nombre": nombre,
        "tipo": tipo,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "json_data": json_data,
        "archivo_b64": archivo_b64
    }

    resp = requests.put(_url(f"{_g(codigo)}/documentos/{doc_id}"), json=datos)
    if resp.ok:
        return doc_id
    return None


def cargar_documentos(codigo: str) -> list:
    if not FIREBASE_URL:
        return []

    resp = requests.get(_url(f"{_g(codigo)}/documentos"))
    if not resp.ok or not resp.json():
        return []

    docs = []
    for doc_id, datos in resp.json().items():
        if datos:
            docs.append({
                "doc_id": doc_id,
                "nombre": datos.get("nombre", doc_id),
                "tipo": datos.get("tipo", "excel"),
                "fecha": datos.get("fecha", ""),
                "json_data": datos.get("json_data", {})
            })

    docs.sort(key=lambda d: d["fecha"], reverse=True)
    return docs


def descargar_documento(codigo: str, doc_id: str) -> bytes | None:
    if not FIREBASE_URL:
        return None

    resp = requests.get(_url(f"{_g(codigo)}/documentos/{doc_id}/archivo_b64"))
    if not resp.ok or not resp.json():
        return None

    try:
        return base64.b64decode(resp.json())
    except Exception:
        return None


def eliminar_documento(codigo: str, doc_id: str) -> bool:
    if not FIREBASE_URL:
        return False
    resp = requests.delete(_url(f"{_g(codigo)}/documentos/{doc_id}"))
    return resp.ok
