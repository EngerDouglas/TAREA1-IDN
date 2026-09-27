"""Genera el extracto de Tableau que usa el dashboard de la actividad 7.

Ejecuta las consultas de 7_Dashboard/Consultas_Dashboard.sql sobre DW_Retail
y guarda cada resultado como una tabla del esquema Extract de un archivo .hyper.
Con el extracto, el libro de Tableau se abre sin acceso al servidor, pero sus
datos siguen saliendo del Data Warehouse.

Requisitos:  pip install pymssql tableauhyperapi
Conexión:    variables DW_SERVIDOR (por defecto localhost), DW_USUARIO (sa)
             y DW_CLAVE.
Uso:         python3 generar_extracto_dashboard.py
Salida:      7_Dashboard/Dashboard_DW_Retail.hyper
"""
import datetime
import decimal
import os
import re

import pymssql
from tableauhyperapi import (Connection, CreateMode, HyperProcess, Inserter, SqlType,
                             TableDefinition, TableName, Telemetry)

BASE = os.path.dirname(os.path.abspath(__file__))
TAREA = os.path.dirname(BASE)
SQL = os.path.join(TAREA, "7_Dashboard", "Consultas_Dashboard.sql")
HYPER = os.path.join(TAREA, "7_Dashboard", "Dashboard_DW_Retail.hyper")


def bloques(texto):
    """Devuelve (tabla, consulta) por cada marca '-- @tabla' del archivo."""
    partes = re.split(r"^-- @tabla (\w+)\s*$", texto, flags=re.M)
    return [(partes[i], partes[i + 1].strip().rstrip(";")) for i in range(1, len(partes), 2)]


def tipo_hyper(valores):
    """Tipo de columna según los valores devueltos por SQL Server."""
    muestra = next((v for v in valores if v is not None), "")
    if isinstance(muestra, bool):
        return SqlType.bool()
    if isinstance(muestra, int):
        return SqlType.big_int()
    if isinstance(muestra, (decimal.Decimal, float)):
        return SqlType.double()
    if isinstance(muestra, datetime.date):
        return SqlType.date()
    return SqlType.text()


def normalizar(v):
    return float(v) if isinstance(v, decimal.Decimal) else v


def main():
    with open(SQL, encoding="utf-8") as f:
        consultas = bloques(f.read())

    origen = pymssql.connect(server=os.environ.get("DW_SERVIDOR", "localhost"),
                             user=os.environ.get("DW_USUARIO", "sa"),
                             password=os.environ["DW_CLAVE"], database="DW_Retail")
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper, \
            Connection(hyper.endpoint, HYPER, CreateMode.CREATE_AND_REPLACE) as destino:
        destino.catalog.create_schema("Extract")
        for tabla, consulta in consultas:
            cur = origen.cursor()
            cur.execute(consulta)
            filas = cur.fetchall()
            nombres = [c[0] for c in cur.description]
            columnas = [TableDefinition.Column(n, tipo_hyper([f[i] for f in filas]))
                        for i, n in enumerate(nombres)]
            definicion = TableDefinition(TableName("Extract", tabla), columnas)
            destino.catalog.create_table(definicion)
            with Inserter(destino, definicion) as ins:
                ins.add_rows([normalizar(v) for v in f] for f in filas)
                ins.execute()
            print("%-22s %7d filas" % (tabla, len(filas)))
    origen.close()
    print("Extracto:", HYPER)


if __name__ == "__main__":
    main()
