"""Genera el PDF de las actividades 2 y 3 de la Práctica 1 de ICC-321:
definición del problema de toma de decisiones y diseño del modelo dimensional.

Uso:  python3 generar_actividad2y3.py
Salida: Practica1_Actividad2y3_Modelo.pdf
"""
import html, os, re, subprocess, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

UNIVERSIDAD = "Pontificia Universidad Católica Madre y Maestra"
ESCUELA = "Escuela de Ingeniería en Computación y Telecomunicaciones"
ASIGNATURA = "ICC-321 Inteligencia de Negocios"
PRACTICA = "Práctica 1: Diseño e implementación de una solución de Inteligencia de Negocios"
ENTREGA = "Actividades 2 y 3 — Problema de decisión y modelo dimensional"
ESTUDIANTE = "Enger Douglas"
MATRICULA = "10144675"
PROFESORA = "Lisibonny Beato"
FECHA = "27 de septiembre de 2026"

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
# ACTIVIDAD 2
# =====================================================================================
h2("1. Situación detectada en los datos")
p("La exploración de la actividad 1 mostró un negocio estable en ingresos —entre RD$ 77 y 82 millones "
  "anuales— con un margen bruto que se mantiene en **26,1 %** año tras año. Sin embargo, al abrir esa "
  "cifra por categoría, por promoción y por devoluciones aparecen tres desequilibrios que el negocio "
  "no puede ver con sus reportes operacionales:")
tabla(["Hallazgo", "Evidencia medida sobre la base"], [
    ["Las promociones sacrifican margen sin generar volumen",
     "Las órdenes con promoción rinden **17,09 % de margen** frente a **28,13 %** sin promoción. El ticket promedio con promoción es **menor** (RD$ 8 965 contra RD$ 10 299) y las unidades por línea son idénticas en ambos grupos (2,85)."],
    ["La categoría que más vende no es la que más aporta",
     "Papelería lidera en venta neta (RD$ 38,7 millones) pero tiene el **margen más bajo: 23,28 %**. Cuidado personal, con RD$ 29,2 millones, rinde **27,95 %**."],
    ["Las devoluciones se concentran en pocas categorías",
     "Moda devuelve el **13,99 %** de sus líneas y Electrodomésticos el **10,00 %**, frente a un promedio general de 6,7 %. En total se reembolsaron **RD$ 13,2 millones**, equivalentes al 17 % del margen bruto del período."],
], [30, 70])

h2("2. Problema de toma de decisiones")
p("**Problema identificado.** La empresa gestiona su desempeño comercial con información de ingresos, "
  "pero no puede medir la **rentabilidad real** de sus categorías y productos, porque los descuentos "
  "promocionales y las devoluciones se registran en procesos separados del registro de ventas. En "
  "consecuencia, se promocionan categorías cuyo margen no resiste el descuento y se mantienen productos "
  "con tasas de devolución altas sin cuantificar su costo.")
p("**Necesidad de información.** Disponer de una vista integrada que permita seguir, sobre la misma base, "
  "la venta, el descuento aplicado, el costo, el margen resultante y el reembolso por devoluciones, con "
  "capacidad de desagregar por categoría, producto, promoción, canal, tienda, cliente y tiempo.")

h3("2.1 Usuario de la solución")
tabla(["Usuario", "Uso previsto"], [
    ["**Gerente comercial / de categorías** (usuario principal)", "Decide el surtido, la política de precios y qué categorías entran en promoción."],
    ["Gerente de mercadeo", "Evalúa el retorno de cada campaña promocional."],
    ["Gerencia de tiendas y canales", "Compara desempeño entre sucursales y entre canal físico y digital."],
    ["Gerencia general", "Sigue el margen consolidado y su evolución."],
], [32, 68])

h3("2.2 Decisiones que se pretende apoyar")
li([
    "Qué categorías, marcas y productos deben entrar o salir de las campañas promocionales.",
    "Qué nivel de descuento es sostenible para cada categoría sin destruir el margen.",
    "Sobre qué productos actuar para reducir devoluciones (revisión con el proveedor, ficha de producto, control de calidad).",
    "Qué proveedores conviene renegociar, según el margen y las devoluciones que generan.",
    "Cómo asignar el esfuerzo comercial entre tiendas y canales de venta.",
])

