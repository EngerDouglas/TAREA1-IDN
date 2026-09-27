"""Genera el flujo de Tableau Prep (.tfl) del ETL de la Práctica 1 — actividad 5.

Uso:  python3 generar_flujo_etl.py [carpeta_salida] [archivo_tfl]

Entradas : CSV extraídos del sistema operacional (carpeta origen/)
Salidas  : un CSV por tabla del Data Warehouse (carpeta salida_dw/)
"""
import json, os, sys, uuid, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
ORIGEN = os.path.join(TAREA, "2_Fuente", "CSV_origen")
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TAREA, "5_ETL", "CSV_salida")
TFL = sys.argv[2] if len(sys.argv) > 2 else os.path.join(TAREA, "5_ETL", "ETL_DW_Retail.tfl")
META = os.path.join(BASE, "_maestroMetadata")

conns = {}
nid = lambda: str(uuid.uuid4())


def fld(n, t):
    return {"name": n, "type": t, "collation": "LEN_RUS" if t == "string" else None,
            "caption": None, "ordinal": None, "isGenerated": False, "prettifiedName": None}


def base(nt, name, bt):
    return {"nodeType": nt, "name": name, "id": nid(), "baseType": bt,
            "nextNodes": [], "serialize": False, "description": None}


def link(a, b, ns="Default"):
    a["nextNodes"].append({"namespace": "Default", "nextNodeId": b["id"], "nextNamespace": ns})


def entrada(nombre, archivo, campos):
    cid = nid()
    conns[cid] = {"connectionType": ".v1.SqlConnection", "id": cid, "name": archivo, "isPackaged": False,
                  "connectionAttributes": {"filename": os.path.join(ORIGEN, archivo), "class": "textscan"}}
    n = base(".v1.LoadCsv", nombre, "input")
    n.update({"connectionId": cid, "connectionAttributes": {}, "fields": [fld(a, b) for a, b in campos],
              "actions": [], "debugModeRowLimit": 393216, "originalDataTypes": {}, "randomSampling": None,
              "updateTimestamp": None, "restrictedFields": {}, "userRenamedFields": {}, "selectedFields": None,
              "samplingType": None, "groupByFields": None, "filters": [], "separator": ",", "locale": "en_US",
              "charSet": "UTF-8", "containsHeaders": True, "textQualifier": "\""})
    return n


# ---- transformaciones dentro de un paso de limpieza ----
def calc(col, expr, nombre=None):
    n = base(".v1.AddColumn", nombre or ("Calcular " + col), "transform")
    n.update({"columnName": col, "expression": expr})
    return n


def renombrar(viejo, nuevo):
    n = base(".v1.RenameColumn", "Renombrar %s a %s" % (viejo, nuevo), "transform")
    n.update({"columnName": viejo, "rename": nuevo})
    return n


def quitar(cols, nombre=None):
    n = base(".v1.RemoveColumns", nombre or "Eliminar columnas no usadas", "transform")
    n["columnNames"] = cols
    return n


def filtro(expr, nombre):
    n = base(".v1.FilterOperation", nombre, "transform")
    n["filterExpression"] = expr
    return n


def tipo(col, t, nombre):
    n = base(".v1.ChangeColumnType", nombre, "transform")
    n["fields"] = {col: {"type": t, "calc": None}}
    return n


def paso(nombre, transformaciones):
    c = base(".v1.Container", nombre, "container")
    for a, b in zip(transformaciones, transformaciones[1:]):
        link(a, b)
    c["loomContainer"] = {"parameters": {"parameters": {}}, "initialNodes": [],
                          "nodes": {t["id"]: t for t in transformaciones}, "connections": {}, "connectionIds": []}
    c["namespacesToInput"] = {"Default": {"nodeId": transformaciones[0]["id"], "namespace": "Default"}}
    c["namespacesToOutput"] = {"Default": {"nodeId": transformaciones[-1]["id"], "namespace": "Default"}}
    c["providedParameters"] = {}
    return c


