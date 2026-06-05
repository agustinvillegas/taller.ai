import customtkinter as ctk
import threading
import json
import os
from datetime import datetime
from back.ai import analizar_datos_web
from back.mail import enviar_mail
import re

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLORS = {
    "bg": "#0f0f0f",
    "surface": "#1a1a1a",
    "surface2": "#242424",
    "accent": "#00ff88",
    "accent_dim": "#00cc6a",
    "text": "#ffffff",
    "text_dim": "#888888",
    "ai_bubble": "#1e2d1e",
    "user_bubble": "#1a1a2e",
    "border": "#2a2a2a",
    "error": "#ff4444",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCELS_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "excels"))
WORDS_DIR  = os.path.normpath(os.path.join(BASE_DIR, "..", "words"))
GALLERY_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "gallery"))
GALLERY_INDEX = os.path.join(GALLERY_DIR, "index.json")


def escanear_biblioteca():
    entries = []
    for carpeta, tipo, ext in [(EXCELS_DIR, "excel", ".xlsx"), (WORDS_DIR, "word", ".docx")]:
        if not os.path.exists(carpeta):
            continue
        for fname in os.listdir(carpeta):
            if fname.endswith(ext):
                fpath = os.path.join(carpeta, fname)
                nombre = fname[:-len(ext)]
                fecha = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
                entries.append({
                    "nombre": nombre,
                    "tipo": tipo,
                    "fecha": fecha,
                    "path": fpath,
                    "json_path": os.path.join(carpeta, nombre + ".json")
                })
    entries.sort(key=lambda e: e["fecha"], reverse=True)
    return entries


