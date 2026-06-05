from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def generar_word(data, output_path):
    titulo = data.get("titulo", "Documento")
    terminos = data.get("terminos", [])
    imagenes_spec = data.get("imagenes", [])  # Lista de dicts con "nombre" y "escala"

    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(3)

    titulo_par = doc.add_paragraph()
    titulo_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    titulo_par.paragraph_format.space_after = Pt(24)
    run_titulo = titulo_par.add_run(titulo)
    run_titulo.bold = True
    run_titulo.font.size = Pt(24)
    run_titulo.font.name = "Arial"

    for t in terminos:
        nombre = t.get("nombre", "")
        definicion = t.get("definicion", "")
        palabras_clave = [pk.lower() for pk in t.get("palabras_clave", [])]

        par = doc.add_paragraph()
        par.paragraph_format.space_before = Pt(10)
        par.paragraph_format.space_after = Pt(10)

        run_nombre = par.add_run(nombre + ": ")
        run_nombre.bold = True
        run_nombre.font.size = Pt(12)
        run_nombre.font.name = "Arial"

        restante = definicion
        while restante:
            primer_idx = len(restante)
            primer_palabra = None

            for pk in palabras_clave:
                idx = restante.lower().find(pk)
                if idx != -1 and idx < primer_idx:
                    primer_idx = idx
                    primer_palabra = pk

            if primer_palabra is None:
                run = par.add_run(restante)
                run.font.size = Pt(12)
                run.font.name = "Arial"
                break
            else:
                if primer_idx > 0:
                    run = par.add_run(restante[:primer_idx])
                    run.font.size = Pt(12)
                    run.font.name = "Arial"

                run_sub = par.add_run(restante[primer_idx:primer_idx + len(primer_palabra)])
                run_sub.underline = True
                run_sub.font.size = Pt(12)
                run_sub.font.name = "Arial"

                restante = restante[primer_idx + len(primer_palabra):]

    # Agregar imágenes si existen con su escala especificada
    if imagenes_spec:
        doc.add_paragraph()  # Espacio
        
        for img_spec in imagenes_spec:
            # El img_spec puede ser un dict con "path" y "escala", o solo un path string
            if isinstance(img_spec, dict):
                img_path = img_spec.get("path", "")
                escala = img_spec.get("escala", 12)
            else:
                img_path = img_spec
                escala = 12
            
            if os.path.exists(img_path):
                try:
                    # Validar escala (5-18 cm recomendado)
                    if not isinstance(escala, (int, float)):
                        escala = 12
                    escala = max(5, min(18, escala))  # Limitar entre 5 y 18
                    
                    img_par = doc.add_paragraph()
                    img_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_picture(img_path, width=Cm(escala))
                    
                    # Espacio después de imagen
                    img_par = doc.add_paragraph()
                    img_par.paragraph_format.space_after = Pt(12)
                except Exception as e:
                    print(f"Error al agregar imagen: {e}")
            else:
                print(f"Imagen no encontrada: {img_path}")

    doc.save(output_path)
    print("Word creado")