def join(nombre, izq, der, tipo_join="inner", quitar_despues=None):
    s = base(".v2018_2_3.SuperJoin", nombre, "superNode")
    a = base(".v1.SimpleJoin", nombre, "transform")
    a.update({"conditions": [{"leftExpression": "[%s]" % izq, "rightExpression": "[%s]" % der, "comparator": "=="}],
              "joinType": tipo_join})
    despues = []
    if quitar_despues:
        despues = [{"namespace": "Default", "annotationNode": quitar(quitar_despues, "Eliminar claves duplicadas")}]
    s.update({"beforeActionAnnotations": [], "afterActionAnnotations": despues, "actionNode": a})
    return s


def agregar(nombre, agrupar, agregados):
    s = base(".v2018_2_3.SuperAggregate", nombre, "superNode")
    a = base(".v1.Aggregate", nombre, "transform")
    a.update({"groupByFields": [{"columnName": g, "function": None, "newColumnName": None, "specialFieldType": None} for g in agrupar],
              "aggregateFields": [{"columnName": c, "function": f, "newColumnName": n, "specialFieldType": None} for c, f, n in agregados]})
    s.update({"beforeActionAnnotations": [], "afterActionAnnotations": [], "actionNode": a})
    return s


def salida(nombre, archivo):
    n = base(".v1.WriteToCsv", nombre, "output")
    n.update({"csvOutputFile": os.path.join(SALIDA, archivo), "separator": ","})
    return n


# =====================================================================================
# ENTRADAS (extracción)
# =====================================================================================
in_categoria = entrada("Categoria", "Categoria.csv", [("CategoriaID", "integer"), ("NombreCategoria", "string")])
in_proveedor = entrada("Proveedor", "Proveedor.csv", [("ProveedorID", "integer"), ("NombreProveedor", "string"),
                                                      ("Pais", "string"), ("FechaAlta", "date")])
in_producto = entrada("Producto", "Producto.csv", [("ProductoID", "integer"), ("SKU", "string"),
                                                   ("NombreProducto", "string"), ("CategoriaID", "integer"),
                                                   ("ProveedorID", "integer"), ("Marca", "string"),
                                                   ("CostoUnitario", "real"), ("PrecioLista", "real"),
                                                   ("FechaLanzamiento", "date"), ("Activo", "integer")])
in_tienda = entrada("Tienda", "Tienda.csv", [("TiendaID", "integer"), ("NombreTienda", "string"), ("Ciudad", "string"),
                                             ("Provincia", "string"), ("TipoTienda", "string"), ("FechaApertura", "date")])
in_cliente = entrada("Cliente", "Cliente.csv", [("ClienteID", "integer"), ("Nombre", "string"), ("Apellido", "string"),
                                                ("Sexo", "string"), ("FechaNacimiento", "date"), ("Ciudad", "string"),
                                                ("Provincia", "string"), ("Segmento", "string"), ("FechaRegistro", "date")])
in_promocion = entrada("Promocion", "Promocion.csv", [("PromocionID", "integer"), ("NombrePromocion", "string"),
                                                      ("FechaInicio", "date"), ("FechaFin", "date"),
                                                      ("PorcentajeDto", "real"), ("CanalPromocion", "string")])
in_orden = entrada("OrdenVenta", "OrdenVenta.csv", [("OrdenID", "integer"), ("ClienteID", "integer"), ("TiendaID", "integer"),
                                                    ("FechaOrden", "datetime"), ("CanalVenta", "string"),
                                                    ("EstadoOrden", "string"), ("PromocionID", "integer")])
in_detalle = entrada("DetalleOrden", "DetalleOrden.csv", [("DetalleOrdenID", "integer"), ("OrdenID", "integer"),
                                                          ("ProductoID", "integer"), ("Cantidad", "integer"),
                                                          ("PrecioUnitario", "real"), ("DescuentoMonto", "real")])
in_pago = entrada("Pago", "Pago.csv", [("PagoID", "integer"), ("OrdenID", "integer"), ("FechaPago", "datetime"),
                                       ("MetodoPago", "string"), ("Monto", "real")])
