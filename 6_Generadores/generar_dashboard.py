"""Genera el libro de Tableau del dashboard de la actividad 7 (Práctica 1, ICC-321).

El libro tiene dos tableros sobre el extracto Dashboard_DW_Retail.hyper, que sale
de DW_Retail con generar_extracto_dashboard.py:

  1. Rentabilidad de la venta   (P1, P2, P5, P6, P7)   fuente: tabla Ventas
  2. Devoluciones y proveedores (P3, P4, P8)           fuente: tabla RentabilidadProducto

Los filtros son parámetros (Año, Categoría, Canal), porque un parámetro es global
y filtra a la vez las dos fuentes. Cada hoja aplica el campo calculado [Filtro].

Un .twb es XML que Tableau valida al abrirlo; escribirlo aquí permite regenerarlo
igual cada vez. El .twbx empaqueta el libro con el extracto para abrirlo en
cualquier equipo con Tableau Desktop.

Uso:     python3 generar_dashboard.py [--ruta-extracto C:\\ruta\\Dashboard_DW_Retail.hyper]
Salida:  7_Dashboard/Dashboard_Retail.twb y 7_Dashboard/Dashboard_Retail.twbx
"""
import os
import sys
import uuid
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
SALIDA = os.path.join(TAREA, "7_Dashboard")
HYPER = "Dashboard_DW_Retail.hyper"

# Colores: los mismos azules de los informes; el ladrillo marca lo que resta margen.
TINTA = "#14243d"
AZUL = "#1f4e79"
AZUL_CLARO = "#dbe6f2"
LADRILLO = "#b5523b"
LADRILLO_CLARO = "#f3ddd6"
GRIS = "#6b7688"
GRIS_BARRA = "#a9b3c1"
FUENTE = "Tableau Book"
FUENTE_TITULO = "Tableau Semibold"


def uid():
    return "{%s}" % str(uuid.uuid4()).upper()


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("'", "&apos;").replace('"', "&quot;"))


# =====================================================================================
# FUENTES DE DATOS
# =====================================================================================

class Fuente:
    """Una tabla del extracto: columnas, campos calculados y formato de cada campo."""

    def __init__(self, nombre, caption, tabla, columnas, calculos):
        self.nombre = nombre          # federated.<algo>
        self.caption = caption
        self.tabla = tabla
        self.columnas = columnas      # (nombre, datatype, caption|None, formato|None)
        self.calculos = calculos      # (id, caption, datatype, role, type, formula, formato)
        self.col = {c[0]: c for c in columnas}
        self.calc = {c[0]: c for c in calculos}

    def decl(self, campo, indent="            "):
        """Declaración de un campo (columna o cálculo) para datasource-dependencies."""
        if campo in self.col:
            n, dt, cap, fmt = self.col[campo]
            role, ty = rol_tipo(dt, n)
            extra = (" caption='%s'" % esc(cap) if cap else "") + \
                    (" default-format='%s'" % esc(fmt) if fmt else "")
            return "%s<column%s datatype='%s' name='[%s]' role='%s' type='%s' />" % (
                indent, extra, dt, n, role, ty)
        i, cap, dt, role, ty, formula, fmt = self.calc[campo]
        extra = " default-format='%s'" % esc(fmt) if fmt else ""
        if i in TABLA_CALC:
            calc = ("%s  <calculation class='tableau' formula='%s'>\n%s    <table-calc ordering-type='Columns' />\n"
                    "%s  </calculation>\n" % (indent, esc(formula), indent, indent))
        else:
            calc = "%s  <calculation class='tableau' formula='%s' />\n" % (indent, esc(formula))
        return ("%s<column caption='%s' datatype='%s'%s name='[%s]' role='%s' type='%s'>\n%s%s</column>") % (
            indent, esc(cap), dt, extra, i, role, ty, calc, indent)


def rol_tipo(dt, nombre):
    if nombre == "Anio":
        return "dimension", "ordinal"
    if dt in ("integer", "real") and nombre not in ("VentaKey", "OrdenID", "Trimestre", "Mes"):
        return "measure", "quantitative"
    if dt == "date":
        return "dimension", "ordinal"
    return "dimension", ("ordinal" if dt == "integer" else "nominal")


MONEDA = 'n"RD$ "#,##0;-"RD$ "#,##0'
MILLONES = 'n"RD$ "#,##0.0" M";-"RD$ "#,##0.0" M"'
PORC = "p0.0%"
ENTERO = "n#,##0"

FILTRO_VENTAS = ('([Parameters].[p_anio] = "Todos" OR STR([Anio]) = [Parameters].[p_anio]) '
                 'AND ([Parameters].[p_categoria] = "Todas" OR [Categoria] = [Parameters].[p_categoria]) '
                 'AND ([Parameters].[p_canal] = "Todos" OR [CanalVenta] = [Parameters].[p_canal])')
FILTRO_PRODUCTO = ('([Parameters].[p_anio] = "Todos" OR STR([Anio]) = [Parameters].[p_anio]) '
                   'AND ([Parameters].[p_categoria] = "Todas" OR [Categoria] = [Parameters].[p_categoria])')

