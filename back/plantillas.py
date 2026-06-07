from back.empresa import get_contexto_empresa


def _ctx(sesion):
    return get_contexto_empresa(sesion)


def _datos_provistos(datos: dict) -> str:
    lineas = []
    for k, v in datos.items():
        if v and str(v).strip():
            lineas.append(f'- {k}: "{v}"')
        else:
            lineas.append(f'- {k}: (NO PROVISTO)')
    return "\n".join(lineas)


def _items_provistos(items: list, campos: list) -> str:
    if not items:
        return "(El usuario no agregó items.)"
    lineas = []
    for i, it in enumerate(items, 1):
        lineas.append(f"Item {i}:")
        for key, label in campos:
            v = it.get(key, "")
            lineas.append(f'  - {label}: "{v or "(NO PROVISTO)"}"')
    return "\n".join(lineas)


def _linea(datos: dict) -> str:
    if datos.get("valor"):
        return f'- {datos["clave"]}: "{datos["valor"]}"'
    return f'- {datos["clave"]}: (NO PROVISTO)'


def _secciones_texto(secciones: list[str]) -> str:
    if not secciones:
        return "(El usuario no especificó secciones.)"
    return "\n".join(f"- {s}" for s in secciones)


def _construir_indice(secciones: list[str]) -> list[dict]:
    return [{"titulo": s, "nivel": 1} for s in secciones]


