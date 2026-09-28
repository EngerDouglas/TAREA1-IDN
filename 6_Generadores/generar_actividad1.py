"""Genera el PDF de la Actividad 1 (exploración de la fuente de datos) de la Práctica 1 de ICC-321.

Uso:  python3 generar_actividad1.py
Salida: Practica1_Actividad1_Exploracion.pdf
"""
import html, os, re, subprocess, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

UNIVERSIDAD = "Pontificia Universidad Católica Madre y Maestra"
ESCUELA = "Escuela de Ingeniería en Computación y Telecomunicaciones"
ASIGNATURA = "ICC-321 Inteligencia de Negocios"
PRACTICA = "Práctica 1: Diseño e implementación de una solución de Inteligencia de Negocios"
ENTREGA = "Actividad 1 — Exploración de la fuente de datos"
INTEGRANTES = [("Elías De La Cruz Jiménez", "10155971"), ("Enger Douglas", "10144675")]
PROFESORA = "Lisibonny Beato"
FECHA = "26 de septiembre de 2026"

BLOQUES = []


def h2(t): BLOQUES.append(("h2", t))
def h3(t): BLOQUES.append(("h3", t))
def p(t): BLOQUES.append(("p", t))
def li(items): BLOQUES.append(("li", items))
def tabla(headers, filas, anchos, aligns=None): BLOQUES.append(("tabla", headers, filas, anchos, aligns or [None] * len(headers)))
def nota(t): BLOQUES.append(("nota", t))
def svg(t): BLOQUES.append(("svg", t))
def salto(): BLOQUES.append(("salto",))


# =====================================================================================
# 1. ALCANCE Y MÉTODO
# =====================================================================================
h2("1. Alcance y método de la exploración")
p("Este documento corresponde a la **actividad 1 de la Práctica 1**: la exploración de la base de datos "
  "operacional que servirá de fuente para la solución de Inteligencia de Negocios. El objetivo es "
  "comprender las entidades y relaciones disponibles, la granularidad de cada tabla, las variables "
  "aprovechables para el análisis, los problemas de calidad presentes y las posibilidades analíticas "
  "que ofrece la fuente.")
p("La base **BI_Practica_Retail** se creó ejecutando el script entregado con la práctica sobre **SQL "
  "Server 2022**. Todas las cifras de este documento provienen de consultas ejecutadas directamente "
  "sobre esa base; ninguna es estimada.")
nota("**Observación sobre el script.** El script original no se ejecuta tal cual: utiliza el alias de "
     "columna `LineNo` en el bloque que genera los detalles de orden, y `LINENO` es palabra reservada de "
     "Transact-SQL, por lo que el motor devuelve el error «Incorrect syntax near the keyword LineNo». "
     "Se renombró ese alias a `LineaNo` (9 ocurrencias) y con ese cambio el script corre completo.")

# =====================================================================================
# 2. ENTIDADES
# =====================================================================================
h2("2. Principales entidades y relaciones")
p("La fuente contiene **10 tablas** en el esquema `dbo`, con 9 claves foráneas declaradas. Se distinguen "
  "dos grupos: las tablas de **catálogo** (describen el negocio y cambian poco) y las tablas "
  "**transaccionales** (registran los hechos y crecen con la operación).")
tabla(["Tabla", "Tipo", "Filas", "Contenido"], [
    ["Categoria", "Catálogo", "10", "Categorías comerciales de producto."],
    ["Proveedor", "Catálogo", "24", "Proveedores, con país y fecha de alta."],
    ["Producto", "Catálogo", "250", "SKU, nombre, marca, costo unitario, precio de lista y estado (activo o no)."],
    ["Tienda", "Catálogo", "12", "Sucursales, con ciudad, provincia, tipo y fecha de apertura."],
    ["Cliente", "Catálogo", "2 500", "Datos demográficos, ubicación, segmento y fecha de registro."],
    ["Promocion", "Catálogo", "15", "Campañas con vigencia, porcentaje de descuento y canal."],
    ["OrdenVenta", "Transaccional", "30 000", "Cabecera de la venta: fecha y hora, tienda, cliente, canal, estado y promoción."],
    ["DetalleOrden", "Transaccional", "76 784", "Línea de la venta: producto, cantidad, precio unitario y descuento."],
    ["Pago", "Transaccional", "28 803", "Pago de la orden: fecha, método y monto."],
    ["Devolucion", "Transaccional", "5 139", "Devolución de una línea: fecha, cantidad devuelta, motivo y reembolso."],
], [17, 14, 10, 59], [None, None, "right", None])

