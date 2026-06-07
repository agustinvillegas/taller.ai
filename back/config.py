import os
import sys
import json
from groq import Groq
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path)

# === Hardcoded defaults (replace these before building .exe) ===
GROQ_API_KEY_DEFAULT = os.getenv("GROQ_API_KEY", "")
FIREBASE_DATABASE_URL_DEFAULT = os.getenv("FIREBASE_URL", "")

# === Runtime values (loaded from config file or defaults) ===
GROQ_API_KEY = ""
FIREBASE_DATABASE_URL = ""
client = None


def _get_config_dir():
    """Directory where the .exe or main.py lives (for taller_ai_config.json)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config():
    global GROQ_API_KEY, FIREBASE_DATABASE_URL, client

    # Priority: 1) env var (dev mode), 2) default constant, 3) config file override
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") or GROQ_API_KEY_DEFAULT
    FIREBASE_DATABASE_URL = os.getenv("FIREBASE_URL") or FIREBASE_DATABASE_URL_DEFAULT

    config_path = os.path.join(_get_config_dir(), "taller_ai_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("groq_api_key"):
                GROQ_API_KEY = cfg["groq_api_key"]
            if cfg.get("firebase_database_url"):
                FIREBASE_DATABASE_URL = cfg["firebase_database_url"]
        except Exception:
            pass

    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
    else:
        client = Groq(api_key="")


def save_config(groq_api_key=None, firebase_database_url=None):
    """Save config to taller_ai_config.json (next to .exe in production, next to project in dev)."""
    config_path = os.path.join(_get_config_dir(), "taller_ai_config.json")
    cfg = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    if groq_api_key is not None:
        cfg["groq_api_key"] = groq_api_key
    if firebase_database_url is not None:
        cfg["firebase_database_url"] = firebase_database_url
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


_load_config()

instrucciones_excel = """
Respond ONLY with valid JSON.

Structure:
{
  "datos": [[...], [...]],
  "columnas": ["col1", "col2"],
  "estilo": {
    "font_size": <number, default 11>,
    "header_color": <hex sin #, default "2F4F7F">,
    "font_color_header": <hex sin #, default "FFFFFF">,
    "row_alt_color": <hex sin #, default "F2F2F2">
  }
}

Rules:
- Only include "grafico" field if the user explicitly asks for a chart
- "grafico" types: "bar", "line", "pie"
- "columna_x" and "columna_y" must match exact column names in "columnas"
- If a calculated column is needed, use EXACTLY these names: "Total", "Subtotal", "IVA", "Promedio", "Cantidad"
- "Total" = price × quantity (final price with taxes)
- "Subtotal" = price before taxes
- "IVA" = tax amount (21% of Subtotal)
- "Promedio" = average of a numeric column
- You MUST use the real data provided under "Verified real data" as the PRIMARY source for any text field (descriptions, characteristics, observations) that the user did NOT provide. Quote, paraphrase, or summarize the verified information to fill empty description cells. Never invent information that contradicts it. NEVER leave description cells empty if the "Verified real data" section contains relevant descriptive information about that item.
- If the user provided a value (text OR number) in the "PRODUCTOS" / "PROVEEDORES" / "CLIENTES" / "VENTAS" section, you MUST use it VERBATIM. Do not modify, round, or replace it.
- If a value was NOT provided by the user AND there is no verified real data, the cell MUST be empty (string "" for text, 0 for numeric). NEVER fill cells with invented values, generic placeholders, or made-up data.
- Price/monetary columns: USE the value provided by the user VERBATIM. If the user did not provide a price, set to 0. NEVER invent or estimate prices from web data or general knowledge.
- Stock/quantity columns: USE the value provided by the user VERBATIM. If not provided, leave empty. NEVER invent stock.
- Description text fields: use what the user provided. If the user did NOT provide a description, USE the "Verified real data" section to write a verified description. If neither source has information, leave EMPTY. NEVER write generic/invented descriptions.
- DO NOT include a "Codigo de Producto" / "Codigo de Cliente" / "Codigo" column unless the user explicitly provided codes in the data. If no codes were provided by the user, OMIT that column entirely from both "columnas" and "datos" — do not even include an empty column.
- don't make up or say anything that isn't proven
- No explanations, no markdown, no extra text
- columnas y datos must match in quantity
- Descriptions must be detailed, specific and distinct from each other
- Data must be realistic and coherent with the context
- Never repeat the same value in a description column
- Style must be coherent with the requested Excel theme
- All text content (column names, data) must be written in Spanish
- CRITICAL: Each row must represent ONE product. Never split products across columns by brand. All products go in the same columns regardless of brand.

DATA RULES (CRITICAL — non-negotiable):
- NUNCA inventes datos personales o identificables: nombres de personas, DNIs, CUITs, teléfonos, direcciones (físicas o de email), números de cuentas bancarias, ni nombres de empresas o personas reales.
- Si el usuario no proveyó estos datos, el campo debe quedar VACÍO (string "" para texto, 0 para numéricos) o con un placeholder como "—" / "Sin datos". NUNCA inventes un valor para llenar el campo.
- Los nombres de clientes, proveedores, empleados y empresas deben provenir exclusivamente del usuario o de los datos verificados de la búsqueda web. Si no hay datos, dejá el campo vacío.
- SÍ podés generar: descripciones de productos, características técnicas, rubros, categorías, condiciones de pago, tipos de servicio y demás datos de conocimiento general.
- Para información verificable (nombres de productos reales, datos de empresas existentes, etc.) usá los datos verificados de la web como fuente primaria. Si no hay datos verificados disponibles, NO inventes — dejá el campo vacío.
- Si el contexto de empresa del usuario aporta datos, usalo como fuente de verdad para esa empresa.