in_devolucion = entrada("Devolucion", "Devolucion.csv", [("DevolucionID", "integer"), ("DetalleOrdenID", "integer"),
                                                         ("FechaDevolucion", "datetime"), ("CantidadDevuelta", "integer"),
                                                         ("Motivo", "string"), ("MontoReembolso", "real")])

FECHA_KEY = "YEAR([%s]) * 10000 + MONTH([%s]) * 100 + DAY([%s])"
CANAL_KEY = 'CASE [CanalVenta] WHEN "Tienda" THEN 1 WHEN "Web" THEN 2 WHEN "App" THEN 3 ELSE 0 END'
MOTIVO_KEY = ('CASE [Motivo] WHEN "Producto defectuoso" THEN 1 WHEN "Producto equivocado" THEN 2 '
              'WHEN "Cambio de opinion" THEN 3 WHEN "Danado en transporte" THEN 4 '
              'WHEN "Talla o presentacion" THEN 5 ELSE 0 END')
METODO_KEY = ('CASE [MetodoPago] WHEN "Efectivo" THEN 1 WHEN "Tarjeta credito" THEN 2 '
              'WHEN "Tarjeta debito" THEN 3 WHEN "Transferencia" THEN 4 '
              'WHEN "Billetera digital" THEN 5 ELSE 0 END')

# =====================================================================================
# DIMENSIONES
# =====================================================================================
j_prod_cat = join("Producto + Categoria", "CategoriaID", "CategoriaID", "inner", ["CategoriaID-1"])
j_prod_prov = join("Producto + Proveedor", "ProveedorID", "ProveedorID", "inner", ["ProveedorID-1"])
dim_producto = paso("DimProducto", [
    renombrar("NombreCategoria", "Categoria"),
    renombrar("NombreProveedor", "Proveedor"),
    renombrar("Pais", "PaisProveedor"),
    calc("ProductoKey", "[ProductoID]", "Clave subrogada del producto"),
    calc("RangoPrecio", 'IF [PrecioLista] < 800 THEN "Economico" ELSEIF [PrecioLista] < 1500 THEN "Medio" ELSE "Premium" END',
         "Clasificar el producto por rango de precio"),
    quitar(["CategoriaID", "ProveedorID", "FechaAlta"]),
])
out_producto = salida("Salida DimProducto", "DimProducto.csv")

dim_cliente = paso("DimCliente", [
    calc("ClienteKey", "[ClienteID]", "Clave subrogada del cliente"),
    calc("NombreCompleto", '[Nombre] + " " + [Apellido]', "Unir nombre y apellido"),
    calc("Sexo", 'IFNULL([Sexo], "No especificado")', "Reemplazar sexo nulo"),
    calc("GrupoEdad", ('IF DATEDIFF("year", [FechaNacimiento], TODAY()) < 30 THEN "Menor de 30" '
                       'ELSEIF DATEDIFF("year", [FechaNacimiento], TODAY()) < 45 THEN "30 a 44" '
                       'ELSEIF DATEDIFF("year", [FechaNacimiento], TODAY()) < 60 THEN "45 a 59" '
                       'ELSE "60 o mas" END'), "Derivar grupo de edad"),
    calc("AnioRegistro", "YEAR([FechaRegistro])", "Derivar año de registro"),
    quitar(["Nombre", "Apellido", "FechaNacimiento", "FechaRegistro"]),
])
out_cliente = salida("Salida DimCliente", "DimCliente.csv")

dim_tienda = paso("DimTienda", [
    calc("TiendaKey", "[TiendaID]", "Clave subrogada de la tienda"),
    calc("AnioApertura", "YEAR([FechaApertura])", "Derivar año de apertura"),
    quitar(["FechaApertura"]),
])
out_tienda = salida("Salida DimTienda", "DimTienda.csv")

dim_promocion = paso("DimPromocion", [
    calc("PromocionKey", "[PromocionID]", "Clave subrogada de la promoción"),
])
out_promocion = salida("Salida DimPromocion", "DimPromocion.csv")