p("El diagrama siguiente resume las relaciones declaradas en la base:")
svg("""
<svg viewBox="0 0 1000 505" class="diagrama">
  <defs>
    <marker id="flecha" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#5a6b85"/>
    </marker>
  </defs>
  <g font-family="Arial" font-size="15">
    <!-- catálogos izquierda -->
    <rect x="20" y="40" width="185" height="42" rx="6" class="cat"/>
    <text x="112" y="66" text-anchor="middle" fill="#1c2430">Cliente (2 500)</text>
    <rect x="20" y="115" width="185" height="42" rx="6" class="cat"/>
    <text x="112" y="141" text-anchor="middle" fill="#1c2430">Tienda (12)</text>
    <rect x="20" y="190" width="185" height="42" rx="6" class="cat"/>
    <text x="112" y="216" text-anchor="middle" fill="#1c2430">Promocion (15)</text>
    <!-- transaccionales centro -->
    <rect x="355" y="110" width="230" height="52" rx="6" class="tx"/>
    <text x="470" y="134" text-anchor="middle" font-weight="bold" fill="#ffffff">OrdenVenta</text>
    <text x="470" y="152" text-anchor="middle" font-size="13" fill="#ffffff">30 000 órdenes</text>
    <rect x="355" y="290" width="230" height="52" rx="6" class="tx"/>
    <text x="470" y="314" text-anchor="middle" font-weight="bold" fill="#ffffff">DetalleOrden</text>
    <text x="470" y="332" text-anchor="middle" font-size="13" fill="#ffffff">76 784 líneas</text>
    <rect x="355" y="440" width="230" height="52" rx="6" class="tx2"/>
    <text x="470" y="464" text-anchor="middle" font-weight="bold" fill="#ffffff">Devolucion</text>
    <text x="470" y="482" text-anchor="middle" font-size="13" fill="#ffffff">5 139 devoluciones</text>
    <rect x="720" y="110" width="230" height="52" rx="6" class="tx2"/>
    <text x="835" y="134" text-anchor="middle" font-weight="bold" fill="#ffffff">Pago</text>
    <text x="835" y="152" text-anchor="middle" font-size="13" fill="#ffffff">28 803 pagos</text>
    <!-- catálogos derecha -->
    <rect x="750" y="290" width="200" height="42" rx="6" class="cat"/>
    <text x="850" y="316" text-anchor="middle" fill="#1c2430">Producto (250)</text>
    <rect x="750" y="370" width="200" height="42" rx="6" class="cat"/>
    <text x="850" y="396" text-anchor="middle" fill="#1c2430">Categoria (10)</text>
    <rect x="750" y="440" width="200" height="42" rx="6" class="cat"/>
    <text x="850" y="466" text-anchor="middle" fill="#1c2430">Proveedor (24)</text>
    <!-- relaciones -->
    <g stroke="#5a6b85" stroke-width="1.6" fill="none" marker-end="url(#flecha)">
      <path d="M205,61 L280,61 L280,126 L350,126"/>
      <path d="M205,136 L350,136"/>
      <path d="M205,211 L280,211 L280,148 L350,148"/>
      <path d="M470,162 L470,285"/>
      <path d="M470,342 L470,435"/>
      <path d="M585,136 L715,136"/>
      <path d="M745,311 L590,311"/>
      <path d="M850,370 L850,337"/>
      <path d="M850,440 L850,415"/>
    </g>
    <g font-size="12" fill="#5a6b85">
      <text x="240" y="55">1:N</text>
      <text x="262" y="130">1:N</text>
      <text x="240" y="205">1:N</text>
      <text x="480" y="228">1:N</text>
      <text x="480" y="395">1:N</text>
      <text x="640" y="128">1:1</text>
      <text x="660" y="304">1:N</text>
    </g>
  </g>
</svg>
""")
li([
    "Una **orden** pertenece a una tienda, opcionalmente a un cliente y opcionalmente a una promoción.",
    "Una **orden** tiene entre 1 y 4 líneas de detalle, y cada línea apunta a un producto.",
    "Un **producto** pertenece a una categoría y a un proveedor.",
    "Un **pago** corresponde a una orden completa; una **devolución**, a una línea de detalle.",
])