h3("2.3 Preguntas de análisis")
p("La solución deberá responder las siguientes preguntas, que son las que guían el diseño del modelo:")
tabla(["#", "Pregunta de análisis"], [
    ["P1", "¿Qué categorías, marcas y productos aportan más **margen bruto**, y no solo más ingresos?"],
    ["P2", "¿Cuánto margen sacrifican las promociones y qué volumen adicional generan realmente?"],
    ["P3", "¿Qué productos y categorías concentran las **devoluciones** y cuánto cuestan en reembolsos?"],
    ["P4", "¿Cuál es el **margen neto de devoluciones** por categoría y por proveedor?"],
    ["P5", "¿Cómo evolucionan la venta y el margen mes a mes, y qué meses concentran la demanda?"],
    ["P6", "¿Qué canal de venta y qué tipo de tienda rinden mejor en ticket promedio y margen?"],
    ["P7", "¿Qué segmentos de cliente sostienen la venta y qué peso tienen las ventas sin cliente identificado?"],
    ["P8", "¿Qué proveedores concentran el margen y cuáles arrastran las devoluciones?"],
], [7, 93], ["center", None])

# =====================================================================================
# ACTIVIDAD 3
# =====================================================================================
h2("3. Diseño del modelo dimensional")
h3("3.1 Proceso de negocio y grano")
p("**Proceso de negocio:** la **venta al detalle** de productos en tiendas y canales digitales.")
p("**Grano de la tabla de hechos:** *una línea de detalle de una orden de venta completada*. Es decir, "
  "una fila por cada producto vendido dentro de una orden.")
p("Se eligió este grano porque es el **nivel más fino disponible** en la fuente y permite agregar hacia "
  "arriba (producto, categoría, orden, tienda, día, mes) sin pérdida de información. Las órdenes "
  "canceladas —1 197 órdenes y 3 117 líneas— quedan fuera del hecho, por no representar una venta "
  "efectiva.")

h3("3.2 Medidas")
tabla(["Medida", "Cómo se obtiene", "Aditividad"], [
    ["CantidadVendida", "DetalleOrden.Cantidad", "Aditiva"],
    ["MontoBruto", "Cantidad × PrecioUnitario", "Aditiva"],
    ["DescuentoMonto", "DetalleOrden.DescuentoMonto", "Aditiva"],
    ["MontoNeto", "MontoBruto − DescuentoMonto", "Aditiva"],
    ["CostoTotal", "Cantidad × Producto.CostoUnitario", "Aditiva"],
    ["MargenBruto", "MontoNeto − CostoTotal", "Aditiva"],
    ["PrecioUnitario", "DetalleOrden.PrecioUnitario", "**No aditiva**: se promedia, nunca se suma"],
    ["MargenPorcentual", "MargenBruto ÷ MontoNeto", "**No aditiva**: se calcula al nivel de agregación, no se almacena"],
], [20, 38, 42])
nota("**Sobre la aditividad.** Las seis primeras medidas pueden sumarse por cualquier dimensión, que es "
     "la condición que Kimball exige a un hecho bien diseñado. El precio unitario y el margen porcentual "
     "son razones: se guardan sus componentes (numerador y denominador) y el porcentaje se calcula en el "
     "dashboard, para evitar el error clásico de promediar porcentajes.")

h3("3.3 Dimensiones")
tabla(["Dimensión", "Atributos principales", "Observaciones de diseño"], [
    ["DimFecha", "FechaKey, Fecha, Año, Trimestre, Mes, NombreMes, Semana, DíaSemana, EsFinDeSemana", "Dimensión de tiempo obligatoria. Cubre del 1-1-2023 al 31-12-2026. Se usa con **doble rol**: fecha de venta y fecha de devolución."],
    ["DimProducto", "ProductoKey, SKU, NombreProducto, Marca, Categoría, Proveedor, PaísProveedor, Activo, RangoPrecio", "Se **desnormalizan** Categoría y Proveedor dentro de la dimensión, siguiendo el esquema estrella en lugar del copo de nieve."],
    ["DimCliente", "ClienteKey, Nombre, Sexo, GrupoEdad, Ciudad, Provincia, Segmento, AñoRegistro", "Incluye el miembro **«No identificado»** (clave −1) para las 2 407 órdenes sin cliente. El sexo nulo se carga como «No especificado»."],
    ["DimTienda", "TiendaKey, NombreTienda, Ciudad, Provincia, TipoTienda, AñoApertura", "12 sucursales, con el tipo de tienda como atributo de análisis."],
    ["DimPromocion", "PromocionKey, NombrePromoción, PorcentajeDto, CanalPromoción, Vigencia", "Incluye el miembro **«Sin promoción»** (clave −1) para las 24 034 órdenes sin campaña."],
    ["DimCanal", "CanalKey, CanalVenta", "Tienda, Web y App. Se separa como dimensión propia por ser eje directo de la pregunta P6."],
    ["DimMotivoDevolucion", "MotivoKey, Motivo", "Cinco motivos. Aplica al hecho de devoluciones."],
    ["DimMetodoPago", "MetodoPagoKey, MetodoPago", "Cinco métodos. Aplica al hecho de pagos, que va a grano de orden."],
], [17, 38, 45])

