CAMPOS_EMPRESA = [
    ("nombre",      "Nombre de la empresa"),
    ("rubro",       "Rubro / actividad"),
    ("cuit",        "CUIT"),
    ("direccion",   "Direccion"),
    ("responsable", "Responsable / dueno"),
    ("telefono",    "Telefono de contacto"),
    ("email",       "Email de contacto"),
]


def empresa_vacia() -> dict:
    return {campo: "" for campo, _ in CAMPOS_EMPRESA}


def empresa_completa(empresa: dict) -> bool:
    return bool(empresa.get("nombre") and empresa.get("rubro"))


def get_contexto_empresa(sesion: dict | None) -> str:
    if not sesion:
        return ""

    empresa = sesion.get("empresa") or {}
    if not empresa_completa(empresa):
        return ""

    partes = []

    if empresa.get("nombre"):
        partes.append(f'La empresa se llama "{empresa["nombre"]}"')
    if empresa.get("rubro"):
        partes.append(f'rubro {empresa["rubro"]}')
    if empresa.get("cuit"):
        partes.append(f'CUIT {empresa["cuit"]}')
    if empresa.get("direccion"):
        partes.append(f'direccion {empresa["direccion"]}')
    if empresa.get("responsable"):
        partes.append(f'responsable {empresa["responsable"]}')
    if empresa.get("telefono"):
        partes.append(f'telefono {empresa["telefono"]}')
    if empresa.get("email"):
        partes.append(f'email {empresa["email"]}')

    if not partes:
        return ""

    return "CONTEXTO DE EMPRESA: " + ", ".join(partes) + ".\n"