VENTAS = Fuente("federated.ventas", "Ventas (DW_Retail)", "Ventas", [
    ("VentaKey", "integer", None, None),
    ("OrdenID", "integer", "Orden", None),
    ("Fecha", "date", "Fecha", None),
    ("Anio", "integer", "Año", None),
    ("Trimestre", "integer", None, None),
    ("Mes", "integer", None, None),
    ("NombreMes", "string", "Mes", None),
    ("Categoria", "string", "Categoría", None),
    ("Marca", "string", None, None),
    ("Proveedor", "string", None, None),
    ("PaisProveedor", "string", "País del proveedor", None),
    ("NombreProducto", "string", "Producto", None),
    ("RangoPrecio", "string", "Rango de precio", None),
    ("Segmento", "string", "Segmento de cliente", None),
    ("ProvinciaCliente", "string", "Provincia del cliente", None),
    ("NombreTienda", "string", "Tienda", None),
    ("TipoTienda", "string", "Tipo de tienda", None),
    ("ProvinciaTienda", "string", "Provincia de la tienda", None),
    ("CanalVenta", "string", "Canal", None),
    ("Promocion", "string", "Promoción", None),
    ("TipoVenta", "string", "Tipo de venta", None),
    ("Campana", "string", "Campaña", None),
    ("PorcentajeDto", "real", "Descuento de la promoción", None),
    ("CantidadVendida", "integer", "Unidades vendidas", ENTERO),
    ("MontoBruto", "real", "Venta bruta", MONEDA),
    ("DescuentoMonto", "real", "Descuento", MONEDA),
    ("MontoNeto", "real", "Venta neta", MONEDA),
    ("CostoTotal", "real", "Costo", MONEDA),
    ("MargenBruto", "real", "Margen bruto", MONEDA),
], [
    ("MargenPct", "Margen %", "real", "measure", "quantitative",
     "SUM([MargenBruto]) / SUM([MontoNeto])", PORC),
    ("Ordenes", "Órdenes", "integer", "measure", "quantitative", "COUNTD([OrdenID])", ENTERO),
    ("Ticket", "Ticket promedio", "real", "measure", "quantitative",
     "SUM([MontoNeto]) / COUNTD([OrdenID])", MONEDA),
    ("VentaM", "Venta neta", "real", "measure", "quantitative", "SUM([MontoNeto]) / 1000000", MILLONES),
    ("MargenM", "Margen bruto", "real", "measure", "quantitative", "SUM([MargenBruto]) / 1000000", MILLONES),
    ("Participacion", "Participación en la venta", "real", "measure", "quantitative",
     "SUM([MontoNeto]) / TOTAL(SUM([MontoNeto]))", PORC),
    ("Filtro", "Filtro del tablero", "boolean", "dimension", "nominal", FILTRO_VENTAS, None),
])

PRODUCTO = Fuente("federated.producto", "Rentabilidad por producto (DW_Retail)", "RentabilidadProducto", [
    ("Anio", "integer", "Año", None),
    ("Categoria", "string", "Categoría", None),
    ("Marca", "string", None, None),
    ("Proveedor", "string", None, None),
    ("PaisProveedor", "string", "País del proveedor", None),
    ("NombreProducto", "string", "Producto", None),
    ("MontoNeto", "real", "Venta neta", MONEDA),
    ("CostoTotal", "real", "Costo", MONEDA),
    ("MargenBruto", "real", "Margen bruto", MONEDA),
    ("LineasVendidas", "integer", "Líneas vendidas", ENTERO),
    ("UnidadesVendidas", "integer", "Unidades vendidas", ENTERO),
    ("Devoluciones", "integer", "Devoluciones", ENTERO),
    ("UnidadesDevueltas", "integer", "Unidades devueltas", ENTERO),
    ("MontoReembolso", "real", "Reembolsos", MONEDA),
], [
    ("TasaDev", "Tasa de devolución", "real", "measure", "quantitative",
     "SUM([Devoluciones]) / SUM([LineasVendidas])", PORC),
    ("MargenPct", "Margen %", "real", "measure", "quantitative",
     "SUM([MargenBruto]) / SUM([MontoNeto])", PORC),
    ("MargenNeto", "Margen después de devoluciones", "real", "measure", "quantitative",
     "SUM([MargenBruto]) - SUM([MontoReembolso])", MONEDA),
    ("MargenNetoM", "Margen después de devoluciones", "real", "measure", "quantitative",
     "(SUM([MargenBruto]) - SUM([MontoReembolso])) / 1000000", MILLONES),
    ("MargenM", "Margen bruto", "real", "measure", "quantitative", "SUM([MargenBruto]) / 1000000", MILLONES),
    ("ReembolsoM", "Reembolsos", "real", "measure", "quantitative", "SUM([MontoReembolso]) / 1000000", MILLONES),
    ("PerdidaPct", "Margen que se va en reembolsos", "real", "measure", "quantitative",
     "SUM([MontoReembolso]) / SUM([MargenBruto])", PORC),
    ("Filtro", "Filtro del tablero", "boolean", "dimension", "nominal", FILTRO_PRODUCTO, None),
])