# =====================================================================================
# 3. GRANULARIDAD
# =====================================================================================
h2("3. Naturaleza y granularidad de los datos")
p("Identificar el grano de cada tabla es el paso decisivo de esta exploración, porque de él depende el "
  "diseño del modelo dimensional. Los conteos confirman lo siguiente:")
tabla(["Tabla", "Grano (una fila representa…)", "Comprobación realizada"], [
    ["OrdenVenta", "una venta registrada, con fecha y hora", "30 000 filas, 30 000 OrdenID distintos"],
    ["DetalleOrden", "un producto dentro de una orden", "76 784 filas sobre 30 000 órdenes: 2,56 líneas por orden en promedio"],
    ["Pago", "el pago de una orden completa", "28 803 pagos para 28 803 órdenes distintas: **un pago por orden**"],
    ["Devolucion", "la devolución de una línea de detalle", "5 139 filas con 5 139 DetalleOrdenID distintos"],
    ["Cliente / Producto / Tienda / Promocion / Categoria / Proveedor", "una entidad del catálogo", "Clave primaria simple de tipo IDENTITY en todas"],
], [21, 30, 49])

p("Distribución de líneas por orden:")
tabla(["Líneas en la orden", "1", "2", "3", "4"],
      [["Órdenes", "6 099", "8 009", "8 901", "6 991"]], [24, 19, 19, 19, 19],
      [None, "right", "right", "right", "right"])

nota("**Implicación para el modelo dimensional.** `Pago` y `Devolucion` **no están al mismo grano** que "
     "`DetalleOrden`. Incorporar el método o el monto de pago en un hecho de ventas a nivel de línea "
     "duplicaría los montos tantas veces como líneas tenga la orden. El pago debe tratarse a nivel de "
     "orden y las devoluciones como un hecho aparte, a nivel de línea.")

# =====================================================================================
# 4. VARIABLES
# =====================================================================================
h2("4. Variables disponibles para el análisis")
p("Las columnas de la fuente se clasifican según el papel que pueden cumplir en el modelo dimensional:")
tabla(["Papel", "Variables"], [
    ["Métricas (hechos)", "Cantidad, PrecioUnitario y DescuentoMonto en DetalleOrden; CostoUnitario y PrecioLista en Producto; Monto en Pago; CantidadDevuelta y MontoReembolso en Devolucion."],
    ["Atributos de tiempo", "FechaOrden (con hora), FechaPago, FechaDevolucion, FechaRegistro del cliente, FechaApertura de la tienda, FechaLanzamiento del producto, vigencia de las promociones."],
    ["Atributos de producto", "SKU, NombreProducto, Marca (12 marcas), Categoria (10 categorías), Proveedor (24) y País del proveedor, Activo."],
    ["Atributos de cliente", "Sexo, FechaNacimiento, Ciudad, Provincia (8), Segmento (Regular, Preferente, Corporativo)."],
    ["Atributos de tienda", "NombreTienda, Ciudad, Provincia, TipoTienda (Calle, Centro comercial, Express, Outlet)."],
    ["Atributos de la venta", "CanalVenta (Tienda, Web, App), EstadoOrden, MetodoPago, PromocionID y porcentaje de descuento, Motivo de devolución."],
], [22, 78])

