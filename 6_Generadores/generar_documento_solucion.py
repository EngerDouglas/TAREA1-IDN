"""Genera el documento de la solución de la Práctica 1 de ICC-321 (entregable 1).

Reúne en un solo PDF las actividades 1 a 7: fuente de datos, problema de decisión,
modelo dimensional, Data Warehouse, ETL, análisis de las medidas y dashboard, más la
justificación de las decisiones de diseño.

Uso:  python3 generar_documento_solucion.py
Salida: 3_Informes/Practica1_Documento_Solucion.pdf
"""
import html, os, re, subprocess, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CAPTURAS = os.path.join(TAREA, "7_Dashboard", "capturas")
SALIDA_PDF = "Practica1_Documento_Solucion.pdf"
# En un documento largo las tablas pueden partirse entre páginas; las filas no.
CSS_EXTRA = "table { break-inside: auto; } tr { break-inside: avoid; }"

UNIVERSIDAD = "Pontificia Universidad Católica Madre y Maestra"
ESCUELA = "Escuela de Ingeniería en Computación y Telecomunicaciones"
ASIGNATURA = "ICC-321 Inteligencia de Negocios"
PRACTICA = "Práctica 1: Diseño e implementación de una solución de Inteligencia de Negocios"
ENTREGA = "Documento de la solución"
INTEGRANTES = [("Elías De La Cruz Jiménez", "10155971"), ("Enger Douglas", "10144675")]
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
def img(archivo, pie): BLOQUES.append(("img", os.path.join(CAPTURAS, archivo), pie))
def salto(): BLOQUES.append(("salto",))


# =====================================================================================
# 1. FUENTE DE DATOS
# =====================================================================================
h2("1. Descripción general de la fuente de datos")
p("La fuente es la base operacional **BI_Practica_Retail**, creada con el script entregado con la práctica "
  "sobre **SQL Server 2022**. Registra la operación de una cadena de venta al detalle con 12 sucursales y "
  "canales digitales entre el 1 de enero de 2023 y el 15 de agosto de 2026. Todas las cifras de este "
  "documento provienen de consultas ejecutadas sobre esa base o sobre el Data Warehouse construido a partir "
  "de ella; ninguna es estimada.")
nota("**Observación sobre el script.** El script original no se ejecuta tal cual: utiliza el alias de "
     "columna `LineNo` en el bloque que genera los detalles de orden, y `LINENO` es palabra reservada de "
     "Transact-SQL, por lo que el motor devuelve el error «Incorrect syntax near the keyword LineNo». "
     "Se renombró ese alias a `LineaNo` (9 ocurrencias) en `Retail_Operacional_fix.sql` y con ese cambio "
     "el script corre completo.")

h3("1.1 Entidades y relaciones")
p("La fuente contiene **10 tablas** en el esquema `dbo`, con 9 claves foráneas declaradas. Seis son de "
  "**catálogo** (describen el negocio y cambian poco) y cuatro son **transaccionales** (registran los "
  "hechos y crecen con la operación).")
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
li([
    "Una **orden** pertenece a una tienda, opcionalmente a un cliente y opcionalmente a una promoción.",
    "Una **orden** tiene entre 1 y 4 líneas de detalle, y cada línea apunta a un producto.",
    "Un **producto** pertenece a una categoría y a un proveedor.",
    "Un **pago** corresponde a una orden completa; una **devolución**, a una línea de detalle.",
])

h3("1.2 Granularidad")
tabla(["Tabla", "Grano (una fila representa…)", "Comprobación realizada"], [
    ["OrdenVenta", "una venta registrada, con fecha y hora", "30 000 filas, 30 000 OrdenID distintos"],
    ["DetalleOrden", "un producto dentro de una orden", "76 784 filas sobre 30 000 órdenes: 2,56 líneas por orden en promedio"],
    ["Pago", "el pago de una orden completa", "28 803 pagos para 28 803 órdenes distintas: **un pago por orden**"],
    ["Devolucion", "la devolución de una línea de detalle", "5 139 filas con 5 139 DetalleOrdenID distintos"],
], [21, 30, 49])
p("`Pago` y `Devolucion` **no están al mismo grano** que `DetalleOrden`. Llevar el monto del pago a la "
  "línea lo repetiría tantas veces como líneas tenga la orden; por eso el modelo separa los hechos por grano.")