CATEGORIAS = ["Alimentos y bebidas", "Bebés", "Cuidado personal", "Deportes", "Electrodomésticos",
              "Hogar y limpieza", "Mascotas", "Moda", "Papelería", "Tecnología"]
PARAMETROS = [
    ("p_anio", "Año", "Todos", ["Todos", "2023", "2024", "2025", "2026"]),
    ("p_categoria", "Categoría", "Todas", ["Todas"] + CATEGORIAS),
    ("p_canal", "Canal", "Todos", ["Todos", "Tienda", "Web", "App"]),
]


def fuente_parametros():
    cols = []
    for n, cap, defecto, valores in PARAMETROS:
        miembros = "\n".join("        <member value='&quot;%s&quot;' />" % esc(v) for v in valores)
        cols.append(
            "      <column caption='%s' datatype='string' name='[%s]' param-domain-type='list' "
            "role='measure' type='nominal' value='&quot;%s&quot;'>\n"
            "        <calculation class='tableau' formula='&quot;%s&quot;' />\n"
            "        <members>\n%s\n        </members>\n      </column>"
            % (esc(cap), n, esc(defecto), esc(defecto), miembros))
    return ("    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>\n"
            "      <aliases enabled='yes' />\n%s\n    </datasource>" % "\n".join(cols))


def deps_parametros():
    cuerpo = "\n".join(
        "            <column caption='%s' datatype='string' name='[%s]' param-domain-type='list' "
        "role='measure' type='nominal' value='&quot;%s&quot;'>\n"
        "              <calculation class='tableau' formula='&quot;%s&quot;' />\n"
        "            </column>" % (esc(cap), n, esc(d), esc(d)) for n, cap, d, _ in PARAMETROS)
    return "          <datasource-dependencies datasource='Parameters'>\n%s\n          </datasource-dependencies>" % cuerpo


# Identificador fijo del objeto lógico de cada tabla (Tableau lo usa en object-graph).
OBJETO = {"Ventas": "5C2467DE9A5C49019266D47BE9385E98", "RentabilidadProducto": "8A41D0C2B7E54F6A9D3E1F0B6C7A2D19"}
REMOTO = {"string": 129, "integer": 20, "real": 5, "date": 133}
AGREGADO = {"string": "Count", "integer": "Sum", "real": "Sum", "date": "Year"}


def fuente_xml(f, ruta_extracto):
    objeto = "%s (Extract.%s)_%s" % (f.tabla, f.tabla, OBJETO[f.tabla])
    meta = "\n".join("""        <metadata-record class='column'>
          <remote-name>%s</remote-name>
          <remote-type>%d</remote-type>
          <local-name>[%s]</local-name>
          <parent-name>[%s]</parent-name>
          <remote-alias>%s</remote-alias>
          <ordinal>%d</ordinal>
          <local-type>%s</local-type>
          <aggregation>%s</aggregation>
          <contains-null>true</contains-null>
          <object-id>[%s]</object-id>
        </metadata-record>""" % (n, REMOTO[dt], n, f.tabla, n, i, dt, AGREGADO[dt], objeto)
                     for i, (n, dt, _, _) in enumerate(f.columnas))
    columnas = "\n".join(f.decl(c[0], indent="      ") for c in f.columnas)
    calculos = "\n".join(f.decl(c[0], indent="      ") for c in f.calculos)
    conexion = "hyper." + f.tabla.lower()
    inst_paleta, estilo_paleta = paletas_fuente(f) or ("", "")
    return f"""    <datasource caption='{esc(f.caption)}' inline='true' name='{f.nombre}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='Dashboard_DW_Retail' name='{conexion}'>
            <connection authentication='auth-none' author-locale='en_US' class='hyper' dbname='{esc(ruta_extracto)}' default-settings='yes' server='' sslmode='' username='tableau_internal_user' />
          </named-connection>
        </named-connections>
        <relation connection='{conexion}' name='{f.tabla}' table='[Extract].[{f.tabla}]' type='table' />
        <metadata-records>
{meta}
        </metadata-records>
      </connection>
      <aliases enabled='yes' />
      <column datatype='string' name='[:Measure Names]' role='dimension' type='nominal' />
{columnas}
{calculos}
      <column caption='{f.tabla}' datatype='table' name='[__tableau_internal_object_id__].[{objeto}]' role='measure' type='quantitative' />
{inst_paleta}      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
{estilo_paleta}      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;Dominican Republic&quot;' />
      </semantic-values>
      <object-graph>
        <objects>
          <object caption='{f.tabla}' id='{objeto}'>
            <properties context=''>
              <relation connection='{conexion}' name='{f.tabla}' table='[Extract].[{f.tabla}]' type='table' />
            </properties>
          </object>
        </objects>
      </object-graph>
    </datasource>"""


# =====================================================================================
# HOJAS
# =====================================================================================