p("Algunas distribuciones relevantes observadas:")
tabla(["Variable", "Distribución observada"], [
    ["CanalVenta", "Tienda 15 223 órdenes (50,7 %) · Web 8 252 (27,5 %) · App 6 525 (21,8 %)"],
    ["EstadoOrden", "Completada 28 803 (96,01 %) · Cancelada 1 197 (3,99 %)"],
    ["Segmento de cliente", "Regular 1 553 · Preferente 643 · Corporativo 304"],
    ["TipoTienda", "Calle 4 · Centro comercial 4 · Express 3 · Outlet 1"],
    ["MetodoPago", "Los cinco métodos se reparten de forma casi uniforme (entre 5 755 y 5 766 pagos cada uno)"],
    ["Promoción", "Solo 5 966 órdenes (19,9 %) se asocian a una promoción; los descuentos van de 10 % a 20 %"],
    ["Cobertura temporal", "Del 1 de enero de 2023 al 15 de agosto de 2026, con órdenes en las 24 horas del día"],
], [22, 78])

# =====================================================================================
# 5. CALIDAD
# =====================================================================================
h2("5. Problemas de calidad de datos detectados")
p("La exploración identificó seis situaciones que deben resolverse en el proceso ETL antes de cargar el "
  "Data Warehouse. La columna «magnitud» indica el volumen real medido en la base.")
tabla(["#", "Hallazgo", "Magnitud", "Tratamiento propuesto en el ETL"], [
    ["1", "Órdenes sin cliente identificado (ClienteID nulo)", "2 407 órdenes (8,02 %)", "No se pueden descartar: son ventas reales. Se asignan a un miembro «No identificado» en la dimensión Cliente."],
    ["2", "Clientes sin sexo registrado", "254 de 2 500 (10,2 %)", "Sustituir el nulo por la categoría «No especificado», para no perder al cliente en los análisis demográficos."],
    ["3", "Órdenes canceladas con líneas de detalle", "1 197 órdenes · 3 117 líneas · RD$ 12,1 millones", "Excluirlas del hecho de ventas. Si se incluyen, inflan los ingresos casi un 4 %."],
    ["4", "Órdenes sin promoción asociada", "24 034 órdenes (80,1 %)", "Es un nulo legítimo. Se resuelve con un miembro «Sin promoción» en la dimensión Promoción."],
    ["5", "Líneas que venden productos marcados como inactivos", "3 123 líneas sobre 10 productos inactivos", "Conservarlas: son ventas históricas válidas. El atributo Activo se guarda en la dimensión Producto."],
    ["6", "Ventas y devoluciones en tablas de distinto grano", "28 803 pagos (grano orden) frente a 76 784 líneas", "Separar los hechos por grano, según lo indicado en la sección 3."],
], [5, 26, 20, 49], ["center", None, None, None])

p("También se verificaron condiciones que **no** presentan problemas, lo que simplifica el ETL:")
li([
    "No hay devoluciones con cantidad mayor a la vendida, ni anteriores a la fecha de la orden, ni asociadas a órdenes canceladas.",
    "No hay pagos de órdenes canceladas; el monto de cada pago coincide exactamente con el neto de su orden en las 28 803 órdenes pagadas.",
    "No hay productos con precio de lista inferior al costo, ni claves foráneas huérfanas.",
])

# =====================================================================================
# 6. POSIBILIDADES
# =====================================================================================
h2("6. Posibilidades de análisis que ofrece la fuente")
p("Con las variables disponibles, la fuente permite responder preguntas de negocio en cinco frentes. "
  "Los valores siguientes, calculados sobre las órdenes completadas, muestran que los datos tienen "
  "suficiente variabilidad para sostener el análisis:")
tabla(["Indicador (órdenes completadas, 2023–2026)", "Valor"], [
    ["Unidades vendidas", "210 229"],
    ["Venta bruta", "RD$ 298 749 966"],
    ["Descuentos otorgados", "RD$ 9 758 409"],
    ["Venta neta", "RD$ 288 991 558"],
    ["Costo de la mercancía vendida", "RD$ 213 382 973"],
    ["Margen bruto", "RD$ 75 608 585 (26,2 %)"],
], [70, 30], [None, "right"])

