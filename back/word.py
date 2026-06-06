from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import os


def agregar_indice(doc):
    """
    Inserta un índice automático de Word.
    Word calcula las páginas cuando se actualiza.
    """

    p = doc.add_paragraph()

    run = p.add_run()

    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')

    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'TOC \\o "1-3" \\h'

    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')


    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)



def agregar_secciones(doc, secciones):

    for sec in secciones:

        titulo = sec.get("titulo", "")
        nivel = sec.get("nivel", 1)

        doc.add_heading(
            titulo,
            level=nivel
        )

        contenido = sec.get("contenido", "")

        if contenido:
            doc.add_paragraph(contenido)


        for sub in sec.get("subsecciones", []):

            agregar_secciones(
                doc,
                [sub]
            )



def generar_word(data, output_path):

    titulo = data.get(
        "titulo",
        "Documento"
    )

    terminos = data.get(
        "terminos",
        []
    )

    secciones = data.get(
        "secciones",
        []
    )

    imagenes_spec = data.get(
        "imagenes",
        []
    )


    doc = Document()


    # Márgenes

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(3)



    # Título

    titulo_par = doc.add_paragraph()

    titulo_par.alignment = WD_ALIGN_PARAGRAPH.CENTER

    titulo_par.paragraph_format.space_after = Pt(24)


    run = titulo_par.add_run(titulo)

    run.bold = True
    run.font.size = Pt(24)
    run.font.name = "Arial"



    # Índice

    if data.get("indice", False):

        doc.add_heading(
            "Índice",
            level=1
        )

        agregar_indice(doc)

        doc.add_page_break()



    # Documento estructurado

    if secciones:

        agregar_secciones(
            doc,
            secciones
        )



    # Formato antiguo de términos

    if terminos:


        for t in terminos:

            nombre = t.get(
                "nombre",
                ""
            )

            definicion = t.get(
                "definicion",
                ""
            )

            palabras_clave = [
                x.lower()
                for x in t.get(
                    "palabras_clave",
                    []
                )
            ]


            par = doc.add_paragraph()

            par.paragraph_format.space_before = Pt(10)
            par.paragraph_format.space_after = Pt(10)


            titulo = par.add_run(
                nombre + ": "
            )

            titulo.bold = True
            titulo.font.size = Pt(12)
            titulo.font.name = "Arial"



            restante = definicion


            while restante:

                posicion = len(restante)
                palabra = None


                for pk in palabras_clave:

                    idx = restante.lower().find(pk)

                    if idx != -1 and idx < posicion:
                        posicion = idx
                        palabra = pk



                if palabra is None:

                    run = par.add_run(restante)
                    run.font.size = Pt(12)
                    break


                if posicion > 0:

                    run = par.add_run(
                        restante[:posicion]
                    )

                    run.font.size = Pt(12)



                sub = par.add_run(
                    restante[
                        posicion:
                        posicion + len(palabra)
                    ]
                )

                sub.underline = True
                sub.font.size = Pt(12)


                restante = restante[
                    posicion + len(palabra):
                ]



    # Imágenes

    if imagenes_spec:

        doc.add_page_break()


        for img_spec in imagenes_spec:


            if isinstance(img_spec, dict):

                img_path = img_spec.get(
                    "path",
                    ""
                )

                escala = img_spec.get(
                    "escala",
                    12
                )

            else:

                img_path = img_spec
                escala = 12



            if os.path.exists(img_path):

                try:

                    escala = max(
                        5,
                        min(
                            18,
                            float(escala)
                        )
                    )


                    p = doc.add_paragraph()

                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


                    doc.add_picture(
                        img_path,
                        width=Cm(escala)
                    )


                except Exception as e:

                    print(
                        "Error imagen:",
                        e
                    )


            else:

                print(
                    "Imagen no encontrada:",
                    img_path
                )



    doc.save(output_path)

    print(
        "Word creado"
    )