agg_canal = agregar("Canales distintos", ["CanalVenta"], [("OrdenID", "COUNT", "Ordenes")])
dim_canal = paso("DimCanal", [
    calc("CanalKey", CANAL_KEY, "Asignar clave al canal"),
    quitar(["Ordenes"]),
])
out_canal = salida("Salida DimCanal", "DimCanal.csv")

agg_motivo = agregar("Motivos distintos", ["Motivo"], [("DevolucionID", "COUNT", "Devoluciones")])
dim_motivo = paso("DimMotivoDevolucion", [
    calc("MotivoKey", MOTIVO_KEY, "Asignar clave al motivo"),
    quitar(["Devoluciones"]),
])
out_motivo = salida("Salida DimMotivoDevolucion", "DimMotivoDevolucion.csv")

agg_metodo = agregar("Metodos de pago distintos", ["MetodoPago"], [("PagoID", "COUNT", "Pagos")])
dim_metodo = paso("DimMetodoPago", [
    calc("MetodoPagoKey", METODO_KEY, "Asignar clave al método de pago"),
    quitar(["Pagos"]),
])
out_metodo = salida("Salida DimMetodoPago", "DimMetodoPago.csv")

# =====================================================================================
# HECHOS
# =====================================================================================
limpieza_orden = paso("Filtrar ordenes completadas", [
    filtro('[EstadoOrden] = "Completada"', "Mantener solo ordenes completadas"),
    calc("FechaKey", FECHA_KEY % ("FechaOrden", "FechaOrden", "FechaOrden"), "Derivar FechaKey de la venta"),
    calc("ClienteKey", "IFNULL([ClienteID], -1)", "Cliente no identificado como -1"),
    calc("PromocionKey", "IFNULL([PromocionID], -1)", "Sin promoción como -1"),
    calc("CanalKey", CANAL_KEY, "Asignar clave al canal"),
    calc("TiendaKey", "[TiendaID]", "Clave de la tienda"),
    quitar(["ClienteID", "PromocionID", "TiendaID", "EstadoOrden", "CanalVenta"]),
])

j_venta = join("Detalle + Orden", "OrdenID", "OrdenID", "inner", ["OrdenID-1"])
j_venta_prod = join("Ventas + Producto", "ProductoID", "ProductoID", "inner", ["ProductoID-1"])
fact_ventas = paso("FactVentas", [
    calc("VentaKey", "[DetalleOrdenID]", "Clave del hecho"),
    calc("CantidadVendida", "[Cantidad]", "Renombrar la medida de cantidad"),
    calc("MontoBruto", "ROUND([Cantidad] * [PrecioUnitario], 2)", "Medida: monto bruto"),
    calc("MontoNeto", "ROUND([MontoBruto] - [DescuentoMonto], 2)", "Medida: monto neto"),
    calc("CostoTotal", "ROUND([Cantidad] * [CostoUnitario], 2)", "Medida: costo total"),
    calc("MargenBruto", "ROUND([MontoNeto] - [CostoTotal], 2)", "Medida: margen bruto"),
    quitar(["DetalleOrdenID", "ProductoID", "Cantidad", "SKU", "NombreProducto", "Marca", "Categoria",
            "Proveedor", "PaisProveedor", "CostoUnitario", "PrecioLista", "RangoPrecio", "FechaLanzamiento",
            "Activo", "FechaOrden"], "Eliminar columnas del catálogo"),
])
out_ventas = salida("Salida FactVentas", "FactVentas.csv")