PREFIJO = {"None": "none", "Sum": "sum", "User": "usr", "Month-Trunc": "tmn", "Avg": "avg"}


class I:
    """Instancia de un campo en una hoja: campo, derivación y tipo (nk, ok o qk)."""

    def __init__(self, f, campo, deriv="None", tipo=None):
        self.f, self.campo, self.deriv = f, campo, deriv
        if tipo is None:
            tipo = "quantitative" if deriv in ("Sum", "User", "Avg", "Month-Trunc") else "nominal"
        self.tipo = tipo
        clave = {"quantitative": "qk", "nominal": "nk", "ordinal": "ok"}[tipo]
        self.nombre = "[%s:%s:%s]" % (PREFIJO[deriv], campo, clave)
        self.ref = "[%s].%s" % (f.nombre, self.nombre)

    def decl(self):
        return ("            <column-instance column='[%s]' derivation='%s' name='%s' pivot='key' type='%s' />"
                % (self.campo, self.deriv, self.nombre, self.tipo))


# Cálculos de tabla: se calculan sobre la tabla hacia abajo.
TABLA_CALC = {"Participacion"}


def texto(runs):
    """runs: lista de (texto, dict de atributos). Devuelve <formatted-text>."""
    partes = []
    for t, a in runs:
        attrs = "".join(" %s='%s'" % (k, esc(v)) for k, v in a.items())
        partes.append("<run%s>%s</run>" % (attrs, esc(t).replace("\n", "&#10;")))
    return "<formatted-text>%s</formatted-text>" % "".join(partes)


def titulo_hoja(t, sub=None):
    runs = [(t, {"bold": "true", "fontcolor": TINTA, "fontname": FUENTE_TITULO, "fontsize": "11"})]
    if sub:
        runs += [("Æ\n", {}), (sub, {"fontcolor": GRIS, "fontname": FUENTE, "fontsize": "9"})]
    return texto(runs)


# Colores fijos de las dimensiones: Tableau los guarda en la fuente, no en la hoja.
PALETAS = {"TipoVenta": [("Sin promoción", GRIS_BARRA), ("Con promoción", AZUL)]}


def paletas_fuente(f):
    reglas = []
    for campo, mapa in PALETAS.items():
        if campo not in f.col:
            continue
        filas = "\n".join("            <map to='%s'><bucket>&quot;%s&quot;</bucket></map>" % (c, esc(v))
                          for v, c in mapa)
        reglas.append("        <style-rule element='mark'>\n"
                      "          <encoding attr='color' field='[none:%s:nk]' type='palette'>\n%s\n"
                      "          </encoding>\n        </style-rule>" % (campo, filas))
    if not reglas:
        return ""
    instancias = "".join("      <column-instance column='[%s]' derivation='None' name='[none:%s:nk]' pivot='key' type='nominal' />\n"
                         % (c, c) for c in PALETAS if c in f.col)
    return instancias, "      <style>\n%s\n      </style>\n" % "\n".join(reglas)


def degradado(inst, desde, hasta):
    return ("          <style-rule element='mark'>\n"
            "            <encoding attr='color' field='%s' type='custom-interpolated'>\n"
            "              <color-palette custom='true' name='' type='ordered-sequential'>\n"
            "                <color>%s</color>\n                <color>%s</color>\n"
            "              </color-palette>\n            </encoding>\n          </style-rule>"
            % (inst.ref, desde, hasta))


def sin_titulo_eje(inst, ambito):
    return ("          <style-rule element='axis'>\n"
            "            <format attr='title' class='0' field='%s' scope='%s' value='' />\n"
            "            <format attr='display' class='0' field='%s' scope='%s' value='false' />\n"
            "          </style-rule>" % (inst.ref, ambito, inst.ref, ambito))


def eje_titulo(inst, ambito, titulo):
    return ("          <style-rule element='axis'>\n"
            "            <format attr='title' class='0' field='%s' scope='%s' value='%s' />\n"
            "            <format attr='font-size' value='8' />\n"
            "            <format attr='color' value='%s' />\n"
            "          </style-rule>" % (inst.ref, ambito, esc(titulo), GRIS))


ESTILO_BASE = f"""          <style-rule element='worksheet'>
            <format attr='display-field-labels' scope='cols' value='false' />
            <format attr='display-field-labels' scope='rows' value='false' />
            <format attr='font-family' value='{FUENTE}' />
            <format attr='color' value='{TINTA}' />
          </style-rule>
          <style-rule element='header'>
            <format attr='font-size' value='9' />
            <format attr='color' value='{TINTA}' />
          </style-rule>
          <style-rule element='gridline'>
            <format attr='stroke-size' value='0' />
            <format attr='line-visibility' value='off' />
          </style-rule>
          <style-rule element='zeroline'>
            <format attr='stroke-size' value='0' />
            <format attr='line-visibility' value='off' />
          </style-rule>
          <style-rule element='table-div'>
            <format attr='stroke-size' scope='rows' value='0' />
            <format attr='line-visibility' scope='rows' value='off' />
            <format attr='stroke-size' scope='cols' value='0' />
            <format attr='line-visibility' scope='cols' value='off' />
          </style-rule>
          <style-rule element='label'>
            <format attr='font-size' value='8' />
            <format attr='color' value='{TINTA}' />
          </style-rule>"""