h3("3.4 Esquema estrella")
svg("""
<svg viewBox="0 0 1000 470" class="diagrama">
  <g font-family="Arial" font-size="14">
    <rect x="370" y="175" width="260" height="120" rx="8" class="tx"/>
    <text x="500" y="203" text-anchor="middle" font-weight="bold" fill="#ffffff" font-size="16">FactVentas</text>
    <text x="500" y="224" text-anchor="middle" fill="#ffffff" font-size="12.5">grano: línea de orden completada</text>
    <text x="500" y="246" text-anchor="middle" fill="#ffffff" font-size="12.5">CantidadVendida · MontoBruto</text>
    <text x="500" y="264" text-anchor="middle" fill="#ffffff" font-size="12.5">DescuentoMonto · MontoNeto</text>
    <text x="500" y="282" text-anchor="middle" fill="#ffffff" font-size="12.5">CostoTotal · MargenBruto</text>

    <rect x="60" y="30" width="200" height="46" rx="6" class="cat"/>
    <text x="160" y="58" text-anchor="middle" fill="#1c2430">DimFecha</text>
    <rect x="60" y="205" width="200" height="46" rx="6" class="cat"/>
    <text x="160" y="233" text-anchor="middle" fill="#1c2430">DimProducto</text>
    <rect x="60" y="380" width="200" height="46" rx="6" class="cat"/>
    <text x="160" y="408" text-anchor="middle" fill="#1c2430">DimCliente</text>
    <rect x="740" y="30" width="200" height="46" rx="6" class="cat"/>
    <text x="840" y="58" text-anchor="middle" fill="#1c2430">DimTienda</text>
    <rect x="740" y="205" width="200" height="46" rx="6" class="cat"/>
    <text x="840" y="233" text-anchor="middle" fill="#1c2430">DimPromocion</text>
    <rect x="740" y="380" width="200" height="46" rx="6" class="cat"/>
    <text x="840" y="408" text-anchor="middle" fill="#1c2430">DimCanal</text>

    <g stroke="#5a6b85" stroke-width="1.6" fill="none">
      <path d="M260,53 L370,190"/>
      <path d="M260,228 L370,228"/>
      <path d="M260,403 L370,280"/>
      <path d="M740,53 L630,190"/>
      <path d="M740,228 L630,228"/>
      <path d="M740,403 L630,280"/>
    </g>
    <text x="500" y="330" text-anchor="middle" font-size="12.5" fill="#5a6b85">Dimensión degenerada dentro del hecho: OrdenID</text>
  </g>
</svg>
""")
p("El modelo se completa con dos hechos adicionales, que **no pueden integrarse en FactVentas porque "
  "están a otro grano**, según se comprobó en la actividad 1:")
tabla(["Hecho", "Grano", "Medidas", "Dimensiones"], [
    ["FactVentas", "Línea de orden completada", "CantidadVendida, MontoBruto, DescuentoMonto, MontoNeto, CostoTotal, MargenBruto", "Fecha, Producto, Cliente, Tienda, Promoción, Canal"],
    ["FactDevoluciones", "Devolución de una línea", "CantidadDevuelta, MontoReembolso", "Fecha, Producto, Cliente, Tienda, MotivoDevolución"],
    ["FactPagos", "Pago de una orden", "MontoPagado", "Fecha, Cliente, Tienda, Canal, MétodoPago"],
], [17, 22, 34, 27])

h3("3.5 Matriz de bus")
p("La matriz muestra qué dimensiones comparte cada proceso; las dimensiones compartidas son las que "
  "permiten analizar los tres hechos con los mismos filtros (dimensiones conformadas).")