j_dev_det = join("Devolucion + Detalle", "DetalleOrdenID", "DetalleOrdenID", "inner", ["DetalleOrdenID-1"])
j_dev_orden = join("Devoluciones + Orden", "OrdenID", "OrdenID", "inner", ["OrdenID-1"])
fact_devoluciones = paso("FactDevoluciones", [
    calc("DevolucionKey", "[DevolucionID]", "Clave del hecho"),
    calc("FechaKeyDevolucion", FECHA_KEY % ("FechaDevolucion", "FechaDevolucion", "FechaDevolucion"),
         "Derivar FechaKey de la devolución"),
    calc("MotivoKey", MOTIVO_KEY, "Asignar clave al motivo de devolución"),
    quitar(["DevolucionID", "ProductoID", "FechaDevolucion", "Cantidad", "PrecioUnitario", "DescuentoMonto",
            "FechaKey", "PromocionKey", "CanalKey", "FechaOrden", "OrdenID", "SKU", "NombreProducto", "Marca",
            "Categoria", "Proveedor", "PaisProveedor", "CostoUnitario", "PrecioLista", "RangoPrecio",
            "FechaLanzamiento", "Activo", "Motivo"], "Eliminar columnas de la venta y del catálogo"),
    renombrar("FechaKeyDevolucion", "FechaKey"),
])
out_devoluciones = salida("Salida FactDevoluciones", "FactDevoluciones.csv")

j_pago_orden = join("Pago + Orden", "OrdenID", "OrdenID", "inner", ["OrdenID-1"])
fact_pagos = paso("FactPagos", [
    calc("PagoKey", "[PagoID]", "Clave del hecho"),
    calc("FechaKeyPago", FECHA_KEY % ("FechaPago", "FechaPago", "FechaPago"), "Derivar FechaKey del pago"),
    calc("MetodoPagoKey", METODO_KEY, "Asignar clave al método de pago"),
    calc("MontoPagado", "[Monto]", "Renombrar la medida"),
    quitar(["PagoID", "Monto", "FechaPago", "MetodoPago", "FechaKey", "PromocionKey", "FechaOrden"],
           "Eliminar columnas no usadas"),
    renombrar("FechaKeyPago", "FechaKey"),
])
out_pagos = salida("Salida FactPagos", "FactPagos.csv")

# =====================================================================================
# CONEXIONES DEL FLUJO
# =====================================================================================
link(in_producto, j_prod_cat, "Left"); link(in_categoria, j_prod_cat, "Right")
link(j_prod_cat, j_prod_prov, "Left"); link(in_proveedor, j_prod_prov, "Right")
link(j_prod_prov, dim_producto); link(dim_producto, out_producto)

link(in_cliente, dim_cliente); link(dim_cliente, out_cliente)
link(in_tienda, dim_tienda); link(dim_tienda, out_tienda)
link(in_promocion, dim_promocion); link(dim_promocion, out_promocion)

link(in_orden, agg_canal); link(agg_canal, dim_canal); link(dim_canal, out_canal)
link(in_devolucion, agg_motivo); link(agg_motivo, dim_motivo); link(dim_motivo, out_motivo)
link(in_pago, agg_metodo); link(agg_metodo, dim_metodo); link(dim_metodo, out_metodo)

link(in_orden, limpieza_orden)
link(in_detalle, j_venta, "Left"); link(limpieza_orden, j_venta, "Right")
link(j_venta, j_venta_prod, "Left"); link(dim_producto, j_venta_prod, "Right")
link(j_venta_prod, fact_ventas); link(fact_ventas, out_ventas)

link(in_devolucion, j_dev_det, "Left"); link(j_venta_prod, j_dev_det, "Right")
link(j_dev_det, fact_devoluciones); link(fact_devoluciones, out_devoluciones)

link(in_pago, j_pago_orden, "Left"); link(limpieza_orden, j_pago_orden, "Right")
link(j_pago_orden, fact_pagos); link(fact_pagos, out_pagos)

nodos = [in_categoria, in_proveedor, in_producto, in_tienda, in_cliente, in_promocion, in_orden, in_detalle,
         in_pago, in_devolucion, j_prod_cat, j_prod_prov, dim_producto, out_producto, dim_cliente, out_cliente,
         dim_tienda, out_tienda, dim_promocion, out_promocion, agg_canal, dim_canal, out_canal,
         agg_motivo, dim_motivo, out_motivo, agg_metodo, dim_metodo, out_metodo, limpieza_orden,
         j_venta, j_venta_prod, fact_ventas, out_ventas, j_dev_det, fact_devoluciones, out_devoluciones,
         j_pago_orden, fact_pagos, out_pagos]