def guardar_json_documento(path_archivo, data):
    base = os.path.splitext(path_archivo)[0]
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_json_documento(path_archivo):
    base = os.path.splitext(path_archivo)[0]
    json_path = base + ".json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def cargar_galeria():
    """Carga el índice de imágenes disponibles"""
    os.makedirs(GALLERY_DIR, exist_ok=True)
    if os.path.exists(GALLERY_INDEX):
        with open(GALLERY_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_galeria(galeria):
    """Guarda el índice de imágenes"""
    os.makedirs(GALLERY_DIR, exist_ok=True)
    with open(GALLERY_INDEX, "w", encoding="utf-8") as f:
        json.dump(galeria, f, ensure_ascii=False, indent=2)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("docs ")
        self.geometry("800x600")
        self.minsize(700, 500)
        self.configure(fg_color=COLORS["bg"])
        self.current_frame = None
        self.mostrar_menu()

    def cambiar_frame(self, frame_class, **kwargs):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

    def mostrar_menu(self):
        self.cambiar_frame(MenuFrame)

    def mostrar_chat(self, tipo, json_inicial=None, path_inicial=None):
        self.cambiar_frame(ChatFrame, tipo=tipo, json_inicial=json_inicial, path_inicial=path_inicial)

    def mostrar_biblioteca(self):
        self.cambiar_frame(BibliotecaFrame)

    def mostrar_galeria(self):
        self.cambiar_frame(GaleriaFrame)


class MenuFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLORS["bg"])

        ctk.CTkLabel(
            self,
            text="ia documents",
            font=ctk.CTkFont(family="Courier New", size=48, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(80, 8))

        ctk.CTkLabel(
            self,
            text="documents generator whit ai (now using llama-3.3-70b-versatile)",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_dim"]
        ).pack(pady=(0, 60))

        btn_cfg = dict(
            width=260, height=52,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=8,
        )

        ctk.CTkButton(
            self, text="📊  Generar Excel",
            fg_color=COLORS["surface2"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=lambda: master.mostrar_chat("excel"),
            **btn_cfg
        ).pack(pady=8)

        ctk.CTkButton(
            self, text="📄  Generar Word",
            fg_color=COLORS["surface2"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=lambda: master.mostrar_chat("word"),
            **btn_cfg
        ).pack(pady=8)

        ctk.CTkButton(
            self, text="📁  Biblioteca",
            fg_color=COLORS["surface"], hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"],
            command=master.mostrar_biblioteca,
            **btn_cfg
        ).pack(pady=8)

        ctk.CTkButton(
            self, text="🖼️  Galería",
            fg_color=COLORS["surface"], hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"],
            command=master.mostrar_galeria,
            **btn_cfg
        ).pack(pady=8)


class ChatFrame(ctk.CTkFrame):
    def __init__(self, master, tipo, json_inicial=None, path_inicial=None):
        super().__init__(master, fg_color=COLORS["bg"])
        self.master = master
        self.tipo = tipo
        self.seleccion = "1" if tipo == "excel" else "2"
        self.ultimo_json = json_inicial
        self.ultimo_path = path_inicial

        # Si viene con JSON, arranca directo en modo edición
        if json_inicial and path_inicial:
            self.estado = "editando"
        else:
            self.estado = "esperando_prompt"

        self._build_ui()
        self.after(300, self._saludo_inicial)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=52, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="←", width=40, height=36,
            fg_color="transparent", hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"],
            command=self.master.mostrar_menu,
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=8, pady=8)

        tipo_str = "Excel" if self.tipo == "excel" else "Word"
        modo = " — Editando" if self.estado == "editando" else ""
        ctk.CTkLabel(
            header,
            text=f"Generar {tipo_str}{modo}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=4)

        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.chat_scroll.pack(fill="both", expand=True)

        input_bar = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=64, corner_radius=0)
        input_bar.pack(fill="x")
        input_bar.pack_propagate(False)

        self.input_box = ctk.CTkEntry(
            input_bar,
            placeholder_text="Escribí acá...",
            fg_color=COLORS["surface2"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            height=40, corner_radius=8
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=12)
        self.input_box.bind("<Return>", lambda e: self._enviar())

        self.btn_enviar = ctk.CTkButton(
            input_bar, text="Enviar",
            width=90, height=40,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_dim"],
            text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8, command=self._enviar
        )
        self.btn_enviar.pack(side="right", padx=(0, 12), pady=12)

    def _agregar_burbuja(self, texto, es_ia=True):
        color = COLORS["ai_bubble"] if es_ia else COLORS["user_bubble"]
        anchor = "w" if es_ia else "e"
        prefix = "🤖  " if es_ia else ""

        wrapper = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        wrapper.pack(fill="x", pady=4, padx=12)

        ctk.CTkLabel(
            wrapper,
            text=prefix + texto,
            fg_color=color,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            wraplength=520,
            justify="left",
            anchor="w",
            padx=14, pady=10
        ).pack(anchor=anchor)
        self.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _agregar_boton_abrir(self, path):
        wrapper = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        wrapper.pack(fill="x", pady=4, padx=12)
        ctk.CTkButton(
            wrapper, text="📂  Abrilo acá",
            width=160, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_dim"],
            text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=lambda: os.startfile(path) if os.path.exists(path) else None
        ).pack(anchor="w")
        self.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _set_input(self, habilitado):
        state = "normal" if habilitado else "disabled"
        self.input_box.configure(state=state)
        self.btn_enviar.configure(state=state)

    def _extraer_imagenes(self, prompt):
        """Extrae referencias a imágenes del prompt (/nombreimg o /nombreimg:escala)
        Ejemplos:
        - /logo → logo con 12cm (default)
        - /logo:8 → logo con 8cm
        - /foto:6 → foto con 6cm
        """
        import re
        galeria = cargar_galeria()
        
        # Buscar patrones /nombreimg o /nombreimg:numero
        matches = re.findall(r'/(\w+)(?::(\d+))?', prompt)
        imagenes = []
        prompt_limpio = prompt
        
        for match in matches:
            nombre_img = match[0]
            escala_str = match[1]
            
            if nombre_img in galeria:
                # Convertir escala a número, default 12
                try:
                    escala = int(escala_str) if escala_str else 12
                    # Validar rango (5-18 cm recomendado)
                    escala = max(5, min(18, escala))
                except ValueError:
                    escala = 12
                
                # Agregar con escala especificada
                imagenes.append({
                    "nombre": nombre_img,
                    "path": galeria[nombre_img]["path"],
                    "escala": escala
                })
                
                # Remover referencia del prompt
                if escala_str:
                    prompt_limpio = re.sub(rf'/\b{nombre_img}\b:\d+', '', prompt_limpio)
                else:
                    prompt_limpio = re.sub(rf'/\b{nombre_img}\b(?::\d+)?', '', prompt_limpio)
        
        return imagenes, prompt_limpio.strip()

    def _saludo_inicial(self):
        if self.estado == "editando":
            nombre = os.path.splitext(os.path.basename(self.ultimo_path))[0]
            self._agregar_burbuja(f"Editando '{nombre}'. ¿Qué querés modificar?")
        else:
            tipo_str = "Excel" if self.tipo == "excel" else "Word"
            self._agregar_burbuja(f"Hola! Describí el {tipo_str} que querés generar.")

    def _enviar(self):
        texto = self.input_box.get().strip()
        if not texto:
            return
        self.input_box.delete(0, "end")
        self._agregar_burbuja(texto, es_ia=False)
        self._set_input(False)

        if self.estado == "esperando_prompt":
            self._agregar_burbuja("Procesando tu pedido...")
            threading.Thread(target=self._generar, args=(texto,), daemon=True).start()
        elif self.estado == "esperando_nombre":
            self._guardar_archivo(texto)
        elif self.estado == "editando":
            self._agregar_burbuja("Aplicando cambios...")
            threading.Thread(target=self._editar, args=(texto,), daemon=True).start()

    def _generar(self, prompt):
        try:
            from back.ai import mejorar_prompt, buscar_datos_web, generacion_json, parsear_json, analizar_datos_web
            from back.config import instrucciones_excel, instrucciones_word

            # Extraer imágenes del prompt del usuario
            imagenes, prompt_limpio = self._extraer_imagenes(prompt)

            self._agregar_burbuja("Mejorando tu prompt...")
            prompt_mejorado = mejorar_prompt(prompt_limpio, self.seleccion)

            if self.seleccion == "1":
                self._agregar_burbuja("Buscando datos en la web...")
                datos_web = buscar_datos_web(prompt_mejorado)
                self._agregar_burbuja("Analizando datos encontrados...")
                datos_analizados = analizar_datos_web(prompt_mejorado, datos_web, "Excel")
                prompt_final = f"{prompt_mejorado}\n\nVerified real data:\n{datos_analizados}"
            else:
                prompt_final = prompt_mejorado

            instrucciones = instrucciones_excel if self.seleccion == "1" else instrucciones_word
            contenido = generacion_json(prompt_final, instrucciones)

            data = parsear_json(contenido)
            if data is None:
                self._agregar_burbuja("No pude generar un resultado válido. Intentá de nuevo.")
                self._set_input(True)
                return

            # Agregar imágenes extraídas del prompt al JSON (solo para Word)
            if imagenes and self.seleccion == "2":
                data["imagenes"] = imagenes
                # Crear mensaje con detalles de imágenes
                detalles = ", ".join([f"{img['nombre']} ({img['escala']}cm)" for img in imagenes])
                self._agregar_burbuja(f"✓ Imágenes añadidas: {detalles}")

            self.ultimo_json = data
            self.estado = "esperando_nombre"
            self._agregar_burbuja("¡Listo! ¿Qué nombre le ponés al archivo? (sin extensión)")
            self._set_input(True)

        except Exception as e:
            self._agregar_burbuja(f"Error: {str(e)}")
            self._set_input(True)

    def _guardar_archivo(self, nombre):
        try:
            import pandas as pd
            from back.excel import formatear_excel, aplicar_formulas
            from back.word import generar_word
            from openpyxl import load_workbook

            os.makedirs(EXCELS_DIR if self.seleccion == "1" else WORDS_DIR, exist_ok=True)

            if self.seleccion == "1":
                path = os.path.join(EXCELS_DIR, nombre + ".xlsx")
                df = pd.DataFrame(self.ultimo_json["datos"], columns=self.ultimo_json["columnas"])
                df.to_excel(path, index=False)
                formatear_excel(path, self.ultimo_json.get("estilo", {}))
            else:
                path = os.path.join(WORDS_DIR, nombre + ".docx")
                generar_word(self.ultimo_json, path)

            guardar_json_documento(path, self.ultimo_json)
            self.ultimo_path = path

            self._agregar_burbuja(f"Archivo guardado ✓ (NOTE: please check before use it, can be wrong)")
            self._agregar_boton_abrir(path)
            self._agregar_burbuja("you can get it via mail in the section biblioteca")
            self._agregar_burbuja("¿Querés modificar algo? Describí los cambios o escribí 'no' para terminar.")
            self.estado = "editando"
            self._set_input(True)

        except Exception as e:
            self._agregar_burbuja(f"Error al guardar: {str(e)}")
            self._set_input(True)

    def _editar(self, pedido):
        from back.ai import interpretar_fin
    
        intencion = interpretar_fin(pedido)
        if intencion == "no":
            self._agregar_burbuja("Perfecto. Podés volver al menú cuando quieras.")
            self._set_input(True)
            return
    
        # Extraer imágenes del pedido del usuario
        imagenes, pedido_limpio = self._extraer_imagenes(pedido)

        try:
            from back.ai import editar_json, parsear_json
            from back.config import instrucciones_excel, instrucciones_word
            from back.excel import formatear_excel, aplicar_formulas
            from back.word import generar_word
            from openpyxl import load_workbook
            import pandas as pd

            instrucciones = instrucciones_excel if self.seleccion == "1" else instrucciones_word
            contenido = editar_json(
                json.dumps(self.ultimo_json, ensure_ascii=False),
                pedido_limpio,
                instrucciones
            )

            data = parsear_json(contenido)
            if data is None:
                self._agregar_burbuja("No pude aplicar los cambios. Intentá describir la modificación de otra forma.")
                self._set_input(True)
                return

            # Agregar o reemplazar imágenes si el usuario las especificó
            if imagenes and self.seleccion == "2":
                data["imagenes"] = imagenes
                detalles = ", ".join([f"{img['nombre']} ({img['escala']}cm)" for img in imagenes])
                self._agregar_burbuja(f"✓ Imágenes añadidas: {detalles}")

            self.ultimo_json = data
            path = self.ultimo_path

            if path:
                if self.seleccion == "1":
                    df = pd.DataFrame(data["datos"], columns=data["columnas"])
                    df.to_excel(path, index=False)
                    formatear_excel(path, data.get("estilo", {}))
                else:
                    generar_word(data, path)

                guardar_json_documento(path, data)

            self._agregar_burbuja("Cambios aplicados ✓ ¿Algo más?")
            self._agregar_boton_abrir(path)
            self._set_input(True)

        except Exception as e:
            self._agregar_burbuja(f"Error: {str(e)}")
            self._set_input(True)


class BibliotecaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLORS["bg"])
        self.master = master
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=52, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="←", width=40, height=36,
            fg_color="transparent", hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"],
            command=self.master.mostrar_menu,
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=8, pady=8)

        ctk.CTkLabel(
            header, text="Biblioteca",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=4)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        self.scroll.pack(fill="both", expand=True, padx=16, pady=16)

        self._cargar_entradas()

    def _cargar_entradas(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        entries = escanear_biblioteca()

        if not entries:
            ctk.CTkLabel(
                self.scroll,
                text="No hay archivos generados todavía.",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=14)
            ).pack(pady=40)
            return

        for entry in entries:
            self._agregar_entrada(entry)

    def _agregar_entrada(self, entry):
        row = ctk.CTkFrame(self.scroll, fg_color=COLORS["surface"], corner_radius=8)
        row.pack(fill="x", pady=5)

        icono = "📊" if entry["tipo"] == "excel" else "📄"
        ctk.CTkLabel(
            row,
            text=f"{icono}  {entry['nombre']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"], anchor="w"
        ).pack(side="left", padx=14, pady=12)

        ctk.CTkLabel(
            row, text=entry["fecha"],
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"]
        ).pack(side="left", padx=8)

        # Botón borrar
        ctk.CTkButton(
            row, text="🗑",
            width=36, height=30,
            fg_color=COLORS["surface2"], hover_color=COLORS["error"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=14),
            corner_radius=6,
            command=lambda e=entry, r=row: self._borrar(e, r)
        ).pack(side="right", padx=(0, 8), pady=12)

        # Botón editar
        ctk.CTkButton(
            row, text="✏️ Editar",
            width=80, height=30,
            fg_color=COLORS["surface2"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
            command=lambda e=entry: self._editar(e)
        ).pack(side="right", padx=(0, 6), pady=12)

        # Botón abrir
        ctk.CTkButton(
            row, text="Abrir",
            width=70, height=30,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_dim"],
            text_color="#000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
            command=lambda p=entry["path"]: os.startfile(p) if os.path.exists(p) else None
        ).pack(side="right", padx=(0, 6), pady=12)
        # Botón mail
        ctk.CTkButton(
            row, text="✉ Mail",
            width=80, height=30,
            fg_color=COLORS["surface2"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
            command=lambda e=entry: self._abrir_mail_popup(e)
        ).pack(side="right", padx=(0, 6), pady=12)

    def _borrar(self, entry, row):
        if os.path.exists(entry["path"]):
            os.remove(entry["path"])
        if os.path.exists(entry["json_path"]):
            os.remove(entry["json_path"])
        row.destroy()

    def _editar(self, entry):
        data = cargar_json_documento(entry["path"])
        if data is None:
            print("No se encontró el JSON asociado")
            return
        self.master.mostrar_chat(
            tipo=entry["tipo"],
            json_inicial=data,
            path_inicial=entry["path"]
        )

    #pop up mail usuario
    def _abrir_mail_popup(self, entry):
        top = ctk.CTkToplevel(self)
        top.title("Enviar archivo")
        top.geometry("350x160")

        ctk.CTkLabel(
            top,
            text="Ingresa tu mail para recibir tu archivo",
            text_color=COLORS["text"]
        ).pack(pady=(15, 5))

        entry_mail = ctk.CTkEntry(
            top,
            width=250,
            fg_color=COLORS["surface2"],
            text_color=COLORS["text"]
        )
        entry_mail.pack(pady=5)

        error_label = ctk.CTkLabel(
            top,
            text="",
            text_color=COLORS["error"]
        )
        error_label.pack()

        def validar_email(mail):
            return re.match(r"^[^@]+@[^@]+\.[^@]+$", mail)

        def enviar():
            mail = entry_mail.get().strip()
            archivo = entry["path"]

            if not validar_email(mail):
                error_label.configure(text="Mail inválido")
                return

            try:
                enviar_mail(mail, archivo)
                top.destroy()
            except Exception as e:
                error_label.configure(text="Error al enviar")

        ctk.CTkButton(
            top,
            text="Enviar",
            fg_color=COLORS["accent"],
            text_color="#000000",
            command=enviar
        ).pack(pady=10)


class GaleriaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLORS["bg"])
        self.master = master
        self.galeria = cargar_galeria()
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=52, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="←", width=40, height=36,
            fg_color="transparent", hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"],
            command=self.master.mostrar_menu,
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=8, pady=8)

        ctk.CTkLabel(
            header, text="Galería de Imágenes",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            header, text="+ Subir",
            width=80, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_dim"],
            text_color="#000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._cargar_imagen
        ).pack(side="right", padx=(0, 8), pady=8)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        self.scroll.pack(fill="both", expand=True, padx=16, pady=16)

        self._cargar_imagenes()

    def _cargar_imagenes(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not self.galeria:
            ctk.CTkLabel(
                self.scroll,
                text="No hay imágenes cargadas. ¡Subí una!",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=14)
            ).pack(pady=40)
            return

        for nombre, datos in self.galeria.items():
            self._agregar_imagen(nombre, datos)

    def _agregar_imagen(self, nombre, datos):
        row = ctk.CTkFrame(self.scroll, fg_color=COLORS["surface"], corner_radius=8)
        row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            row,
            text=f"🖼️  {nombre}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"], anchor="w"
        ).pack(side="left", padx=14, pady=12)

        ctk.CTkLabel(
            row, text=f"/{nombre}",
            font=ctk.CTkFont(size=11, family="Courier New"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=8)

        # Botón copiar comando
        def copiar_comando():
            import tkinter as tk
            self.clipboard_clear()
            self.clipboard_append(f"/{nombre}")
            self.update()

        ctk.CTkButton(
            row, text="📋",
            width=36, height=30,
            fg_color=COLORS["surface2"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=14),
            corner_radius=6,
            command=copiar_comando
        ).pack(side="right", padx=(0, 6), pady=12)

        # Botón borrar
        ctk.CTkButton(
            row, text="🗑",
            width=36, height=30,
            fg_color=COLORS["surface2"], hover_color=COLORS["error"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=14),
            corner_radius=6,
            command=lambda n=nombre: self._borrar_imagen(n, row)
        ).pack(side="right", padx=(0, 6), pady=12)

    def _cargar_imagen(self):
        from tkinter import filedialog
        import shutil

        ruta = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp"), ("Todos", "*.*")]
        )

        if not ruta:
            return

        try:
            # Intentar validar con PIL si está disponible
            try:
                from PIL import Image
                img = Image.open(ruta)
                img.verify()
            except ImportError:
                # Si PIL no está disponible, solo verificar que sea un archivo
                pass
            except Exception as e:
                print(f"Archivo de imagen inválido: {e}")
                return

            # Obtener nombre sin extensión
            nombre = os.path.splitext(os.path.basename(ruta))[0]

            # Si el nombre ya existe, agregar número
            nombre_original = nombre
            contador = 1
            while nombre in self.galeria:
                nombre = f"{nombre_original}_{contador}"
                contador += 1

            # Crear directorio si no existe
            os.makedirs(GALLERY_DIR, exist_ok=True)

            # Copiar archivo
            ext = os.path.splitext(ruta)[1]
            path_dest = os.path.join(GALLERY_DIR, nombre + ext)
            shutil.copy2(ruta, path_dest)

            # Guardar en índice
            self.galeria[nombre] = {
                "path": path_dest,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            guardar_galeria(self.galeria)

            # Actualizar UI
            self._cargar_imagenes()

        except Exception as e:
            print(f"Error al cargar imagen: {e}")

    def _borrar_imagen(self, nombre, row):
        if nombre in self.galeria:
            path = self.galeria[nombre]["path"]
            if os.path.exists(path):
                os.remove(path)
            del self.galeria[nombre]
            guardar_galeria(self.galeria)
            row.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()