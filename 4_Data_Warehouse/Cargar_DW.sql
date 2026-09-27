/*
===============================================================================
 ICC-321 Inteligencia de Negocios — Práctica 1
 Carga del Data Warehouse con la salida del flujo de Tableau Prep

 Estudiante: Enger Douglas (ID 10144675)

 Requisito previo: haber ejecutado DW_Retail.sql (crea la base y DimFecha)
 y el flujo ETL_DW_Retail.tfl (genera los CSV en la carpeta salida_dw).

 Los CSV se cargan en tablas temporales de staging, porque Tableau Prep
 escribe las columnas en orden alfabético, y de ahí se insertan en las tablas
 definitivas con el tipo de dato correcto.
===============================================================================
*/

USE DW_Retail;
GO

SET NOCOUNT ON;

/* Las tablas de hechos se vacían primero por las claves foráneas */
DELETE FROM dbo.FactVentas;
DELETE FROM dbo.FactDevoluciones;
DELETE FROM dbo.FactPagos;
DELETE FROM dbo.DimProducto;
DELETE FROM dbo.DimTienda;
DELETE FROM dbo.DimCanal;
DELETE FROM dbo.DimMotivoDevolucion;
DELETE FROM dbo.DimMetodoPago;
DELETE FROM dbo.DimCliente     WHERE ClienteKey   <> -1;   -- se conserva «No identificado»
DELETE FROM dbo.DimPromocion   WHERE PromocionKey <> -1;   -- se conserva «Sin promocion»
GO

/* =========================================================================
   DIMENSIONES
   ========================================================================= */

CREATE TABLE #DimProducto (Activo varchar(10), Categoria varchar(80), CostoUnitario varchar(30),
    FechaLanzamiento varchar(30), Marca varchar(60), NombreProducto varchar(120), PaisProveedor varchar(60),
    PrecioLista varchar(30), ProductoID varchar(20), ProductoKey varchar(20), Proveedor varchar(120),
    RangoPrecio varchar(20), SKU varchar(20));
BULK INSERT #DimProducto FROM '/datos/DimProducto.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimProducto (ProductoKey, ProductoID, SKU, NombreProducto, Marca, Categoria, Proveedor,
                             PaisProveedor, CostoUnitario, PrecioLista, RangoPrecio, FechaLanzamiento, Activo)
SELECT CAST(ProductoKey AS int), CAST(ProductoID AS int), SKU, NombreProducto, Marca, Categoria, Proveedor,
       PaisProveedor, CAST(CostoUnitario AS decimal(12,2)), CAST(PrecioLista AS decimal(12,2)), RangoPrecio,
       CAST(FechaLanzamiento AS date), CAST(CAST(Activo AS int) AS bit)
FROM #DimProducto;

CREATE TABLE #DimCliente (AnioRegistro varchar(10), Ciudad varchar(80), ClienteID varchar(20), ClienteKey varchar(20),
    GrupoEdad varchar(20), NombreCompleto varchar(130), Provincia varchar(80), Segmento varchar(30), Sexo varchar(20));
BULK INSERT #DimCliente FROM '/datos/DimCliente.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimCliente (ClienteKey, ClienteID, NombreCompleto, Sexo, GrupoEdad, Ciudad, Provincia, Segmento, AnioRegistro)
SELECT CAST(ClienteKey AS int), CAST(ClienteID AS int), NombreCompleto, Sexo, GrupoEdad, Ciudad, Provincia,
       Segmento, CAST(NULLIF(AnioRegistro,'') AS smallint)
FROM #DimCliente;

CREATE TABLE #DimTienda (AnioApertura varchar(10), Ciudad varchar(80), NombreTienda varchar(100),
    Provincia varchar(80), TiendaID varchar(20), TiendaKey varchar(20), TipoTienda varchar(30));
BULK INSERT #DimTienda FROM '/datos/DimTienda.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimTienda (TiendaKey, TiendaID, NombreTienda, Ciudad, Provincia, TipoTienda, AnioApertura)
SELECT CAST(TiendaKey AS int), CAST(TiendaID AS int), NombreTienda, Ciudad, Provincia, TipoTienda,
       CAST(AnioApertura AS smallint)
FROM #DimTienda;

CREATE TABLE #DimPromocion (CanalPromocion varchar(20), FechaFin varchar(30), FechaInicio varchar(30),
    NombrePromocion varchar(100), PorcentajeDto varchar(20), PromocionID varchar(20), PromocionKey varchar(20));
BULK INSERT #DimPromocion FROM '/datos/DimPromocion.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimPromocion (PromocionKey, PromocionID, NombrePromocion, PorcentajeDto, CanalPromocion, FechaInicio, FechaFin)
SELECT CAST(PromocionKey AS int), CAST(PromocionID AS int), NombrePromocion, CAST(PorcentajeDto AS decimal(5,2)),
       CanalPromocion, CAST(FechaInicio AS date), CAST(FechaFin AS date)
FROM #DimPromocion;

CREATE TABLE #DimCanal (CanalKey varchar(20), CanalVenta varchar(20));
BULK INSERT #DimCanal FROM '/datos/DimCanal.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimCanal (CanalKey, CanalVenta) SELECT CAST(CanalKey AS int), CanalVenta FROM #DimCanal;

CREATE TABLE #DimMotivo (Motivo varchar(50), MotivoKey varchar(20));
BULK INSERT #DimMotivo FROM '/datos/DimMotivoDevolucion.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimMotivoDevolucion (MotivoKey, Motivo) SELECT CAST(MotivoKey AS int), Motivo FROM #DimMotivo;