def hoja(nombre, f, titulo, rows, cols, marca, codif, extra_estilo="", orden=None,
         etiquetas=True, instancias_extra=(), filtros_extra="", subtitulo=None,
         etiqueta_formato=None, color_marca=None):
    """Una hoja de trabajo.

    rows, cols: listas de instancias (se anidan con '/').
    codif: lista de (atributo, instancia): color, text, label, size, tooltip.
    orden: (instancia de la dimensión, instancia de la medida, 'ASC'|'DESC').
    """
    filtro = I(f, "Filtro")
    usadas = list(rows) + list(cols) + [i for _, i in codif] + list(instancias_extra) + [filtro]
    if orden:
        usadas += [orden[1]]
    campos, vistos_c, inst, vistos_i = [], set(), [], set()
    for i in usadas:
        if i.campo not in vistos_c:
            vistos_c.add(i.campo)
            campos.append(i.campo)
        if i.nombre not in vistos_i:
            vistos_i.add(i.nombre)
            inst.append(i)
    # Los cálculos que usan otros campos necesitan declarar esos campos también.
    for c in list(campos):
        if c in f.calc:
            for base in [x[0] for x in f.columnas] + [x[0] for x in f.calculos]:
                if "[%s]" % base in f.calc[c][5] and base not in vistos_c:
                    vistos_c.add(base)
                    campos.append(base)
    deps = ("          <datasource-dependencies datasource='%s'>\n%s\n%s\n          </datasource-dependencies>"
            % (f.nombre, "\n".join(f.decl(c) for c in campos), "\n".join(i.decl() for i in inst)))
    filtro_xml = ("          <filter class='categorical' column='%s' context='true'>\n"
                  "            <groupfilter function='member' level='%s' member='true' "
                  "user:ui-domain='relevant' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n"
                  "          </filter>" % (filtro.ref, filtro.nombre))
    orden_xml = ""
    if orden:
        orden_xml = ("\n          <sort class='computed' column='%s' direction='%s' using='%s' />"
                     % (orden[0].ref, orden[2], orden[1].ref))
    view = f"""          <datasources>
            <datasource caption='{esc(f.caption)}' name='{f.nombre}' />
            <datasource name='Parameters' />
          </datasources>
{deps}
{deps_parametros()}
{filtro_xml}{filtros_extra}{orden_xml}
          <slices>
            <column>{filtro.ref}</column>
          </slices>
          <aggregation value='true' />"""
    enc = "\n".join("              <%s column='%s' />" % (a, i.ref) for a, i in codif)
    estilo_marca = [f"<format attr='mark-labels-show' value='{'true' if etiquetas else 'false'}' />",
                    "<format attr='mark-labels-cull' value='true' />"]
    if color_marca:
        estilo_marca.append("<format attr='mark-color' value='%s' />" % color_marca)
    etiqueta = ""
    if etiqueta_formato:
        etiqueta = "\n              <customized-label>\n                %s\n              </customized-label>" % etiqueta_formato
    panes = f"""          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{marca}' />
            <encodings>
{enc}
            </encodings>{etiqueta}
            <style>
              <style-rule element='mark'>
                {chr(10).join('                ' + s for s in estilo_marca).strip()}
              </style-rule>
            </style>
          </pane>"""
    r = " / ".join(i.ref for i in rows)
    c = " / ".join(i.ref for i in cols)
    return f"""    <worksheet name='{esc(nombre)}'>
      <layout-options>
        <title>
          {titulo_hoja(titulo, subtitulo)}
        </title>
      </layout-options>
      <table>
        <view>
{view}
        </view>
        <style>
{ESTILO_BASE}
{extra_estilo}
        </style>
        <panes>
{panes}
        </panes>
        {'<rows>%s</rows>' % r if r else '<rows />'}
        {'<cols>%s</cols>' % c if c else '<cols />'}
      </table>
      <simple-id uuid='{uid()}' />
    </worksheet>"""


def tarjeta(nombre, f, rotulo, medida):
    """Cifra de cabecera: el rótulo va como título y la cifra como texto grande."""
    estilo = """          <style-rule element='mark'>
            <format attr='font-size' value='18' />
          </style-rule>"""
    etiqueta = texto([("<%s>" % medida.ref,
                       {"bold": "true", "fontcolor": TINTA, "fontname": FUENTE_TITULO, "fontsize": "18"})])
    x = hoja(nombre, f, rotulo, [], [], "Text", [("text", medida)], estilo, etiqueta_formato=etiqueta)
    # El título de una tarjeta es el rótulo, pequeño y gris.
    return x.replace(titulo_hoja(rotulo), texto([(rotulo, {"fontcolor": GRIS, "fontname": FUENTE, "fontsize": "9"})]))