h3("Frentes de análisis identificados")
tabla(["Frente", "Preguntas que la fuente permite responder"], [
    ["Rentabilidad", "¿Qué categorías, marcas o proveedores aportan más margen y no solo más ingresos? Papelería es la categoría de mayor venta neta (RD$ 38,7 millones) pero su margen es el más bajo del grupo líder (23,3 %), mientras Cuidado personal rinde 27,9 %."],
    ["Devoluciones", "¿Qué productos y categorías concentran las devoluciones? La tasa media es de 6,7 % de todas las líneas del detalle (incluidas las de órdenes canceladas), pero **Moda llega a 13,4 %** y Electrodomésticos a 9,6 %. Los motivos se reparten de forma pareja entre cinco causas."],
    ["Canal y tienda", "¿Cómo se comparan tienda física, Web y App en ticket promedio y margen? ¿Qué tipo de tienda rinde mejor por sucursal?"],
    ["Promociones", "¿Las órdenes con promoción generan más volumen del que sacrifican en descuento? Solo una de cada cinco órdenes usa promoción, lo que permite comparar contra un grupo de control amplio."],
    ["Cliente", "¿Cómo se comportan los segmentos Regular, Preferente y Corporativo? ¿Qué provincias concentran la venta? Debe considerarse que el 8 % de las ventas no tiene cliente asociado."],
], [17, 83])

# =====================================================================================
# 7. CONCLUSIONES
# =====================================================================================
h2("7. Conclusiones de la exploración")
li([
    "La fuente es adecuada para una solución de BI: cubre **44 meses** de operación, 30 000 órdenes y 76 784 líneas, con dimensiones suficientes (producto, cliente, tienda, promoción, canal y tiempo).",
    "El proceso de negocio natural para el modelo es la **venta al detalle**, y el grano candidato es la **línea de detalle de una orden completada**, que es el nivel más fino disponible y permite agregar hacia arriba sin pérdida.",
    "Las devoluciones justifican una **segunda tabla de hechos** al mismo grano de línea, en lugar de forzarse dentro del hecho de ventas.",
    "El pago debe analizarse a nivel de orden; llevarlo a la línea rompería la aditividad de los montos.",
    "Los seis problemas de calidad detectados son tratables en el ETL y ninguno obliga a descartar datos, salvo las órdenes canceladas, que deben excluirse del hecho de ventas.",
])
p("Con estos elementos queda preparada la **actividad 2** (definición del problema de toma de decisiones) "
  "y la **actividad 3** (diseño del modelo dimensional).")


# =====================================================================================
# RENDERIZADO
# =====================================================================================
CSS = """
@page { size: Letter; margin: 20mm 18mm 16mm 18mm;
        @bottom-center { content: counter(page); font: 9pt Arial, sans-serif; color: #7a8394; } }
@page :first { @bottom-center { content: none; } }
* { box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1c2430; margin: 0; }

.portada { height: 240mm; display: flex; flex-direction: column; text-align: center; break-after: page; }
.portada .univ { font-family: Georgia, serif; font-size: 13pt; margin-top: 18mm; line-height: 1.6; }
.portada .escuela, .portada .asignatura { font-size: 11pt; color: #44506a; }
.portada .bloque { margin-top: 42mm; }
.portada h1 { font-family: Georgia, serif; font-size: 25pt; line-height: 1.25; margin: 0 auto 10px; max-width: 150mm; color: #14243d; }
.portada .entrega { font-size: 14pt; color: #1f4e79; margin-bottom: 6px; }
.portada .linea { width: 70px; height: 3px; background: #1f4e79; margin: 16px auto 0; }
.portada .datos { margin-top: auto; margin-bottom: 14mm; font-size: 11.5pt; line-height: 2; }
.portada .datos b { color: #14243d; }

h2 { font-family: Georgia, serif; font-size: 15pt; color: #14243d; margin: 22px 0 8px; break-after: avoid;
     border-bottom: 1.5px solid #1f4e79; padding-bottom: 5px; }
h3 { font-size: 11.5pt; color: #1f4e79; margin: 16px 0 6px; break-after: avoid; }
p { margin: 0 0 9px; text-align: justify; }
ul { margin: 0 0 10px; padding-left: 20px; }
li { margin-bottom: 4px; text-align: justify; }

table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 9.2pt; break-inside: avoid; }
th { background: #14243d; color: #fff; text-align: left; padding: 6px 8px; font-weight: 600; }
td { border: 1px solid #ccd3de; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #f5f7fa; }

.nota { background: #fff8e6; border-left: 4px solid #d99a00; padding: 10px 14px; margin: 6px 0 14px;
        font-size: 9.8pt; break-inside: avoid; }
.diagrama { width: 88%; display: block; height: auto; margin: 6px auto 14px; break-inside: avoid; }
.diagrama .cat { fill: #eef2f8; stroke: #7d8ca5; stroke-width: 1.5; }
.diagrama .tx { fill: #14243d; stroke: #14243d; }
.diagrama .tx2 { fill: #1f4e79; stroke: #1f4e79; }
"""


