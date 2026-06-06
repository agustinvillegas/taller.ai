import os
from groq import Groq
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY)

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
- You MUST use the real data provided under "Real data found" as the primary source. Never invent information that contradicts it.
- don't make up or say anything that isn't proven
- No explanations, no markdown, no extra text
- columnas y datos must match in quantity
- Descriptions must be detailed, specific and distinct from each other
- Data must be realistic and coherent with the context
- Never repeat the same value in a description column
- Style must be coherent with the requested Excel theme
- All text content (column names, data) must be written in Spanish
- NEVER fill price or monetary columns with values, always set them to 0. This is mandatory.
- CRITICAL: Each row must represent ONE product. Never split products across columns by brand. All products go in the same columns regardless of brand.

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