def hojas_ventas():
    v = VENTAS
    cat, venta, margen = I(v, "Categoria"), I(v, "MontoNeto", "Sum"), I(v, "MargenPct", "User")
    mes, camp, canal, tipo = I(v, "Fecha", "Month-Trunc"), I(v, "Campana"), I(v, "CanalVenta"), I(v, "TipoTienda")
    ticket, seg, part = I(v, "Ticket", "User"), I(v, "Segmento"), I(v, "Participacion", "User")
    ventam = I(v, "VentaM", "User")
    h = {}
    h["V KPI venta"] = tarjeta("V KPI venta", v, "Venta neta", ventam)
    h["V KPI margen"] = tarjeta("V KPI margen", v, "Margen bruto", I(v, "MargenM", "User"))
    h["V KPI margen %"] = tarjeta("V KPI margen %", v, "Margen %", margen)
    h["V KPI ordenes"] = tarjeta("V KPI ordenes", v, "Órdenes completadas", I(v, "Ordenes", "User"))
    h["V KPI ticket"] = tarjeta("V KPI ticket", v, "Ticket promedio", ticket)

    h["Categorias"] = hoja(
        "Categorias", v, "P1. Venta neta por categoría y su margen", [cat], [venta], "Bar",
        [("color", margen), ("text", margen)],
        degradado(margen, AZUL_CLARO, AZUL) + "\n" + sin_titulo_eje(venta, "cols"),
        orden=(cat, venta, "DESC"),
        subtitulo="Largo de la barra: venta neta. Color y etiqueta: margen %.")

    h["Mensual"] = hoja(
        "Mensual", v, "P5. Venta neta por mes", [ventam], [mes], "Area", [],
        eje_titulo(ventam, "rows", "") + "\n" + eje_titulo(mes, "cols", ""),
        etiquetas=False, color_marca=AZUL,
        subtitulo="Órdenes completadas. La caída final se debe a que agosto de 2026 solo llega al día 15.")

    h["Promociones"] = hoja(
        "Promociones", v, "P2. Margen % según la campaña", [camp], [margen], "Bar",
        [("color", I(v, "TipoVenta")), ("text", margen)],
        sin_titulo_eje(margen, "cols"),
        orden=(camp, margen, "DESC"),
        subtitulo="Entre paréntesis, el descuento de cada campaña.")

    h["Canales"] = hoja(
        "Canales", v, "P6. Ticket promedio por canal y tipo de tienda", [tipo], [canal], "Square",
        [("color", I(v, "MontoNeto", "Sum")), ("text", ticket)],
        degradado(I(v, "MontoNeto", "Sum"), "#eef3f9", "#8fb0d3"),
        subtitulo="Número: ticket promedio. Color: venta neta acumulada.")

    h["Segmentos"] = hoja(
        "Segmentos", v, "P7. Venta neta por segmento de cliente", [seg], [venta], "Bar",
        [("text", part)],
        sin_titulo_eje(venta, "cols"),
        orden=(seg, venta, "DESC"),
        color_marca=AZUL, subtitulo="Etiqueta: participación en la venta neta.")
    return h


def hojas_producto():
    p = PRODUCTO
    cat, tasa = I(p, "Categoria"), I(p, "TasaDev", "User")
    prov, margen = I(p, "Proveedor"), I(p, "MargenPct", "User")
    prod, reemb = I(p, "NombreProducto"), I(p, "MontoReembolso", "Sum")
    neto, perdida = I(p, "MargenNeto", "User"), I(p, "PerdidaPct", "User")
    h = {}
    h["D KPI reembolso"] = tarjeta("D KPI reembolso", p, "Reembolsos", I(p, "ReembolsoM", "User"))
    h["D KPI tasa"] = tarjeta("D KPI tasa", p, "Tasa de devolución", tasa)
    h["D KPI margen"] = tarjeta("D KPI margen", p, "Margen bruto", I(p, "MargenM", "User"))
    h["D KPI neto"] = tarjeta("D KPI neto", p, "Margen después de devoluciones", I(p, "MargenNetoM", "User"))
    h["D KPI perdida"] = tarjeta("D KPI perdida", p, "Margen que se va en reembolsos", perdida)

    h["Tasa devolucion"] = hoja(
        "Tasa devolucion", p, "P3. Tasa de devolución por categoría", [cat], [tasa], "Bar",
        [("color", tasa), ("text", tasa)],
        degradado(tasa, LADRILLO_CLARO, LADRILLO) + "\n" + sin_titulo_eje(tasa, "cols"),
        orden=(cat, tasa, "DESC"),
        subtitulo="Devoluciones sobre líneas vendidas.")

    h["Margen neto"] = hoja(
        "Margen neto", p, "P4. Margen después de devoluciones por categoría", [cat], [neto], "Bar",
        [("color", perdida), ("text", perdida)],
        degradado(perdida, LADRILLO_CLARO, LADRILLO) + "\n" + sin_titulo_eje(neto, "cols"),
        orden=(cat, neto, "DESC"),
        subtitulo="Barra: margen bruto menos reembolsos. Etiqueta: margen que se va en reembolsos.")

    h["Proveedores"] = hoja(
        "Proveedores", p, "P8. Proveedores: margen % frente a tasa de devolución", [tasa], [margen],
        "Circle", [("text", prov), ("size", I(p, "MontoNeto", "Sum")), ("lod", prov)],
        eje_titulo(tasa, "rows", "Tasa de devolución") + "\n" + eje_titulo(margen, "cols", "Margen %")
        + "\n          <style-rule element='axis'>\n"
        "            <encoding attr='space' class='0' field='%s' field-type='quantitative' max='0.36' min='0.14' "
        "range-type='fixed' scope='cols' type='space' />\n          </style-rule>" % margen.ref,
        color_marca=AZUL,
        subtitulo="Cada punto es un proveedor; el tamaño es su venta neta.")

    h["Productos"] = hoja(
        "Productos", p, "P3. Productos con más reembolsos", [prod, cat], [reemb], "Bar",
        [("text", reemb)],
        sin_titulo_eje(reemb, "cols") + """
          <style-rule element='header'>
            <format attr='width' field='%s' value='84' />
            <format attr='width' field='%s' value='118' />
          </style-rule>""" % (prod.ref, cat.ref),
        orden=(prod, reemb, "DESC"),
        filtros_extra="""
          <filter class='categorical' column='%s'>
            <groupfilter count='10' end='top' function='end' units='records' user:ui-marker='end' user:ui-top-by-field='true'>
              <groupfilter direction='DESC' expression='SUM([MontoReembolso])' function='order' user:ui-marker='order'>
                <groupfilter function='level-members' level='%s' user:ui-enumeration='all' user:ui-marker='enumerate' />
              </groupfilter>
            </groupfilter>
          </filter>""" % (prod.ref, prod.nombre),
        color_marca=LADRILLO, subtitulo="Los diez de mayor monto reembolsado.")
    return h