def prompt_factura(cliente: str = "", items: str = "", condicion_pago: str = "",
                   sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    datos = _datos_provistos({
        "Cliente": cliente,
        "Items (productos/servicios con cantidades y precios si los tiene)": items,
        "Condición de pago": condicion_pago,
        "Anotación adicional": nota,
    })
    return f"""{ctx}Generá una factura de venta en formato Excel profesional.

DATOS PROVISTOS POR EL USUARIO:
{datos}

REGLAS:
- Para cada columna que se corresponda con un dato NO PROVISTO, dejá la celda VACÍA ("" para texto, 0 para numéricos). NO inventes valores para completar la planilla.
- Si el usuario proveyó "items" con cantidades y precios explícitos, usalos. Si NO los proveyó, dejá Cantidad, Precio Unitario, Subtotal, IVA y Total en 0/vacío.
- Si la búsqueda web proveyó datos del cliente o productos, usá esos solo donde corresponda. No inventes CUITs, direcciones ni teléfonos.
- Si la anotación incluye instrucciones o datos específicos (ej: "el cliente es X", "sumar 10% de descuento"), aplicalas.
- El "Codigo" puede ser vacío si no fue provisto.

La planilla debe incluir las columnas: Codigo, Descripcion, Cantidad, Precio Unitario, Subtotal, IVA (21%), Total.
Debe tener una fila de totales al final con suma de Subtotal, suma de IVA y Total general.
El estilo debe ser formal y profesional, con colores sobrios (azul oscuro o gris en encabezados).
Incluir columnas de fecha de emision y numero de factura."""


def prompt_productos(productos: list = None, categoria: str = "",
                     sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    campos = [
        ("nombre", "Nombre"),
        ("descripcion", "Descripción"),
        ("precio", "Precio Unitario"),
        ("stock", "Stock disponible"),
    ]
    productos_texto = _items_provistos(productos or [], campos)
    nota_line = _linea({"clave": "Anotación adicional", "valor": nota})
    categoria_line = _linea({"clave": "Categoría (aplica a todos)", "valor": categoria})

    return f"""{ctx}Generá una planilla de productos en Excel.

DATOS PROVISTOS POR EL USUARIO:
{categoria_line}
{nota_line}

PRODUCTOS:
{productos_texto}

REGLAS:
- Generá UNA fila por cada producto provisto.
- Si el usuario no agregó productos, devolvé la planilla con UNA sola fila con placeholders ("—"). NO inventes nombres de productos.
- "Categoria" se aplica a todas las filas (salvo que la anotación indique lo contrario).
- En "Nombre" usá EXACTAMENTE lo provisto por el usuario. Si no fue provisto, dejá VACÍO.
- En "Descripcion detallada": si el usuario proveyó una descripción, usala tal cual. Si NO la proveyó pero hay datos verificados de la web (sección "Verified real data" / "Real data found"), usá esa información para escribir una descripción verificada. Si NO hay ninguna fuente disponible, dejá VACÍO. NO inventes descripciones genéricas ni de conocimiento general sin fuente.
- En "Precio Unitario" usá EXACTAMENTE el valor numérico provisto por el usuario (tal cual, sin redondear). Si NO fue provisto, dejá 0. NUNCA inventes precios ni uses valores estimados de la web.
- En "Stock disponible" usá EXACTAMENTE el valor numérico provisto por el usuario. Si NO fue provisto, dejá VACÍO. NUNCA inventes stock.
- NO incluyas la columna "Codigo de Producto" salvo que el usuario la haya mencionado explícitamente en la anotación.
- Si la anotación incluye instrucciones específicas (ej: "solo marcas X", "buscar descripciones en la web", "incluir columna extra Y"), aplicalas.

Columnas requeridas (en este orden, sin Codigo de Producto): Nombre, Descripcion detallada, Categoria, Precio Unitario, Stock disponible.
Usar colores acordes al rubro en los encabezados."""


def prompt_proveedores(proveedores: list = None, sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    campos = [
        ("nombre", "Nombre del Proveedor"),
        ("cuit", "CUIT"),
        ("contacto", "Contacto (persona)"),
        ("telefono", "Teléfono"),
        ("email", "Email"),
        ("productos", "Productos que provee"),
        ("condiciones", "Condiciones de pago"),
        ("tiempo", "Tiempo de entrega"),
    ]
    proveedores_texto = _items_provistos(proveedores or [], campos)
    nota_line = _linea({"clave": "Anotación adicional", "valor": nota})

    return f"""{ctx}Generá una planilla de proveedores en Excel.

PROVEEDORES PROVISTOS POR EL USUARIO:
{proveedores_texto}
{nota_line}

REGLAS:
- Generá UNA fila por cada proveedor provisto.
- Si el usuario no agregó proveedores, devolvé la planilla con UNA sola fila con placeholders ("—"). NO inventes nombres de proveedores.
- NUNCA inventes CUITs, teléfonos, emails, ni nombres de empresas reales. Si el usuario no los proveyó, dejá VACÍOS.
- En "Productos que provee", "Condiciones de pago" y "Tiempo de entrega" SÍ podés usar conocimiento del rubro o datos verificados de la búsqueda web.
- Si la búsqueda web proveyó datos reales de proveedores del rubro, usá esos. Si no, dejá los identificadores vacíos y completá solo las columnas descriptivas.
- Si la anotación incluye instrucciones o datos específicos, aplicalas.

Columnas: Nombre del Proveedor, CUIT, Contacto (nombre de la persona), Telefono, Email, Productos que provee, Condiciones de pago, Tiempo de entrega (dias).
Usar un estilo formal con colores verdes o azules en encabezados."""


def prompt_clientes(clientes: list = None, sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    campos = [
        ("nombre", "Nombre"),
        ("direccion", "Dirección"),
        ("dni", "DNI/CUIT"),
        ("telefono", "Teléfono"),
        ("email", "Email"),
        ("ciudad", "Ciudad"),
        ("categoria", "Categoría"),
        ("contenido", "Contenido"),
    ]
    clientes_texto = _items_provistos(clientes or [], campos)
    nota_line = _linea({"clave": "Anotación adicional", "valor": nota})

    return f"""{ctx}Generá una base de datos de clientes en Excel.

CLIENTES PROVISTOS POR EL USUARIO:
{clientes_texto}
{nota_line}

REGLAS:
- Generá UNA fila por cada cliente provisto.
- Si el usuario no agregó clientes, devolvé la planilla con UNA sola fila con placeholders ("—"). NO inventes nombres.
- NUNCA inventes DNIs, CUITs, teléfonos, emails, ni datos identificables. Si el usuario no los proveyó, dejá VACÍOS.
- "Ciudad" puede completarse con conocimiento general si hay info del cliente. Si no, dejá vacío.
- "Categoria (mayorista/minorista/particular)" usá lo provisto por el usuario. Si no, dejá vacío.
- "Contenido" va tal cual lo proveyó el usuario (ej: qué compra, intereses, notas internas).
- Si la anotación incluye instrucciones o datos específicos, aplicalas.

Columnas: Codigo de Cliente, Nombre y Apellido, DNI/CUIT, Telefono, Email, Direccion, Ciudad, Fecha de alta como cliente, Categoria (mayorista/minorista/particular), Contenido.
Usar estilo formal con colores en encabezados."""


def prompt_ventas(ventas: list = None, periodo: str = "",
                  sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    campos = [
        ("cliente", "Cliente"),
        ("producto", "Producto vendido"),
        ("vendedor", "Vendedor"),
        ("cantidad", "Cantidad"),
        ("precio", "Precio Unitario"),
        ("fecha", "Fecha (DD/MM/YYYY)"),
    ]
    ventas_texto = _items_provistos(ventas or [], campos)
    nota_line = _linea({"clave": "Anotación adicional", "valor": nota})
    periodo_line = _linea({"clave": "Período", "valor": periodo})

    return f"""{ctx}Generá una planilla de registro de ventas en Excel.

DATOS PROVISTOS POR EL USUARIO:
{periodo_line}

VENTAS:
{ventas_texto}
{nota_line}

REGLAS:
- Generá UNA fila por cada venta provista.
- "Fecha": usá la fecha provista por el usuario (formato DD/MM/YYYY). Si NO la proveyó, distribuila dentro del Período indicado.
- "Numero de Factura": autogenérelos secuencialmente como F-001, F-002, etc. (o vacío).
- "Forma de pago": autogenérelos con valores genéricos como "Efectivo", "Transferencia", "Tarjeta".
- NUNCA inventes nombres reales de clientes. Si el usuario no los proveyó, dejá VACÍOS.
- "Productos vendidos" y "Vendedor" pueden completarse con conocimiento general si el usuario no los proveyó.
- Los precios unitarios, subtotales, IVA y totales deben ser 0 si no los proveyó (la planilla los calcula automáticamente).
- Si la anotación incluye instrucciones específicas, aplicalas.

Columnas: Fecha, Numero de Factura, Cliente, Productos vendidos, Cantidad, Precio Unitario, Subtotal, IVA (21%), Total, Vendedor, Forma de pago.
Al final debe tener una fila de totales con la suma de ventas del periodo.
Agregar un grafico de barras mostrando ventas por fecha si es posible.
Usar colores dinamicos y profesionales en encabezados."""


def prompt_informe_word(tema: str = "", secciones: list[str] = None,
                        sesion: dict = None, nota: str = "") -> tuple:
    ctx = _ctx(sesion)
    if not secciones:
        secciones = ["Introducción", "Desarrollo", "Conclusión"]
    sec_texto = _secciones_texto(secciones)
    indice = _construir_indice(secciones)
    datos = _datos_provistos({
        "Tema del informe": tema,
        "Secciones": " | ".join(secciones),
        "Anotación adicional": nota,
    })
    prompt = f"""{ctx}Generá un informe Word completo y profesional.

DATOS PROVISTOS POR EL USUARIO:
{datos}

SECCIONES REQUERIDAS POR EL USUARIO (en este orden):
{sec_texto}

REGLAS:
- NUNCA inventes datos personales o de contacto (nombres de personas, DNIs, teléfonos, emails, direcciones). Si el usuario no los proveyó, no los menciones o usá placeholders como "—".
- SÍ podés generar descripciones, análisis, procesos, metodologías y contenido de conocimiento general sobre el tema.
- Si la anotación incluye instrucciones o datos específicos (ej: "la empresa se llama X", "incluir análisis FODA"), aplicalas.
- Si el contexto de empresa del usuario aporta datos, usalo como fuente de verdad para esa empresa.
- Generá EXACTAMENTE las secciones listadas arriba, en el orden indicado. NO agregues secciones adicionales.
- Cada sección debe tener contenido extenso y relevante (mínimo 3 párrafos cada una).
- Usá subsecciones donde sea necesario para organizar mejor la información.

El contenido debe ser específico, informativo y profesional."""
    return prompt, indice


def prompt_catalogo_word(productos: list = None, sesion: dict = None, nota: str = "") -> str:
    ctx = _ctx(sesion)
    campos = [
        ("nombre", "Nombre del producto"),
        ("descripcion", "Descripción detallada"),
        ("palabras", "Palabras clave"),
    ]
    productos_texto = _items_provistos(productos or [], campos)
    nota_line = _linea({"clave": "Anotación adicional", "valor": nota})

    return f"""{ctx}Generá un catalogo de productos en Word.

PRODUCTOS PROVISTOS POR EL USUARIO:
{productos_texto}
{nota_line}

REGLAS:
- Generá UNA sección por cada producto provisto por el usuario.
- Si el usuario NO agregó ningún producto, es OBLIGATORIO hacer búsqueda web y completar con 10 productos REALES con descripciones verificadas.
- En "Descripcion detallada" SÍ podés usar conocimiento general o datos verificados de la búsqueda web.
- En "Nombre del producto" usá lo provisto. Si no hay datos, usá productos de búsqueda web.
- "Palabras clave" usá lo provisto o inferí de la descripción.
- Si la anotación incluye instrucciones específicas (ej: "solo productos importados", "rango de precios"), aplicalas.

Para cada producto:
- Nombre del producto
- Descripcion detallada (caracteristicas, usos, ventajas)
- Palabras clave destacadas en la descripcion

El catalogo debe estar bien organizado y ser atractivo para presentar a clientes.
Las descripciones deben ser convincentes y comerciales."""