tabla(["Proceso", "Fecha", "Producto", "Cliente", "Tienda", "Promoción", "Canal", "Motivo", "Método pago"], [
    ["FactVentas", "X", "X", "X", "X", "X", "X", "—", "—"],
    ["FactDevoluciones", "X", "X", "X", "X", "—", "—", "X", "—"],
    ["FactPagos", "X", "—", "X", "X", "X", "X", "—", "X"],
], [22, 9, 11, 10, 9, 12, 9, 9, 12],
   [None, "center", "center", "center", "center", "center", "center", "center", "center"])

h3("3.6 Claves y relaciones")
li([
    "Cada dimensión usa una **clave subrogada** entera, propia del Data Warehouse. En esta implementación se asigna a partir del identificador del origen, y la clave natural se conserva además como atributo para poder rastrear la procedencia de cada fila.",
    "Las tablas de hechos guardan únicamente **claves foráneas a las dimensiones y las medidas**, más la dimensión degenerada `OrdenID`, que identifica la orden sin necesidad de una tabla aparte.",
    "Las dimensiones Cliente y Promoción incluyen miembros especiales con clave **−1** («No identificado» y «Sin promoción») para representar los nulos del origen, de modo que ninguna fila de hechos quede sin relación.",
    "DimFecha usa como clave un entero con formato **AAAAMMDD**, práctica habitual en Kimball porque hace legible la clave y facilita las particiones.",
    "Todas las relaciones son de **uno a muchos** desde la dimensión hacia el hecho.",
])

h3("3.7 Trazabilidad: preguntas, medidas y dimensiones")
tabla(["Pregunta", "Medidas que la responden", "Dimensiones de análisis"], [
    ["P1", "MargenBruto, MontoNeto, MargenPorcentual", "Producto (categoría, marca), Fecha"],
    ["P2", "MontoNeto, DescuentoMonto, MargenBruto, CantidadVendida", "Promoción, Producto, Fecha"],
    ["P3", "CantidadDevuelta, MontoReembolso", "Producto, MotivoDevolución, Fecha"],
    ["P4", "MargenBruto − MontoReembolso", "Producto (categoría, proveedor)"],
    ["P5", "MontoNeto, MargenBruto", "Fecha (año, trimestre, mes)"],
    ["P6", "MontoNeto, MargenBruto, ticket = MontoNeto ÷ órdenes distintas", "Canal, Tienda (tipo de tienda)"],
    ["P7", "MontoNeto, CantidadVendida", "Cliente (segmento, provincia, «No identificado»)"],
    ["P8", "MargenBruto, MontoReembolso", "Producto (proveedor, país del proveedor)"],
], [10, 45, 45], ["center", None, None])

h2("4. Reglas de carga que se derivan del modelo")
p("El diseño anterior determina las transformaciones que deberá ejecutar el proceso ETL de la actividad 5:")
tabla(["#", "Regla", "Motivo"], [
    ["1", "Cargar en FactVentas solo las órdenes con EstadoOrden = «Completada»", "El grano define la venta efectiva; las canceladas inflarían los ingresos en RD$ 12,1 millones."],
    ["2", "Calcular MontoBruto, MontoNeto, CostoTotal y MargenBruto durante el ETL", "Son medidas derivadas; se precalculan para que el dashboard solo agregue."],
    ["3", "Traer CostoUnitario desde Producto al momento de la carga", "El costo vive en el catálogo, no en la línea de venta."],
    ["4", "Sustituir ClienteID nulo por la clave −1 («No identificado»)", "Mantiene las 2 407 órdenes anónimas dentro del análisis."],
    ["5", "Sustituir PromocionID nulo por la clave −1 («Sin promoción»)", "Permite comparar con promoción contra sin promoción (pregunta P2)."],
    ["6", "Sustituir Sexo nulo por «No especificado»", "Evita perder 254 clientes en los cortes demográficos."],
    ["7", "Generar DimFecha de forma independiente, con todos los días del período", "Una dimensión de tiempo no se deriva de los hechos: se construye completa."],
    ["8", "No incorporar el monto ni el método de pago en FactVentas", "Están a grano de orden; se cargan en FactPagos."],
], [5, 40, 55], ["center", None, None])

p("Con el modelo definido queda habilitada la **actividad 4** (implementación del Data Warehouse en SQL "
  "Server), cuyo script (`DW_Retail.sql`) se entrega junto con este documento y fue ejecutado con éxito sobre SQL Server: crea las 8 dimensiones, los 3 hechos, sus claves foráneas e índices, y carga la dimensión de tiempo con los 1 461 días del período.")


# =====================================================================================
# RENDERIZADO (motor compartido con el documento de la actividad 1)
# =====================================================================================
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_motor.py")).read())