# =====================================================================================
# TABLEROS
# =====================================================================================

ESTILO_ZONA = """            <zone-style>
              <format attr='border-style' value='none' />
              <format attr='border-width' value='0' />
              <format attr='margin' value='%d' />
            </zone-style>"""


def zona_hoja(i, nombre, x, y, w, h, margen=6):
    return ("          <zone h='%d' id='%d' name='%s' show-title='true' w='%d' x='%d' y='%d'>\n%s\n          </zone>"
            % (h, i, esc(nombre), w, x, y, ESTILO_ZONA % margen))


def zona_texto(i, runs, x, y, w, h):
    return ("          <zone h='%d' id='%d' type-v2='text' w='%d' x='%d' y='%d'>\n            %s\n%s\n          </zone>"
            % (h, i, w, x, y, texto(runs), ESTILO_ZONA % 4))


def zona_parametro(i, param, x, y, w, h):
    return ("          <zone h='%d' id='%d' mode='compact' param='[Parameters].[%s]' type-v2='paramctrl' w='%d' x='%d' y='%d'>\n%s\n          </zone>"
            % (h, i, param, w, x, y, ESTILO_ZONA % 4))


def encabezado(titulo, subtitulo, parametros):
    z = [zona_texto(2, [(titulo, {"bold": "true", "fontcolor": TINTA, "fontname": FUENTE_TITULO, "fontsize": "17"}),
                        ("Æ\n", {}),
                        (subtitulo, {"fontcolor": GRIS, "fontname": FUENTE, "fontsize": "9"})],
                    800, 600, 60000, 7400)]
    ancho = 11500
    x = 100000 - 800 - ancho * len(parametros)
    for n, prm in enumerate(parametros):
        z.append(zona_parametro(3 + n, prm, x + n * ancho, 900, ancho - 400, 6800))
    return z


def fila_tarjetas(nombres, primer_id, y=8600, h=9200):
    ancho = (100000 - 1600) // len(nombres)
    return [zona_hoja(primer_id + n, nm, 800 + n * ancho, y, ancho, h, margen=8)
            for n, nm in enumerate(nombres)]


def tablero(nombre, fuente, zonas, hojas_usadas):
    return f"""    <dashboard name='{esc(nombre)}'>
      <style>
        <style-rule element='table'>
          <format attr='background-color' value='#ffffff' />
        </style-rule>
      </style>
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' />
      <datasources>
        <datasource name='Parameters' />
        <datasource caption='{esc(fuente.caption)}' name='{fuente.nombre}' />
      </datasources>
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
{chr(10).join(zonas)}
        </zone>
      </zones>
      <devicelayouts>
        <devicelayout name='Phone'>
          <size maxheight='1800' minheight='1800' sizing-mode='vscroll' />
          <zones>
            <zone h='100000' id='1' param='vert' type-v2='layout-flow' w='100000' x='0' y='0'>
              <zone h='100000' id='2' type-v2='text' w='100000' x='0' y='0' />
            </zone>
          </zones>
        </devicelayout>
      </devicelayouts>
      <simple-id uuid='{uid()}' />
    </dashboard>"""