AZUL, VERDE, NARANJA, MORADO, ROJO = "#3D7FA6", "#499893", "#F6A035", "#845578", "#CD677F"
POS = [
    (in_producto, 0, 0, AZUL), (in_categoria, 0, 1, AZUL), (in_proveedor, 0, 2, AZUL),
    (j_prod_cat, 1, 0, AZUL), (j_prod_prov, 2, 0, AZUL), (dim_producto, 3, 0, AZUL), (out_producto, 4, 0, NARANJA),
    (in_cliente, 0, 3, VERDE), (dim_cliente, 1, 3, VERDE), (out_cliente, 2, 3, NARANJA),
    (in_tienda, 0, 4, VERDE), (dim_tienda, 1, 4, VERDE), (out_tienda, 2, 4, NARANJA),
    (in_promocion, 0, 5, VERDE), (dim_promocion, 1, 5, VERDE), (out_promocion, 2, 5, NARANJA),
    (in_orden, 0, 6, MORADO), (agg_canal, 1, 6, MORADO), (dim_canal, 2, 6, MORADO), (out_canal, 3, 6, NARANJA),
    (in_devolucion, 0, 7, ROJO), (agg_motivo, 1, 7, ROJO), (dim_motivo, 2, 7, ROJO), (out_motivo, 3, 7, NARANJA),
    (in_pago, 0, 8, ROJO), (agg_metodo, 1, 8, ROJO), (dim_metodo, 2, 8, ROJO), (out_metodo, 3, 8, NARANJA),
    (limpieza_orden, 1, 9, MORADO), (in_detalle, 0, 10, MORADO), (j_venta, 2, 10, MORADO),
    (j_venta_prod, 3, 10, MORADO), (fact_ventas, 4, 10, MORADO), (out_ventas, 5, 10, NARANJA),
    (j_dev_det, 4, 11, ROJO), (fact_devoluciones, 5, 11, ROJO), (out_devoluciones, 6, 11, NARANJA),
    (j_pago_orden, 2, 12, ROJO), (fact_pagos, 3, 12, ROJO), (out_pagos, 4, 12, NARANJA),
]

flow = {"parameters": {"parameters": {}},
        "initialNodes": [n["id"] for n in nodos if n["baseType"] == "input"],
        "nodes": {n["id"]: n for n in nodos}, "connections": conns, "dataConnections": {},
        "connectionIds": list(conns), "dataConnectionIds": [], "nodeProperties": {}, "extensibility": None,
        "selection": [], "majorVersion": 1, "minorVersion": 2, "documentId": nid()}


def color(h):
    return {"hexCss": h, "rgba": [str(int(h[i:i + 2], 16)) for i in (1, 3, 5)] + ["1"]}


disp = {"majorVersion": 1, "minorVersion": 0,
        "fieldOrder": {"fieldOrdinals": {}, "minOrdinal": 0, "maxOrdinal": 0},
        "flowDisplaySettings": {"flowGroupNodeDisplay": {},
                                "flowSelection": {"type": "nothing", "selectedNodePath": None, "selectedType": None},
                                "flowNodeDisplaySettings": {n["id"]: {"color": color(c), "position": {"x": x, "y": y},
                                                                      "size": {"width": 1, "height": 1}}
                                                            for n, x, y, c in POS}},
        "hiddenColumns": []}

os.makedirs(SALIDA, exist_ok=True)
with zipfile.ZipFile(TFL, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("flow", json.dumps(flow, indent=2))
    z.writestr("displaySettings", json.dumps(disp, indent=2))
    z.writestr("maestroMetadata", open(META).read())
print("Flujo generado:", TFL)
print("Nodos:", len(nodos), "| entradas:", sum(1 for n in nodos if n["baseType"] == "input"),
      "| salidas:", sum(1 for n in nodos if n["baseType"] == "output"))
