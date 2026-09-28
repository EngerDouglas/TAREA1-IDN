"""Genera los diagramas del documento como archivos .drawio.

El esquema estrella usa la tabla del paquete Entity Relation de draw.io (filas
con columna PK/FK) y conectores de notación de pata de gallo. La arquitectura usa
las formas estándar de draw.io. Se exportan a PNG con draw.io desktop:
    drawio -x -f png -s 2 -o estrella.png estrella.drawio
"""
from xml.sax.saxutils import escape

TABLA = ("shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;"
         "rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;")
HECHO = TABLA.replace("fillColor=#dae8fc;strokeColor=#6c8ebf;", "fillColor=#fff2cc;strokeColor=#d6b656;")
FILA = ("shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;"
        "dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=%d;")
CELDA = ("shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;%s"
         "overflow=hidden;whiteSpace=wrap;html=1;")
RELACION = ("edgeStyle=entityRelationEdgeStyle;fontSize=12;html=1;endArrow=ERmany;startArrow=ERmandOne;"
            "endFill=0;startFill=0;strokeColor=#6c8ebf;")


class Diagrama:
    def __init__(self):
        self.celdas = []
        self.n = 2

    def id(self):
        self.n += 1
        return "c%d" % self.n

    def tabla(self, nombre, x, y, filas, ancho=240, estilo=TABLA):
        """filas: lista de (marca, texto) con marca 'PK', 'FK' o ''."""
        tid = self.id()
        self.filas = {}
        alto_fila = 26
        self.celdas.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                           '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                           % (tid, escape(nombre), estilo, x, y, ancho, 30 + alto_fila * len(filas)))
        for i, (marca, texto) in enumerate(filas):
            fid = self.id()
            ultima_clave = marca == "PK" and (i + 1 == len(filas) or filas[i + 1][0] != "PK")
            self.celdas.append('<mxCell id="%s" value="" style="%s" vertex="1" parent="%s">'
                               '<mxGeometry y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                               % (fid, FILA % (1 if ultima_clave else 0), tid, 30 + i * alto_fila, ancho, alto_fila))
            self.filas[texto] = fid
            negrita = "fontStyle=1;" if marca == "PK" else ""
            self.celdas.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">'
                               '<mxGeometry width="30" height="%d" as="geometry"><mxRectangle width="30" height="%d" as="alternateBounds"/></mxGeometry></mxCell>'
                               % (self.id(), marca, CELDA % negrita, fid, alto_fila, alto_fila))
            self.celdas.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">'
                               '<mxGeometry x="30" width="%d" height="%d" as="geometry"><mxRectangle width="%d" height="%d" as="alternateBounds"/></mxGeometry></mxCell>'
                               % (self.id(), escape(texto), CELDA % (negrita + "align=left;spacingLeft=6;"), fid,
                                  ancho - 30, alto_fila, ancho - 30, alto_fila))
        self.pk = self.filas.get(filas[0][1], tid)
        return self.pk if estilo == TABLA else tid

    def forma(self, texto, x, y, w, h, estilo):
        i = self.id()
        self.celdas.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                           '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                           % (i, escape(texto), estilo, x, y, w, h))
        return i

    def flecha(self, a, b, estilo):
        self.celdas.append('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">'
                           '<mxGeometry relative="1" as="geometry"/></mxCell>' % (self.id(), estilo, a, b))

    def guardar(self, archivo):
        with open(archivo, "w", encoding="utf-8") as f:
            f.write('<mxfile host="drawio"><diagram name="Página-1"><mxGraphModel grid="0" page="0">'
                    '<root><mxCell id="0"/><mxCell id="1" parent="0"/>%s</root></mxGraphModel>'
                    '</diagram></mxfile>' % "".join(self.celdas))


def estrella():
    d = Diagrama()
    fecha = d.tabla("DimFecha", 0, 0, [("PK", "FechaKey"), ("", "Fecha"), ("", "Anio, Trimestre"),
                                       ("", "Mes, NombreMes"), ("", "SemanaAnio"),
                                       ("", "DiaSemana, NombreDiaSemana"), ("", "EsFinDeSemana")])
    prod = d.tabla("DimProducto", 0, 260, [("PK", "ProductoKey"), ("", "ProductoID, SKU"),
                                           ("", "NombreProducto, Marca"), ("", "Categoria"),
                                           ("", "Proveedor, PaisProveedor"), ("", "CostoUnitario, PrecioLista"),
                                           ("", "RangoPrecio, Activo")])
    cli = d.tabla("DimCliente", 0, 520, [("PK", "ClienteKey"), ("", "ClienteID"), ("", "NombreCompleto, Sexo"),
                                         ("", "GrupoEdad"), ("", "Ciudad, Provincia"), ("", "Segmento, AnioRegistro")])
    tienda = d.tabla("DimTienda", 760, 20, [("PK", "TiendaKey"), ("", "TiendaID, NombreTienda"),
                                            ("", "Ciudad, Provincia"), ("", "TipoTienda"), ("", "AnioApertura")])
    promo = d.tabla("DimPromocion", 760, 270, [("PK", "PromocionKey"), ("", "PromocionID"), ("", "NombrePromocion"),
                                               ("", "PorcentajeDto"), ("", "CanalPromocion"),
                                               ("", "FechaInicio, FechaFin")])
    canal = d.tabla("DimCanal", 760, 560, [("PK", "CanalKey"), ("", "CanalVenta")])
    hecho = d.tabla("FactVentas", 380, 150, [("PK", "VentaKey"), ("FK", "FechaKey"), ("FK", "ProductoKey"),
                                             ("FK", "ClienteKey"), ("FK", "TiendaKey"), ("FK", "PromocionKey"),
                                             ("FK", "CanalKey"), ("", "OrdenID (degenerada)"),
                                             ("", "CantidadVendida"), ("", "PrecioUnitario"), ("", "MontoBruto"),
                                             ("", "DescuentoMonto"), ("", "MontoNeto"), ("", "CostoTotal"),
                                             ("", "MargenBruto")], ancho=220, estilo=HECHO)
    filas = d.filas
    for dim, fk in ((fecha, "FechaKey"), (prod, "ProductoKey"), (cli, "ClienteKey"),
                    (tienda, "TiendaKey"), (promo, "PromocionKey"), (canal, "CanalKey")):
        d.flecha(dim, filas[fk], RELACION)
    d.guardar("estrella.drawio")


def arquitectura():
    d = Diagrama()
    bd = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;"
          "fillColor=#dae8fc;strokeColor=#6c8ebf;")
    proc = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
    arch = "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;size=14;fillColor=#f5f5f5;strokeColor=#666666;"
    tab = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    flecha = "endArrow=block;endFill=1;html=1;strokeColor=#666666;"
    cajas = [d.forma("<b>BI_Practica_Retail</b><br>Base operacional<br>(SQL Server)", 0, 0, 150, 90, bd),
             d.forma("<b>CSV de origen</b><br>Extracción de<br>las 10 tablas", 200, 5, 140, 80, arch),
             d.forma("<b>Tableau Prep</b><br>Limpieza y<br>transformación", 390, 10, 140, 70, proc),
             d.forma("<b>DW_Retail</b><br>Modelo dimensional<br>(SQL Server)", 580, 0, 150, 90, bd),
             d.forma("<b>Tableau Desktop</b><br>Dashboard<br>interactivo", 780, 10, 140, 70, tab)]
    for a, b in zip(cajas, cajas[1:]):
        d.flecha(a, b, flecha)
    d.guardar("arquitectura.drawio")


if __name__ == "__main__":
    estrella()
    arquitectura()