KPI_VENTAS = ["V KPI venta", "V KPI margen", "V KPI margen %", "V KPI ordenes", "V KPI ticket"]
KPI_DEV = ["D KPI reembolso", "D KPI tasa", "D KPI margen", "D KPI neto", "D KPI perdida"]
TABLERO_1 = "Rentabilidad de la venta"
TABLERO_2 = "Devoluciones y proveedores"


def tablero_ventas():
    z = encabezado("Rentabilidad de la venta al detalle",
                   "Fuente: DW_Retail, hecho FactVentas. Órdenes completadas del 1 de enero de 2023 al 15 de agosto de 2026.",
                   ["p_anio", "p_categoria", "p_canal"])
    z += fila_tarjetas(KPI_VENTAS, 10)
    z += [zona_hoja(20, "Categorias", 800, 18400, 48800, 38600),
          zona_hoja(21, "Mensual", 50400, 18400, 48800, 38600),
          zona_hoja(22, "Promociones", 800, 57600, 32400, 41800),
          zona_hoja(23, "Canales", 33800, 57600, 32400, 41800),
          zona_hoja(24, "Segmentos", 66800, 57600, 32400, 41800)]
    return tablero(TABLERO_1, VENTAS, z, KPI_VENTAS + ["Categorias", "Mensual", "Promociones", "Canales", "Segmentos"])


def tablero_devoluciones():
    z = encabezado("Devoluciones y rentabilidad por proveedor",
                   "Fuente: DW_Retail, FactVentas y FactDevoluciones unidos por año y producto. Enero de 2023 a septiembre de 2026.",
                   ["p_anio", "p_categoria"])
    z += fila_tarjetas(KPI_DEV, 10)
    z += [zona_hoja(20, "Tasa devolucion", 800, 18400, 32400, 40600),
          zona_hoja(21, "Margen neto", 33800, 18400, 32400, 40600),
          zona_hoja(22, "Productos", 66800, 18400, 32400, 40600),
          zona_hoja(23, "Proveedores", 800, 59600, 98400, 39800)]
    return tablero(TABLERO_2, PRODUCTO, z, KPI_DEV + ["Tasa devolucion", "Margen neto", "Productos", "Proveedores"])


# =====================================================================================
# VENTANAS Y ARMADO
# =====================================================================================

def ventana_hoja(nombre):
    """Estado de la interfaz de una hoja. Tableau lo exige para dibujarla."""
    return f"""    <window class='worksheet' hidden='true' name='{esc(nombre)}'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
      </cards>
      <simple-id uuid='{uid()}' />
    </window>"""


def ventana_tablero(nombre, hojas, activa=False):
    vistas = "\n".join("        <viewpoint name='%s'>\n          <zoom type='entire-view' />\n        </viewpoint>"
                       % esc(h) for h in hojas)
    return f"""    <window class='dashboard' {"maximized='true' " if activa else ""}name='{esc(nombre)}'>
      <viewpoints>
{vistas}
      </viewpoints>
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>"""


def libro(ruta_extracto):
    hv, hp = hojas_ventas(), hojas_producto()
    todas = list(hv.items()) + list(hp.items())
    ventanas = "\n".join(ventana_hoja(n) for n, _ in todas)
    ventanas += "\n" + ventana_tablero(TABLERO_1, list(hv), activa=True)
    ventanas += "\n" + ventana_tablero(TABLERO_2, list(hp))
    return f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook source-build='2026.2.0 (20262.0.0)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <_.fcp.AnimationOnByDefault.true...AnimationOnByDefault />
    <_.fcp.MarkAnimation.true...MarkAnimation />
    <_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy />
    <_.fcp.ObjectModelTableType.true...ObjectModelTableType />
    <_.fcp.SchemaViewerObjectModel.true...SchemaViewerObjectModel />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{fuente_parametros()}
{fuente_xml(VENTAS, ruta_extracto)}
{fuente_xml(PRODUCTO, ruta_extracto)}
  </datasources>
  <worksheets>
{chr(10).join(x for _, x in todas)}
  </worksheets>
  <dashboards>
{tablero_ventas()}
{tablero_devoluciones()}
  </dashboards>
  <windows source-height='30'>
{ventanas}
  </windows>
</workbook>
"""


def main():
    ruta = HYPER
    if "--ruta-extracto" in sys.argv:
        ruta = sys.argv[sys.argv.index("--ruta-extracto") + 1]
    twb = os.path.join(SALIDA, "Dashboard_Retail.twb")
    with open(twb, "w", encoding="utf-8") as f:
        f.write(libro(ruta))
    print("Libro:", twb)
    # El paquete lleva el libro con la ruta relativa al extracto dentro de Data/.
    twbx = os.path.join(SALIDA, "Dashboard_Retail.twbx")
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Dashboard_Retail.twb", libro("Data/Extracts/" + HYPER))
        z.write(os.path.join(SALIDA, HYPER), "Data/Extracts/" + HYPER)
    print("Paquete:", twbx)


if __name__ == "__main__":
    main()
