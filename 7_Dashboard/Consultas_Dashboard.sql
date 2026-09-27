/*
===============================================================================
 ICC-321 Inteligencia de Negocios, Práctica 1
 Actividad 7: consultas que alimentan el dashboard

 Estudiantes: Elías De La Cruz (ID 10155971), Enger Douglas (ID 10144675)
 Base: DW_Retail (no se consulta la base operacional)

 Cada bloque "-- @tabla" produce una tabla del extracto de Tableau
 (Dashboard_DW_Retail.hyper). Las consultas solo unen hechos con sus
 dimensiones y agregan; ninguna medida se recalcula desde el origen.
 Las etiquetas de categoría y promoción se escriben con tilde para que
 se lean bien en el tablero.
===============================================================================
*/

USE DW_Retail;

-- @tabla Ventas
/* Grano: una línea de orden completada (el mismo de FactVentas). */
SELECT
    f.VentaKey,
    f.OrdenID,
    d.Fecha,
    d.Anio,
    d.Trimestre,
    d.Mes,
    d.NombreMes,
    CASE p.Categoria
        WHEN 'Bebes'             THEN N'Bebés'
        WHEN 'Electrodomesticos' THEN N'Electrodomésticos'
        WHEN 'Papeleria'         THEN N'Papelería'
        WHEN 'Tecnologia'        THEN N'Tecnología'
        ELSE p.Categoria
    END                                        AS Categoria,
    p.Marca,
    p.Proveedor,
    p.PaisProveedor,
    p.NombreProducto,
    p.RangoPrecio,
    c.Segmento,
    c.Provincia                                AS ProvinciaCliente,
    t.NombreTienda,
    t.TipoTienda,
    t.Provincia                                AS ProvinciaTienda,
    ca.CanalVenta,
    REPLACE(REPLACE(pr.NombrePromocion, 'Valentin', N'Valentín'),
            'Sin promocion', N'Sin promoción') AS Promocion,
    CASE WHEN f.PromocionKey = -1 THEN N'Sin promoción'
         ELSE N'Con promoción' END            AS TipoVenta,
    /* La campaña agrupa las ediciones de cada año de una misma promoción */
    CASE WHEN f.PromocionKey = -1 THEN N'Sin promoción'
         ELSE REPLACE(LEFT(pr.NombrePromocion, LEN(pr.NombrePromocion) - 5), 'Valentin', N'Valentín')
              + N' (' + CAST(CAST(pr.PorcentajeDto AS int) AS nvarchar(3)) + N' %)'
    END                                        AS Campana,
    pr.PorcentajeDto,
    f.CantidadVendida,
    f.MontoBruto,
    f.DescuentoMonto,
    f.MontoNeto,
    f.CostoTotal,
    f.MargenBruto
FROM dbo.FactVentas f
JOIN dbo.DimFecha     d  ON d.FechaKey     = f.FechaKey
JOIN dbo.DimProducto  p  ON p.ProductoKey  = f.ProductoKey
JOIN dbo.DimCliente   c  ON c.ClienteKey   = f.ClienteKey
JOIN dbo.DimTienda    t  ON t.TiendaKey    = f.TiendaKey
JOIN dbo.DimPromocion pr ON pr.PromocionKey = f.PromocionKey
JOIN dbo.DimCanal     ca ON ca.CanalKey    = f.CanalKey;

-- @tabla RentabilidadProducto
/* Consulta entre hechos (drill-across): FactVentas y FactDevoluciones se
   agregan por separado al mismo nivel, año y producto, y se unen por sus
   dimensiones conformadas. Así el reembolso se resta del margen sin
   duplicar ninguna de las dos medidas. Las ventas se ubican en el año de
   la venta y las devoluciones en el año de la devolución. */
WITH v AS (
    SELECT d.Anio, f.ProductoKey,
           SUM(f.MontoNeto)       AS MontoNeto,
           SUM(f.CostoTotal)      AS CostoTotal,
           SUM(f.MargenBruto)     AS MargenBruto,
           COUNT(*)               AS LineasVendidas,
           SUM(f.CantidadVendida) AS UnidadesVendidas
    FROM dbo.FactVentas f
    JOIN dbo.DimFecha d ON d.FechaKey = f.FechaKey
    GROUP BY d.Anio, f.ProductoKey
),
dv AS (
    SELECT d.Anio, f.ProductoKey,
           COUNT(*)                AS Devoluciones,
           SUM(f.CantidadDevuelta) AS UnidadesDevueltas,
           SUM(f.MontoReembolso)   AS MontoReembolso
    FROM dbo.FactDevoluciones f
    JOIN dbo.DimFecha d ON d.FechaKey = f.FechaKey
    GROUP BY d.Anio, f.ProductoKey
)
SELECT
    COALESCE(v.Anio, dv.Anio)                  AS Anio,
    CASE p.Categoria
        WHEN 'Bebes'             THEN N'Bebés'
        WHEN 'Electrodomesticos' THEN N'Electrodomésticos'
        WHEN 'Papeleria'         THEN N'Papelería'
        WHEN 'Tecnologia'        THEN N'Tecnología'
        ELSE p.Categoria
    END                                        AS Categoria,
    p.Marca,
    p.Proveedor,
    p.PaisProveedor,
    p.NombreProducto,
    ISNULL(v.MontoNeto, 0)          AS MontoNeto,
    ISNULL(v.CostoTotal, 0)         AS CostoTotal,
    ISNULL(v.MargenBruto, 0)        AS MargenBruto,
    ISNULL(v.LineasVendidas, 0)     AS LineasVendidas,
    ISNULL(v.UnidadesVendidas, 0)   AS UnidadesVendidas,
    ISNULL(dv.Devoluciones, 0)      AS Devoluciones,
    ISNULL(dv.UnidadesDevueltas, 0) AS UnidadesDevueltas,
    ISNULL(dv.MontoReembolso, 0)    AS MontoReembolso
FROM v
FULL JOIN dv ON dv.Anio = v.Anio AND dv.ProductoKey = v.ProductoKey
JOIN dbo.DimProducto p ON p.ProductoKey = COALESCE(v.ProductoKey, dv.ProductoKey);
