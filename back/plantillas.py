from back.empresa import get_contexto_empresa


def _ctx(sesion):
    return get_contexto_empresa(sesion)


def prompt_factura(cliente: str, items: str, condicion_pago: str, sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    return f"""{ctx}Generá una factura de venta en formato Excel profesional con los siguientes datos:

Cliente: {cliente}
Productos/servicios: {items}
Condición de pago: {condicion_pago}

La factura debe incluir las columnas: Codigo, Descripcion, Cantidad, Precio Unitario, Subtotal, IVA (21%), Total.
Debe tener una fila de totales al final con suma de Subtotal, suma de IVA y Total general.
El estilo debe ser formal y profesional, con colores sobrios (azul oscuro o gris en encabezados).
Incluir columnas de fecha de emision y numero de factura."""


def prompt_productos(categoria: str, cantidad: int, sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    return f"""{ctx}Generá una planilla de productos en Excel para la categoria: {categoria}.

Debe incluir aproximadamente {cantidad} productos con las columnas:
Codigo de Producto, Nombre, Descripcion detallada, Categoria, Precio Unitario, Stock disponible, Proveedor.

Los productos deben ser realistas y variados dentro de la categoria.
Usar colores acordes al rubro en los encabezados.
El stock debe ser un numero realista (entre 5 y 500 unidades)."""


def prompt_proveedores(rubro: str, sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    return f"""{ctx}Generá una planilla de proveedores en Excel para el rubro: {rubro}.

Debe incluir al menos 8 proveedores con las columnas:
Nombre del Proveedor, CUIT, Contacto (nombre de la persona), Telefono, Email,
Productos que provee, Condiciones de pago, Tiempo de entrega (dias).

Los proveedores deben ser ficticios pero realistas para Argentina.
Usar un estilo formal con colores verdes o azules en encabezados."""


def prompt_clientes(sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    empresa_rubro = ""
    if sesion and sesion.get("empresa", {}).get("rubro"):
        empresa_rubro = f" (empresa del rubro {sesion['empresa']['rubro']})"

    return f"""{ctx}Generá una base de datos de clientes en Excel para una empresa{empresa_rubro}.

Debe incluir al menos 12 clientes con las columnas:
Codigo de Cliente, Nombre y Apellido, DNI/CUIT, Telefono, Email,
Direccion, Ciudad, Fecha de alta como cliente, Categoria (mayorista/minorista/particular).

Los clientes deben ser ficticios pero con datos argentinos realistas.
Incluir variedad de ciudades (Buenos Aires, Cordoba, Rosario, Mendoza, etc).
Usar estilo formal con colores en encabezados."""


def prompt_ventas(periodo: str, sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    return f"""{ctx}Generá una planilla de registro de ventas en Excel para el periodo: {periodo}.

Debe incluir al menos 15 registros de ventas con las columnas:
Fecha, Numero de Factura, Cliente, Productos vendidos, Cantidad, Precio Unitario,
Subtotal, IVA (21%), Total, Vendedor, Forma de pago.

Al final debe tener una fila de totales con la suma de ventas del periodo.
Incluir variedad de clientes y productos.
Agregar un grafico de barras mostrando ventas por fecha si es posible.
Usar colores dinamicos y profesionales en encabezados."""


def prompt_informe_word(tema: str, secciones_extra: str = "", sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    extra = f"\nSecciones adicionales requeridas: {secciones_extra}" if secciones_extra else ""
    return f"""{ctx}Generá un informe Word completo y profesional sobre el siguiente tema: {tema}.

El informe debe incluir las siguientes secciones:
- Introduccion (contexto y objetivos del informe)
- Desarrollo (analisis detallado del tema con datos y argumentos)
- Conclusion (resumen y recomendaciones){extra}

Cada seccion debe tener contenido extenso y relevante (minimo 3 parrafos cada una).
El contenido debe ser especifico, informativo y profesional.
Usar subsecciones donde sea necesario para organizar mejor la informacion."""


def prompt_catalogo_word(tipo_productos: str, sesion: dict = None) -> str:
    ctx = _ctx(sesion)
    return f"""{ctx}Generá un catalogo de productos en Word para: {tipo_productos}.

Debe incluir al menos 10 productos con:
- Nombre del producto
- Descripcion detallada (caracteristicas, usos, ventajas)
- Palabras clave destacadas en la descripcion

El catalogo debe estar bien organizado y ser atractivo para presentar a clientes.
Las descripciones deben ser convincentes y comerciales."""