def esc(t):
    return html.escape(t)


def fmt(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def render_html():
    o = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>",
         esc("Práctica 1 — Actividad 1"), "</title><style>", CSS, "</style></head><body>"]
    o.append(
        "<div class='portada'><div class='univ'>%s<div class='escuela'>%s</div>"
        "<div class='asignatura'>%s</div></div>"
        "<div class='bloque'><div class='entrega'>%s</div><h1>%s</h1><div class='linea'></div></div>"
        "<div class='datos'><div><b>Integrantes:</b></div>%s"
        "<div><b>Profesora:</b> %s</div><div><b>Fecha:</b> %s</div></div></div>"
        % (esc(UNIVERSIDAD), esc(ESCUELA), esc(ASIGNATURA), esc(ENTREGA), esc(PRACTICA),
           "".join("<div>%s (ID %s)</div>" % (esc(n), esc(i)) for n, i in INTEGRANTES), esc(PROFESORA), esc(FECHA)))

    for b in BLOQUES:
        k = b[0]
        if k == "h2":
            o.append("<h2>%s</h2>" % esc(b[1]))
        elif k == "h3":
            o.append("<h3>%s</h3>" % esc(b[1]))
        elif k == "p":
            o.append("<p>%s</p>" % fmt(b[1]))
        elif k == "li":
            o.append("<ul>%s</ul>" % "".join("<li>%s</li>" % fmt(i) for i in b[1]))
        elif k == "nota":
            o.append("<div class='nota'>%s</div>" % fmt(b[1]))
        elif k == "svg":
            o.append(b[1])
        elif k == "salto":
            o.append("<div style='break-after:page'></div>")
        elif k == "tabla":
            _, hd, filas, anchos, aligns = b
            cols = "".join("<col style='width:%s%%'>" % w for w in anchos)
            th = "".join("<th%s>%s</th>" % (" style='text-align:%s'" % a if a else "", esc(h)) for h, a in zip(hd, aligns))
            trs = "".join("<tr>%s</tr>" % "".join(
                "<td%s>%s</td>" % (" style='text-align:%s'" % a if a else "", fmt(c)) for c, a in zip(f, aligns))
                for f in filas)
            o.append("<table><colgroup>%s</colgroup><tr>%s</tr>%s</table>" % (cols, th, trs))

    o.append("</body></html>")
    return "".join(o)


if __name__ == "__main__":
    pdf = os.path.join(TAREA, "3_Informes", "Practica1_Actividad1_Exploracion.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        h = os.path.join(tmp, "doc.html")
        with open(h, "w", encoding="utf-8") as f:
            f.write(render_html())
        import shutil
        navegador = CHROME if os.path.exists(CHROME) else (os.environ.get("CHROME") or shutil.which("chromium"))
        subprocess.run([navegador, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--allow-file-access-from-files", "--print-to-pdf=" + pdf, "file://" + h],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("PDF:", pdf)