h3("1.3 Problemas de calidad de datos")
tabla(["#", "Hallazgo", "Magnitud", "Tratamiento en el ETL"], [
    ["1", "Órdenes sin cliente identificado (ClienteID nulo)", "2 407 órdenes (8,02 %)", "Se asignan al miembro «No identificado» (clave −1) de la dimensión Cliente."],
    ["2", "Clientes sin sexo registrado", "254 de 2 500 (10,2 %)", "El nulo se sustituye por «No especificado»."],
    ["3", "Órdenes canceladas con líneas de detalle", "1 197 órdenes, 3 117 líneas, RD$ 12,1 millones", "Se excluyen del hecho de ventas; incluirlas inflaría los ingresos casi un 4 %."],
    ["4", "Órdenes sin promoción asociada", "24 034 órdenes (80,1 %)", "Nulo legítimo: se asignan al miembro «Sin promoción» (clave −1)."],
    ["5", "Líneas que venden productos marcados como inactivos", "3 123 líneas sobre 10 productos", "Se conservan: son ventas históricas válidas. El atributo Activo queda en DimProducto."],
    ["6", "Pagos y devoluciones a distinto grano que la línea", "28 803 pagos frente a 76 784 líneas", "Se cargan en hechos separados (FactPagos y FactDevoluciones)."],
], [5, 28, 22, 45], ["center", None, None, None])
p("También se verificó que no hay devoluciones mayores a la cantidad vendida ni asociadas a órdenes "
  "canceladas, que no hay pagos de órdenes canceladas, que el monto de cada pago coincide con el neto de su "
  "orden y que no existen claves foráneas huérfanas.")

# =====================================================================================
# 2. PROBLEMA DE DECISIÓN
# =====================================================================================
h2("2. Problema de toma de decisiones")
p("La exploración mostró un negocio estable en ingresos (entre RD$ 77 y 82 millones anuales) con un margen "
  "bruto que se mantiene cerca de **26,2 %** año tras año. Al abrir esa cifra por categoría, por promoción y "
  "por devoluciones aparecen tres desequilibrios que los reportes operacionales no muestran:")
tabla(["Hallazgo", "Evidencia medida sobre la base"], [
    ["Las promociones sacrifican margen sin generar volumen",
     "Las órdenes con promoción rinden **17,09 % de margen** frente a **28,13 %** sin promoción. El ticket promedio con promoción es **menor** (RD$ 8 965 contra RD$ 10 299) y las unidades por orden son prácticamente iguales (7,29 contra 7,30)."],
    ["La categoría que más vende no es la que más aporta",
     "Papelería lidera en venta neta (RD$ 38,7 millones) pero tiene el **margen más bajo: 23,3 %**. Cuidado personal, con RD$ 29,2 millones, rinde **27,9 %**."],
    ["Las devoluciones se concentran en pocas categorías",
     "Moda devuelve el **14,0 %** de sus líneas y Electrodomésticos el **10,0 %**, frente a un promedio de 7,0 % sobre las líneas vendidas. En total se reembolsaron **RD$ 13,2 millones**, el 17,4 % del margen bruto del período."],
], [30, 70])
p("**Problema identificado.** La empresa gestiona su desempeño comercial con información de ingresos, pero "
  "no puede medir la **rentabilidad real** de sus categorías y productos, porque los descuentos "
  "promocionales y las devoluciones se registran en procesos separados del registro de ventas. En "
  "consecuencia, se promocionan categorías cuyo margen no resiste el descuento y se mantienen productos con "
  "tasas de devolución altas sin cuantificar su costo.")
p("**Necesidad de información.** Una vista integrada que permita seguir, sobre la misma base, la venta, el "
  "descuento aplicado, el costo, el margen resultante y el reembolso por devoluciones, con capacidad de "
  "desagregar por categoría, producto, promoción, canal, tienda, cliente y tiempo.")