CREATE TABLE #DimMetodoPago (MetodoPago varchar(30), MetodoPagoKey varchar(20));
BULK INSERT #DimMetodoPago FROM '/datos/DimMetodoPago.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.DimMetodoPago (MetodoPagoKey, MetodoPago) SELECT CAST(MetodoPagoKey AS int), MetodoPago FROM #DimMetodoPago;
GO

/* =========================================================================
   HECHOS
   ========================================================================= */

CREATE TABLE #FactVentas (CanalKey varchar(20), CantidadVendida varchar(20), ClienteKey varchar(20),
    CostoTotal varchar(30), DescuentoMonto varchar(30), FechaKey varchar(20), MargenBruto varchar(30),
    MontoBruto varchar(30), MontoNeto varchar(30), OrdenID varchar(20), PrecioUnitario varchar(30),
    ProductoKey varchar(20), PromocionKey varchar(20), TiendaKey varchar(20), VentaKey varchar(20));
BULK INSERT #FactVentas FROM '/datos/FactVentas.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a', BATCHSIZE=20000);
INSERT INTO dbo.FactVentas (VentaKey, FechaKey, ProductoKey, ClienteKey, TiendaKey, PromocionKey, CanalKey,
                            OrdenID, CantidadVendida, PrecioUnitario, MontoBruto, DescuentoMonto, MontoNeto,
                            CostoTotal, MargenBruto)
SELECT CAST(VentaKey AS bigint), CAST(FechaKey AS int), CAST(ProductoKey AS int), CAST(ClienteKey AS int),
       CAST(TiendaKey AS int), CAST(PromocionKey AS int), CAST(CanalKey AS int), CAST(OrdenID AS bigint),
       CAST(CantidadVendida AS int), CAST(PrecioUnitario AS decimal(12,2)), CAST(MontoBruto AS decimal(14,2)),
       CAST(DescuentoMonto AS decimal(14,2)), CAST(MontoNeto AS decimal(14,2)), CAST(CostoTotal AS decimal(14,2)),
       CAST(MargenBruto AS decimal(14,2))
FROM #FactVentas;

CREATE TABLE #FactDevoluciones (CantidadDevuelta varchar(20), ClienteKey varchar(20), DetalleOrdenID varchar(20),
    DevolucionKey varchar(20), FechaKey varchar(20), MontoReembolso varchar(30), MotivoKey varchar(20),
    ProductoKey varchar(20), TiendaKey varchar(20));
BULK INSERT #FactDevoluciones FROM '/datos/FactDevoluciones.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a');
INSERT INTO dbo.FactDevoluciones (DevolucionKey, FechaKey, ProductoKey, ClienteKey, TiendaKey, MotivoKey,
                                  DetalleOrdenID, CantidadDevuelta, MontoReembolso)
SELECT CAST(DevolucionKey AS bigint), CAST(FechaKey AS int), CAST(ProductoKey AS int), CAST(ClienteKey AS int),
       CAST(TiendaKey AS int), CAST(MotivoKey AS int), CAST(DetalleOrdenID AS bigint),
       CAST(CantidadDevuelta AS int), CAST(MontoReembolso AS decimal(14,2))
FROM #FactDevoluciones;

CREATE TABLE #FactPagos (CanalKey varchar(20), ClienteKey varchar(20), FechaKey varchar(20),
    MetodoPagoKey varchar(20), MontoPagado varchar(30), OrdenID varchar(20), PagoKey varchar(20), TiendaKey varchar(20));
BULK INSERT #FactPagos FROM '/datos/FactPagos.csv'
    WITH (FORMAT='CSV', FIRSTROW=2, FIELDTERMINATOR=',', ROWTERMINATOR='0x0a', BATCHSIZE=20000);
INSERT INTO dbo.FactPagos (PagoKey, FechaKey, ClienteKey, TiendaKey, CanalKey, MetodoPagoKey, OrdenID, MontoPagado)
SELECT CAST(PagoKey AS bigint), CAST(FechaKey AS int), CAST(ClienteKey AS int), CAST(TiendaKey AS int),
       CAST(CanalKey AS int), CAST(MetodoPagoKey AS int), CAST(OrdenID AS bigint), CAST(MontoPagado AS decimal(14,2))
FROM #FactPagos;
GO

/* =========================================================================
   VERIFICACIÓN DE LA CARGA
   ========================================================================= */

SELECT 'DimFecha' AS Tabla, COUNT(*) AS Filas FROM dbo.DimFecha
UNION ALL SELECT 'DimProducto', COUNT(*) FROM dbo.DimProducto
UNION ALL SELECT 'DimCliente', COUNT(*) FROM dbo.DimCliente
UNION ALL SELECT 'DimTienda', COUNT(*) FROM dbo.DimTienda
UNION ALL SELECT 'DimPromocion', COUNT(*) FROM dbo.DimPromocion
UNION ALL SELECT 'DimCanal', COUNT(*) FROM dbo.DimCanal
UNION ALL SELECT 'DimMotivoDevolucion', COUNT(*) FROM dbo.DimMotivoDevolucion
UNION ALL SELECT 'DimMetodoPago', COUNT(*) FROM dbo.DimMetodoPago
UNION ALL SELECT 'FactVentas', COUNT(*) FROM dbo.FactVentas
UNION ALL SELECT 'FactDevoluciones', COUNT(*) FROM dbo.FactDevoluciones
UNION ALL SELECT 'FactPagos', COUNT(*) FROM dbo.FactPagos;

SELECT CAST(SUM(MontoNeto) AS decimal(18,2)) AS VentaNeta,
       CAST(SUM(MargenBruto) AS decimal(18,2)) AS MargenBruto,
       SUM(CantidadVendida) AS Unidades,
       CAST(100.0 * SUM(MargenBruto) / SUM(MontoNeto) AS decimal(5,2)) AS MargenPct
FROM dbo.FactVentas;
GO