Example of ideal output:
User asks for: "table of yerba mate products with name, description and origin"

{
  "datos": [
    ["Taragüi", "Yerba mate líder del mercado argentino, producida por Establecimiento Las Marías en Corrientes desde 1924. Sabor intenso y equilibrado, con más de 60.000 toneladas producidas por año.", "Corrientes, Argentina"],
    ["Rosamonte", "Yerba tradicional fundada en 1936 en Apóstoles, Misiones. Reconocida por su sabor robusto y su proceso de curado prolongado con palo de rosa, que le da un aroma distintivo.", "Misiones, Argentina"],
    ["CBSé", "Empresa familiar fundada en 1978 en San Francisco, Córdoba. Primera yerba mate compuesta de Argentina, pionera en mezclas con hierbas serranas como menta, poleo y peperina.", "Córdoba, Argentina"]
  ],
  "columnas": ["Nombre", "Descripción", "Origen"],
  "estilo": {
    "font_size": 11,
    "header_color": "2E7D32",
    "font_color_header": "FFFFFF",
    "row_alt_color": "E8F5E9"
  }
}

"""

instrucciones_word = """
CRITICAL: Output ONLY valid JSON. No markdown, no explanations, no extra text. ONLY JSON.

Structure:

{
  "titulo": "Título del documento",

  "secciones": [
    {
      "titulo": "Título de sección",
      "contenido": "Texto completo de la sección",

      "subsecciones": [
        {
          "titulo": "Título de subsección",
          "contenido": "Texto completo"
        }
      ]
    }
  ],

  "terminos": [
    {
      "nombre": "Nombre del término",
      "definicion": "Descripción del término",
      "palabras_clave": [
        "palabra1",
        "palabra2"
      ]
    }
  ],

  "imagenes": [
    {
      "nombre": "image_name",
      "escala": 8
    }
  ]
}


MANDATORY RULES:

0. DATA RULES (CRITICAL — non-negotiable):
- NUNCA inventes datos personales o identificables: nombres de personas, DNIs, CUITs, teléfonos, direcciones (físicas o de email), números de cuentas bancarias, ni nombres de empresas o personas reales.
- Si el usuario no proveyó estos datos, usá un placeholder como "—" o "Sin datos" dentro del texto. NUNCA inventes valores realistas para llenar baches.
- Los nombres propios (personas, clientes, empresas, productos con marca real) deben venir del usuario o de datos verificados. Si no los hay, evitá mencionarlos o indicá "sin información disponible".
- SÍ podés generar: descripciones de productos, características técnicas, rubros, categorías, procesos, metodologías, análisis y demás contenido de conocimiento general.
- Si el contexto de empresa del usuario aporta datos, usalo como fuente de verdad para esa empresa.

1. RESPOND ONLY WITH VALID JSON.

2. Use "secciones" when the user requests:
- informes
- reportes
- ensayos
- manuales
- guías
- documentos largos
- documentos con capítulos o partes

3. "secciones" represents the actual document content.
Every section MUST contain useful text in "contenido".

4. Do NOT create empty sections.
Do NOT use filler text like ".", "...", repeated characters, or placeholders.

5. Use "subsecciones" only when they improve organization.
Do NOT create unnecessary subsections.

6. Do NOT create a manual index.
The document generator will create Word headings and automatic tables of contents.

7. Never include page numbers.

8. "terminos" is only for:
- lists
- glossaries
- catalogs
- product definitions
- concept collections

9. If the user requests products or a catalog, use "terminos".

10. If the user requests an informative document, prefer "secciones".

11. All text MUST be in Spanish.

12. Do NOT ask questions.

13. Do NOT include additional fields.

14. Do NOT include an "indice" field. The document generator will automatically insert a table of contents (TOC) in every Word document.

VALID EXAMPLE:

User:
"Necesito un informe sobre una empresa con introducción, productos y conclusión"

Output:

{
  "titulo": "Informe Empresarial",
  "secciones": [
    {
      "titulo": "Introducción",
      "contenido": "Texto desarrollado de introducción..."
    },
    {
      "titulo": "Productos",
      "contenido": "Descripción general...",
      "subsecciones": [
        {
          "titulo": "Producto principal",
          "contenido": "Descripción detallada..."
        }
      ]
    },
    {
      "titulo": "Conclusión",
      "contenido": "Cierre del informe..."
    }
  ],
  "terminos": [],
  "imagenes": []
}


VALID EXAMPLE:

User:
"Lista de productos de yerba mate con descripción"

Output:

{
  "titulo": "Productos de yerba mate",
  "secciones": [],
  "terminos": [
    {
      "nombre": "Yerba Taragüi",
      "definicion": "Descripción del producto.",
      "palabras_clave": [
        "yerba",
        "mate"
      ]
    }
  ],
  "imagenes": []
}


CRITICAL: Start response with { and end with }. NOTHING ELSE.
"""