h3("2.1 Usuario de la solución")
tabla(["Usuario", "Uso previsto"], [
    ["**Gerente comercial o de categorías** (usuario principal)", "Decide el surtido, la política de precios y qué categorías entran en promoción."],
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
# 3. MODELO DIMENSIONAL
# =====================================================================================
h2("3. Modelo dimensional")
h3("3.1 Proceso de negocio y grano")
p("**Proceso de negocio:** la **venta al detalle** de productos en tiendas y canales digitales.")
p("**Grano de la tabla de hechos principal:** **una línea de detalle de una orden de venta completada**, es "
  "decir, una fila por cada producto vendido dentro de una orden. Es el **nivel más fino disponible** en la "
  "fuente y permite agregar hacia arriba (producto, categoría, orden, tienda, día, mes) sin pérdida de "
  "información. Las órdenes canceladas (1 197 órdenes y 3 117 líneas) quedan fuera, porque no representan "
  "una venta efectiva.")

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

h3("3.3 Dimensiones")
tabla(["Dimensión", "Atributos principales", "Observaciones de diseño"], [
    ["DimFecha", "FechaKey, Fecha, Año, Trimestre, Mes, NombreMes, Semana, DíaSemana, EsFinDeSemana", "Dimensión de tiempo del 1-1-2023 al 31-12-2026. Se usa con **doble rol**: fecha de venta y fecha de devolución."],
    ["DimProducto", "ProductoKey, SKU, NombreProducto, Marca, Categoría, Proveedor, PaísProveedor, Activo, RangoPrecio", "Categoría y Proveedor se **desnormalizan** dentro de la dimensión, siguiendo el esquema estrella en lugar del copo de nieve."],
    ["DimCliente", "ClienteKey, Nombre, Sexo, GrupoEdad, Ciudad, Provincia, Segmento, AñoRegistro", "Incluye el miembro **«No identificado»** (clave −1). El sexo nulo se carga como «No especificado»."],
    ["DimTienda", "TiendaKey, NombreTienda, Ciudad, Provincia, TipoTienda, AñoApertura", "12 sucursales, con el tipo de tienda como atributo de análisis."],
    ["DimPromocion", "PromocionKey, NombrePromoción, PorcentajeDto, CanalPromoción, Vigencia", "Incluye el miembro **«Sin promoción»** (clave −1)."],
    ["DimCanal", "CanalKey, CanalVenta", "Tienda, Web y App. Dimensión propia por ser eje directo de la pregunta P6."],
    ["DimMotivoDevolucion", "MotivoKey, Motivo", "Cinco motivos. Aplica al hecho de devoluciones."],
    ["DimMetodoPago", "MetodoPagoKey, MetodoPago", "Cinco métodos. Aplica al hecho de pagos."],
], [17, 38, 45])

h3("3.4 Esquema estrella")
svg("""
<svg viewBox="0 0 1000 470" class="diagrama">
  <g font-family="Arial" font-size="14">
    <rect x="370" y="175" width="260" height="120" rx="8" class="tx"/>
    <text x="500" y="203" text-anchor="middle" font-weight="bold" fill="#ffffff" font-size="16">FactVentas</text>
    <text x="500" y="224" text-anchor="middle" fill="#ffffff" font-size="12.5">grano: línea de orden completada</text>
    <text x="500" y="246" text-anchor="middle" fill="#ffffff" font-size="12.5">CantidadVendida, MontoBruto</text>
    <text x="500" y="264" text-anchor="middle" fill="#ffffff" font-size="12.5">DescuentoMonto, MontoNeto</text>
    <text x="500" y="282" text-anchor="middle" fill="#ffffff" font-size="12.5">CostoTotal, MargenBruto</text>
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
p("El modelo se completa con dos hechos que **no pueden integrarse en FactVentas porque están a otro grano**:")
tabla(["Hecho", "Grano", "Medidas", "Dimensiones"], [
    ["FactVentas", "Línea de orden completada", "CantidadVendida, MontoBruto, DescuentoMonto, MontoNeto, CostoTotal, MargenBruto", "Fecha, Producto, Cliente, Tienda, Promoción, Canal"],
    ["FactDevoluciones", "Devolución de una línea", "CantidadDevuelta, MontoReembolso", "Fecha, Producto, Cliente, Tienda, MotivoDevolución"],
    ["FactPagos", "Pago de una orden", "MontoPagado", "Fecha, Cliente, Tienda, Canal, MétodoPago"],
], [17, 22, 34, 27])

h3("3.5 Matriz de bus")
p("Las dimensiones compartidas son las que permiten analizar los tres hechos con los mismos filtros "
  "(dimensiones conformadas).")
tabla(["Proceso", "Fecha", "Producto", "Cliente", "Tienda", "Promoción", "Canal", "Motivo", "Método pago"], [
    ["FactVentas", "X", "X", "X", "X", "X", "X", "", ""],
    ["FactDevoluciones", "X", "X", "X", "X", "", "", "X", ""],
    ["FactPagos", "X", "", "X", "X", "X", "X", "", "X"],
], [22, 9, 11, 10, 9, 12, 9, 9, 12],
   [None, "center", "center", "center", "center", "center", "center", "center", "center"])

h3("3.6 Claves y relaciones")
li([
    "Cada dimensión usa una **clave subrogada** entera, propia del Data Warehouse. En esta implementación se asigna a partir del identificador del origen, y la clave natural se conserva como atributo para rastrear la procedencia de cada fila.",
    "Las tablas de hechos guardan **claves foráneas a las dimensiones y las medidas**, más la dimensión degenerada `OrdenID`.",
    "Cliente y Promoción incluyen miembros especiales con clave **−1** para representar los nulos del origen, de modo que ninguna fila de hechos quede sin relación.",
    "DimFecha usa como clave un entero con formato **AAAAMMDD**, que hace legible la clave y facilita las particiones.",
    "Todas las relaciones son de **uno a muchos** desde la dimensión hacia el hecho.",
])

h3("3.7 Trazabilidad entre preguntas, medidas y dimensiones")
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

# =====================================================================================
# 4. DATA WAREHOUSE
# =====================================================================================
h2("4. Implementación del Data Warehouse")
p("El modelo se implementó en SQL Server con el script `4_Data_Warehouse/DW_Retail.sql`, que crea la base "
  "**DW_Retail** desde cero. La carga posterior la hace `Cargar_DW.sql` con los archivos que produce el "
  "flujo de Tableau Prep.")
tabla(["Elemento", "Implementación"], [
    ["Dimensiones", "8 tablas (`DimFecha`, `DimProducto`, `DimCliente`, `DimTienda`, `DimPromocion`, `DimCanal`, `DimMotivoDevolucion`, `DimMetodoPago`), cada una con su clave subrogada entera como `PRIMARY KEY`."],
    ["Hechos", "`FactVentas`, `FactDevoluciones` y `FactPagos`, con clave propia `bigint` tomada del identificador de la línea, la devolución o el pago del origen."],
    ["Claves foráneas", "16 restricciones `FOREIGN KEY`: 6 en FactVentas, 5 en FactDevoluciones y 5 en FactPagos. Ningún hecho puede apuntar a un miembro inexistente."],
    ["Tipos de datos", "Montos en `decimal(14,2)` y precios en `decimal(12,2)` para no perder centavos; cantidades en `int`; fechas en `date`; indicadores en `bit`."],
    ["Restricciones", "Todas las columnas de hechos son `NOT NULL`; `CHECK (CantidadVendida > 0)` y `CHECK (CantidadDevuelta > 0)`."],
    ["Índices", "8 índices no agrupados sobre las claves foráneas más consultadas (fecha, producto, cliente, tienda y promoción)."],
    ["DimFecha", "Se genera en el propio script con los 1 461 días del 1-1-2023 al 31-12-2026, independiente de los hechos."],
    ["Miembros especiales", "El script inserta «No identificado» en DimCliente y «Sin promoción» en DimPromocion, ambos con clave −1, antes de cualquier carga."],
], [20, 80])
p("La carga se verificó contra el origen. Los conteos y los totales del Data Warehouse coinciden con los "
  "calculados directamente sobre las órdenes completadas de BI_Practica_Retail:")
tabla(["Tabla", "Filas cargadas", "Comprobación"], [
    ["FactVentas", "73 667", "76 784 líneas menos las 3 117 de órdenes canceladas"],
    ["FactDevoluciones", "5 139", "Todas las devoluciones del origen"],
    ["FactPagos", "28 803", "Un pago por cada orden completada"],
    ["DimCliente", "2 501", "2 500 clientes más el miembro «No identificado»"],
    ["DimPromocion", "16", "15 promociones más el miembro «Sin promoción»"],
    ["DimProducto, DimTienda", "250 y 12", "Iguales al catálogo de origen"],
    ["DimCanal, DimMotivoDevolucion, DimMetodoPago", "3, 5 y 5", "Valores distintos del origen"],
], [30, 18, 52], [None, "right", None])
nota("**Cuadre de la carga.** La venta neta de FactVentas suma **RD$ 288 991 557,74** y el monto de "
     "FactPagos suma exactamente lo mismo, lo que confirma que ninguna línea se duplicó ni se perdió al "
     "pasar de un grano a otro. El margen bruto cargado es RD$ 75 608 585,04 (26,16 %).")

# =====================================================================================
# 5. ETL
# =====================================================================================
h2("5. Proceso ETL en Tableau Prep")
p("El flujo `5_ETL/ETL_DW_Retail.tfl` tiene **40 nodos**: 10 entradas (una por tabla del origen), las "
  "uniones y pasos de limpieza, y 10 salidas, una por tabla del Data Warehouse. Cada salida se escribe como "
  "CSV en `5_ETL/CSV_salida` y `Cargar_DW.sql` la inserta en su tabla con el tipo de dato definitivo.")
tabla(["Paso del flujo", "Transformación", "Requerimiento del modelo que la justifica"], [
    ["Producto + Categoria + Proveedor", "Dos uniones internas por CategoriaID y ProveedorID; se renombran NombreCategoria, NombreProveedor y Pais.", "DimProducto desnormaliza categoría y proveedor para mantener el esquema estrella."],
    ["DimProducto", "Clave subrogada; atributo derivado RangoPrecio (Económico < RD$ 800, Medio < RD$ 1 500, Premium).", "Permite agrupar el margen por rango de precio sin consultar el precio de lista."],
    ["DimCliente", "Une nombre y apellido; `IFNULL(Sexo, \"No especificado\")`; deriva GrupoEdad y AñoRegistro.", "Regla de carga 6 y atributos de segmentación para P7."],
    ["DimTienda, DimPromocion", "Clave subrogada; año de apertura derivado de la fecha.", "Dimensiones de análisis de P2 y P6."],
    ["DimCanal, DimMotivoDevolucion, DimMetodoPago", "Agregación por valor distinto y asignación de clave fija a cada valor.", "El canal, el motivo y el método son texto libre en el origen; como dimensión se analizan con clave propia."],
    ["Filtrar órdenes completadas", "Filtro `EstadoOrden = \"Completada\"`; FechaKey AAAAMMDD; `IFNULL(ClienteID, -1)` e `IFNULL(PromocionID, -1)`; clave de canal.", "Grano del hecho y reglas de carga 1, 4 y 5."],
    ["Detalle + Orden + Producto", "Unión de cada línea con su orden y con el costo unitario del producto.", "El costo vive en el catálogo; se trae al momento de la carga (regla 3)."],
    ["FactVentas", "Cálculo de MontoBruto, MontoNeto, CostoTotal y MargenBruto redondeados a dos decimales.", "Medidas derivadas precalculadas para que el dashboard solo agregue (regla 2)."],
    ["FactDevoluciones", "Unión de la devolución con su línea vendida; FechaKey de la devolución; clave del motivo.", "Hecho aparte al grano de la devolución, con las mismas dimensiones conformadas."],
    ["FactPagos", "Unión del pago con su orden completada; FechaKey del pago; clave del método de pago.", "Hecho al grano de la orden, para no repetir el monto por línea (regla 8)."],
], [22, 42, 36])
p("Las salidas del flujo se compararon línea por línea con el origen: los 73 667 registros de FactVentas "
  "tienen la misma venta neta, el mismo cliente, la misma promoción y la misma fecha que su línea de origen, "
  "sin ninguna diferencia, y ningún registro quedó con clave 0 en canal, motivo o método de pago.")

# =====================================================================================
# 6. ANÁLISIS DE LAS MEDIDAS
# =====================================================================================
h2("6. Análisis de las medidas")
p("Cada medida se describe con lo que representa, cómo se obtiene, su relación con el grano, las "
  "dimensiones por las que se analiza, las preguntas que responde y la forma correcta de agregarla. Los "
  "totales corresponden a todo el período cargado en el Data Warehouse.")

h3("6.1 Medidas de FactVentas (grano: línea de orden completada)")
tabla(["Medida", "Qué representa y cómo se obtiene", "Total del período", "Agregación"], [
    ["CantidadVendida", "Unidades del producto vendidas en la línea. Se copia de `DetalleOrden.Cantidad`.", "210 229 unidades", "Aditiva por todas las dimensiones."],
    ["MontoBruto", "Valor de la línea antes del descuento: Cantidad × PrecioUnitario.", "RD$ 298 749 966,36", "Aditiva."],
    ["DescuentoMonto", "Descuento aplicado a la línea. Se copia de `DetalleOrden.DescuentoMonto`.", "RD$ 9 758 408,62", "Aditiva."],
    ["MontoNeto", "Ingreso efectivo de la línea: MontoBruto − DescuentoMonto.", "RD$ 288 991 557,74", "Aditiva. Es la base del margen porcentual y del ticket."],
    ["CostoTotal", "Costo de la mercancía vendida: Cantidad × `Producto.CostoUnitario`, traído en el ETL.", "RD$ 213 382 972,70", "Aditiva."],
    ["MargenBruto", "Ganancia de la línea antes de devoluciones: MontoNeto − CostoTotal.", "RD$ 75 608 585,04", "Aditiva. Se puede sumar por producto, tienda, mes o cualquier combinación."],
    ["PrecioUnitario", "Precio cobrado por unidad en la línea.", "Promedio simple RD$ 1 421,91", "**No aditiva**. Sumarla no tiene sentido; el precio medio correcto es SUM(MontoBruto) ÷ SUM(CantidadVendida) = RD$ 1 421,07."],
], [16, 40, 20, 24])
p("Las seis primeras medidas están **al mismo grano** que la línea: cada fila de FactVentas las aporta una "
  "sola vez, por lo que cualquier agregación hacia arriba (orden, producto, categoría, tienda, día, mes) es "
  "una suma directa. Se analizan por **las seis dimensiones del hecho**: Fecha, Producto (con su jerarquía "
  "Categoría y Proveedor), Cliente, Tienda, Promoción y Canal. Responden a P1, P2, P5, P6 y P7.")

h3("6.2 Medidas de FactDevoluciones (grano: devolución de una línea)")
tabla(["Medida", "Qué representa y cómo se obtiene", "Total del período", "Agregación"], [
    ["CantidadDevuelta", "Unidades devueltas en la devolución. Se copia de `Devolucion.CantidadDevuelta`.", "9 543 unidades", "Aditiva por Fecha, Producto, Cliente, Tienda y Motivo."],
    ["MontoReembolso", "Dinero devuelto al cliente. Se copia de `Devolucion.MontoReembolso`.", "RD$ 13 158 252,77", "Aditiva por las mismas dimensiones."],
], [18, 40, 18, 24])
p("La fecha de este hecho es la de la **devolución**, no la de la venta: DimFecha cumple aquí su segundo "
  "rol. Por eso las devoluciones llegan hasta el 3 de septiembre de 2026, aunque la última venta es del 15 "
  "de agosto. Estas medidas no se pueden cruzar con Promoción ni con Canal, porque FactDevoluciones no tiene "
  "esas dimensiones. Responden a P3, P4 y P8.")

h3("6.3 Medida de FactPagos (grano: pago de una orden)")
tabla(["Medida", "Qué representa y cómo se obtiene", "Total del período", "Agregación"], [
    ["MontoPagado", "Importe cobrado por la orden. Se copia de `Pago.Monto`.", "RD$ 288 991 557,74", "Aditiva por Fecha, Cliente, Tienda, Canal y MétodoPago. **No** se puede repartir por producto ni por categoría."],
], [18, 40, 18, 24])
p("MontoPagado vive a grano de orden porque así ocurre en el negocio: se paga la orden completa, no cada "
  "línea. Su total coincide con la venta neta de FactVentas, lo que sirve de control de la carga. Por el "
  "método de pago se reparte casi igual entre los cinco métodos (de RD$ 57,6 a 58,0 millones cada uno).")

h3("6.4 Indicadores derivados")
p("Los indicadores que son razones no se almacenan: se calculan en el dashboard a partir de sus "
  "componentes aditivos, al nivel de agregación que se esté mirando. Promediar porcentajes ya calculados "
  "daría resultados incorrectos cuando los grupos tienen tamaños distintos.")
tabla(["Indicador", "Fórmula en el dashboard", "Valor del período", "Pregunta"], [
    ["Margen %", "SUM(MargenBruto) ÷ SUM(MontoNeto)", "26,16 %", "P1, P2, P6, P8"],
    ["Órdenes", "COUNTD(OrdenID), sobre la dimensión degenerada", "28 803", "P6"],
    ["Ticket promedio", "SUM(MontoNeto) ÷ COUNTD(OrdenID)", "RD$ 10 033", "P2, P6"],
    ["Tasa de devolución", "Devoluciones ÷ líneas vendidas", "6,98 %", "P3, P8"],
    ["Margen después de devoluciones", "SUM(MargenBruto) − SUM(MontoReembolso)", "RD$ 62 450 332,27", "P4"],
    ["Margen que se va en reembolsos", "SUM(MontoReembolso) ÷ SUM(MargenBruto)", "17,40 %", "P4, P8"],
], [24, 38, 18, 20])
nota("**Restricción de agregación entre hechos.** El margen después de devoluciones combina dos hechos de "
     "distinto grano. No se obtiene uniendo FactVentas con FactDevoluciones fila a fila, porque cada línea "
     "con devolución se duplicaría. Se agrega cada hecho por separado al nivel común (año y producto) y luego "
     "se combinan los resultados por sus dimensiones conformadas; es la consulta entre hechos (drill-across) "
     "que usa el dashboard. Las órdenes se cuentan con COUNTD y nunca se suman entre grupos, porque una "
     "misma orden tiene varias líneas.")

# =====================================================================================
# 7. DASHBOARD
# =====================================================================================
h2("7. Dashboard interactivo")
p("El dashboard se construyó en **Tableau Desktop** (`7_Dashboard/Dashboard_Retail.twbx`). Su fuente es el "
  "Data Warehouse: las consultas de `7_Dashboard/Consultas_Dashboard.sql` leen únicamente las tablas de "
  "DW_Retail, unen cada hecho con sus dimensiones y guardan el resultado en un extracto de Tableau que va "
  "empaquetado dentro del libro. Así el libro se abre en cualquier equipo con Tableau sin necesitar el "
  "servidor, y ningún dato proviene de la base operacional.")
tabla(["Tabla del extracto", "Origen en DW_Retail", "Filas"], [
    ["Ventas", "FactVentas unido con DimFecha, DimProducto, DimCliente, DimTienda, DimPromocion y DimCanal, al mismo grano del hecho", "73 667"],
    ["RentabilidadProducto", "FactVentas y FactDevoluciones agregados por año y producto y unidos por esas dimensiones conformadas", "1 000"],
], [22, 64, 14], [None, None, "right"])
p("**Interacción.** Cada tablero tiene filtros de **Año**, **Categoría** y, en el primero, **Canal**. Son "
  "parámetros de Tableau aplicados como filtro de contexto en todas las hojas, de modo que un solo cambio "
  "recalcula todas las cifras, incluido el ranking de productos. Al pasar el cursor sobre cualquier marca se "
  "ve el detalle del valor.")

h3("7.1 Tablero 1: rentabilidad de la venta")
img("Tablero_1_Rentabilidad.png", "Figura 1. Tablero «Rentabilidad de la venta» en Tableau Desktop, sin filtros. Responde P1, P2, P5, P6 y P7.")
tabla(["Vista", "Pregunta", "Lo que muestra"], [
    ["Cifras de cabecera", "", "Venta neta RD$ 289,0 M, margen bruto RD$ 75,6 M, margen 26,2 %, 28 803 órdenes y ticket promedio de RD$ 10 033."],
    ["Venta neta por categoría y su margen", "P1", "Papelería es la categoría que más vende (RD$ 38,7 M) y la de menor margen (23,3 %). Cuidado personal (27,9 %) y Electrodomésticos (27,4 %) son las más rentables."],
    ["Margen % según la campaña", "P2", "El margen cae a medida que sube el descuento: San Valentín 20,4 %, Madres 18,9 %, Regreso a clases 15,9 % y Black Friday 11,0 %, frente a 28,1 % sin promoción. El ticket con promoción es menor (RD$ 8 965 contra RD$ 10 299), así que el descuento no compra volumen."],
    ["Venta neta por mes", "P5", "La venta mensual oscila entre RD$ 5,4 y 7,7 millones, con un promedio de RD$ 6,65 millones. Los picos son marzo de 2025 y julio de 2024 y 2025; no hay una temporada que concentre la demanda."],
    ["Ticket por canal y tipo de tienda", "P6", "El ticket se mueve entre RD$ 9 385 y RD$ 10 205 y el margen entre 25,8 % y 26,5 % en todas las combinaciones. La venta se concentra en tienda física de centro comercial."],
    ["Venta neta por segmento", "P7", "Regular sostiene el 56,3 % de la venta, Preferente el 24,3 % y Corporativo el 11,5 %. El 7,8 % no tiene cliente identificado."],
], [24, 10, 66], [None, "center", None])

h3("7.2 Tablero 2: devoluciones y proveedores")
img("Tablero_2_Devoluciones.png", "Figura 2. Tablero «Devoluciones y proveedores» en Tableau Desktop, sin filtros. Responde P3, P4 y P8.")
tabla(["Vista", "Pregunta", "Lo que muestra"], [
    ["Cifras de cabecera", "", "Reembolsos RD$ 13,2 M, tasa de devolución 7,0 %, margen bruto RD$ 75,6 M, margen después de devoluciones RD$ 62,5 M; el 17,4 % del margen se va en reembolsos."],
    ["Tasa de devolución por categoría", "P3", "Moda (14,0 %), Electrodomésticos (10,0 %) y Tecnología (9,3 %) duplican al resto, que está entre 4,7 % y 5,1 %."],
    ["Productos con más reembolsos", "P3", "Los diez productos con mayor monto reembolsado son de Moda, Electrodomésticos y Tecnología; el primero, Producto 188 de Moda, suma RD$ 232 410."],
    ["Margen después de devoluciones", "P4", "Moda pierde el 35,9 % de su margen en reembolsos, Electrodomésticos el 25,0 % y Tecnología el 24,6 %. Papelería, pese a su margen bajo, solo pierde el 14,5 %."],
    ["Proveedores: margen frente a devolución", "P8", "Proveedor 03 tiene uno de los márgenes más altos (29,7 %) pero la mayor tasa de devolución (11,2 %). Proveedor 13 tiene el margen más bajo (18,8 %). Proveedor 24 y Proveedor 01 combinan margen sobre 31 % con devoluciones bajas."],
], [24, 10, 66], [None, "center", None])
img("Tablero_2_Filtro_Moda.png", "Figura 3. El mismo tablero con el filtro Categoría = Moda: todas las vistas se recalculan y el ranking muestra los diez productos de Moda con más reembolsos.")

h3("7.3 Lectura para la toma de decisiones")
li([
    "**Promociones.** Black Friday, con 20 % de descuento, deja 11,0 % de margen y no aumenta el ticket. Conviene limitar el descuento profundo a categorías con margen alto y revisar su alcance.",
    "**Surtido y precio.** Papelería necesita revisión de precio o de costo con sus proveedores: es la mayor fuente de venta con el menor margen.",
    "**Devoluciones.** Moda, Electrodomésticos y Tecnología concentran la pérdida por reembolsos. Los diez productos del ranking son el punto de partida para revisar calidad y ficha de producto.",
    "**Proveedores.** Proveedor 03 debe renegociarse por devoluciones, no por margen; Proveedor 13, por margen.",
    "**Canales.** Canal y tipo de tienda no cambian la rentabilidad, así que no son la palanca principal del margen.",
])

# =====================================================================================
# 8. DECISIONES DE DISEÑO
# =====================================================================================
h2("8. Justificación de las principales decisiones de diseño")
tabla(["Decisión", "Alternativa descartada", "Motivo"], [
    ["Grano de FactVentas en la línea de orden completada", "Grano de orden", "Es el nivel más fino y permite analizar por producto y categoría; a nivel de orden se perdería el producto, eje de P1, P3 y P4."],
    ["Tres hechos separados por grano", "Un solo hecho con pagos y devoluciones", "El pago es por orden y la devolución por línea; mezclarlos duplicaría montos y rompería la aditividad."],
    ["Excluir las órdenes canceladas", "Cargarlas con un indicador de estado", "No son venta efectiva; incluirlas sumaría RD$ 12,1 millones que nunca se cobraron."],
    ["Miembros −1 en Cliente y Promoción", "Dejar la clave foránea en nulo", "Con nulos, 2 407 órdenes quedarían fuera de cualquier cruce y no podría compararse con y sin promoción."],
    ["Esquema estrella con Categoría y Proveedor dentro de DimProducto", "Copo de nieve", "Menos uniones en las consultas y un modelo más fácil de leer para el usuario de negocio."],
    ["Medidas derivadas calculadas en el ETL", "Calcularlas en el dashboard", "Quedan disponibles para cualquier herramienta y el dashboard solo agrega."],
    ["Razones calculadas en el dashboard", "Guardar el margen % en el hecho", "Un porcentaje guardado no se puede sumar ni promediar correctamente al agregar."],
    ["Consulta entre hechos para el margen después de devoluciones", "Unir FactVentas y FactDevoluciones por línea", "La unión directa repite filas; agregar cada hecho por separado y combinar por dimensiones conformadas da el valor exacto."],
    ["Filtros como parámetros de contexto", "Filtros de hoja independientes", "Un parámetro filtra las dos fuentes del dashboard a la vez y el ranking de productos se calcula dentro del filtro."],
], [30, 25, 45])

# =====================================================================================
# 9. ENTREGABLES
# =====================================================================================
h2("9. Entregables")
tabla(["Entregable", "Archivo"], [
    ["Documento de la solución", "`3_Informes/Practica1_Documento_Solucion.pdf`"],
    ["Script SQL del Data Warehouse", "`4_Data_Warehouse/DW_Retail.sql` y `4_Data_Warehouse/Cargar_DW.sql`"],
    ["Flujo de Tableau Prep", "`5_ETL/ETL_DW_Retail.tfl`, con sus salidas en `5_ETL/CSV_salida`"],
    ["Dashboard interactivo", "`7_Dashboard/Dashboard_Retail.twbx`, con las consultas en `7_Dashboard/Consultas_Dashboard.sql`"],
], [30, 70])


# =====================================================================================
# RENDERIZADO (motor compartido con los documentos de las actividades)
# =====================================================================================
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_motor.py")).read())
