import os
import json

_APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
_SESION_DIR = os.path.join(_APPDATA, "taller_ai")
_SESION_PATH = os.path.join(_SESION_DIR, "sesion.json")


def guardar_sesion(codigo: str, nombre_grupo: str, empresa: dict = None):
    os.makedirs(_SESION_DIR, exist_ok=True)
    datos = {
        "codigo": codigo,
        "nombre_grupo": nombre_grupo,
        "empresa": empresa or {}
    }
    with open(_SESION_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def cargar_sesion() -> dict | None:
    if not os.path.exists(_SESION_PATH):
        return None
    try:
        with open(_SESION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def cerrar_sesion():
    if os.path.exists(_SESION_PATH):
        os.remove(_SESION_PATH)


def actualizar_empresa_sesion(empresa: dict):
    sesion = cargar_sesion()
    if sesion:
        sesion["empresa"] = empresa
        guardar_sesion(sesion["codigo"], sesion["nombre_grupo"], empresa)
