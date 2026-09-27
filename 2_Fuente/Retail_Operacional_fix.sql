/*
===============================================================================
 BASE DE DATOS: BI_Practica_Retail
 PROPÓSITO: Fuente operacional sintética para práctica de Inteligencia de Negocios
 MOTOR: Microsoft SQL Server
 NOTA: Este script ELIMINA y vuelve a crear la base de datos si ya existe.
===============================================================================
*/

USE master;
GO

IF DB_ID(N'BI_Practica_Retail') IS NOT NULL
BEGIN
    ALTER DATABASE BI_Practica_Retail SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE BI_Practica_Retail;
END;
GO

CREATE DATABASE BI_Practica_Retail;
GO

USE BI_Practica_Retail;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/* =========================
   1. ESTRUCTURA OPERACIONAL
   ========================= */

CREATE TABLE dbo.Categoria (
    CategoriaID      int IDENTITY(1,1) PRIMARY KEY,
    NombreCategoria  varchar(80) NOT NULL UNIQUE
);

CREATE TABLE dbo.Proveedor (
    ProveedorID       int IDENTITY(1,1) PRIMARY KEY,
    NombreProveedor   varchar(120) NOT NULL,
    Pais              varchar(60) NOT NULL,
    FechaAlta         date NOT NULL
);

CREATE TABLE dbo.Producto (
    ProductoID        int IDENTITY(1,1) PRIMARY KEY,
    SKU               varchar(20) NOT NULL UNIQUE,
    NombreProducto    varchar(120) NOT NULL,
    CategoriaID       int NOT NULL,
    ProveedorID       int NOT NULL,
    Marca              varchar(60) NOT NULL,
    CostoUnitario     decimal(12,2) NOT NULL CHECK (CostoUnitario > 0),
    PrecioLista       decimal(12,2) NOT NULL CHECK (PrecioLista > 0),
    FechaLanzamiento  date NOT NULL,
    Activo             bit NOT NULL,
    CONSTRAINT FK_Producto_Categoria
        FOREIGN KEY (CategoriaID) REFERENCES dbo.Categoria(CategoriaID),
    CONSTRAINT FK_Producto_Proveedor
        FOREIGN KEY (ProveedorID) REFERENCES dbo.Proveedor(ProveedorID)
);

CREATE TABLE dbo.Tienda (
    TiendaID          int IDENTITY(1,1) PRIMARY KEY,
    NombreTienda      varchar(100) NOT NULL,
    Ciudad            varchar(80) NOT NULL,
    Provincia         varchar(80) NOT NULL,
    TipoTienda        varchar(30) NOT NULL,
    FechaApertura     date NOT NULL,
    CONSTRAINT CK_Tienda_Tipo
        CHECK (TipoTienda IN ('Centro comercial','Calle','Express','Outlet'))
);

CREATE TABLE dbo.Cliente (
    ClienteID         int IDENTITY(1,1) PRIMARY KEY,
    Nombre            varchar(60) NOT NULL,
    Apellido          varchar(60) NOT NULL,
    Sexo              char(1) NULL,
    FechaNacimiento   date NULL,
    Ciudad            varchar(80) NOT NULL,
    Provincia         varchar(80) NOT NULL,
    Segmento          varchar(30) NOT NULL,
    FechaRegistro     date NOT NULL,
    CONSTRAINT CK_Cliente_Sexo
        CHECK (Sexo IS NULL OR Sexo IN ('F','M')),
    CONSTRAINT CK_Cliente_Segmento
        CHECK (Segmento IN ('Regular','Preferente','Corporativo'))
);

CREATE TABLE dbo.Promocion (
    PromocionID       int IDENTITY(1,1) PRIMARY KEY,
    NombrePromocion   varchar(100) NOT NULL,
    FechaInicio       date NOT NULL,
    FechaFin          date NOT NULL,
    PorcentajeDto     decimal(5,2) NOT NULL,
    CanalPromocion    varchar(20) NOT NULL,
    CONSTRAINT CK_Promocion_Fechas CHECK (FechaFin >= FechaInicio),
    CONSTRAINT CK_Promocion_Dto CHECK (PorcentajeDto BETWEEN 0 AND 100),
    CONSTRAINT CK_Promocion_Canal CHECK (CanalPromocion IN ('Todos','Tienda','Web','App'))
);

CREATE TABLE dbo.OrdenVenta (
    OrdenID           bigint IDENTITY(1,1) PRIMARY KEY,
    ClienteID         int NULL,
    TiendaID          int NOT NULL,
    FechaOrden        datetime2(0) NOT NULL,
    CanalVenta        varchar(20) NOT NULL,
    EstadoOrden       varchar(20) NOT NULL,
    PromocionID       int NULL,
    CONSTRAINT FK_OrdenVenta_Cliente
        FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente(ClienteID),
    CONSTRAINT FK_OrdenVenta_Tienda
        FOREIGN KEY (TiendaID) REFERENCES dbo.Tienda(TiendaID),
    CONSTRAINT FK_OrdenVenta_Promocion
        FOREIGN KEY (PromocionID) REFERENCES dbo.Promocion(PromocionID),
    CONSTRAINT CK_OrdenVenta_Canal
        CHECK (CanalVenta IN ('Tienda','Web','App')),
    CONSTRAINT CK_OrdenVenta_Estado
        CHECK (EstadoOrden IN ('Completada','Cancelada'))
);

CREATE TABLE dbo.DetalleOrden (
    DetalleOrdenID    bigint IDENTITY(1,1) PRIMARY KEY,
    OrdenID           bigint NOT NULL,
    ProductoID        int NOT NULL,
    Cantidad          int NOT NULL,
    PrecioUnitario    decimal(12,2) NOT NULL,
    DescuentoMonto    decimal(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT FK_DetalleOrden_Orden
        FOREIGN KEY (OrdenID) REFERENCES dbo.OrdenVenta(OrdenID),
    CONSTRAINT FK_DetalleOrden_Producto
        FOREIGN KEY (ProductoID) REFERENCES dbo.Producto(ProductoID),
    CONSTRAINT CK_DetalleOrden_Cantidad CHECK (Cantidad > 0),
    CONSTRAINT CK_DetalleOrden_Precio CHECK (PrecioUnitario > 0),
    CONSTRAINT CK_DetalleOrden_Descuento CHECK (DescuentoMonto >= 0)
);

CREATE TABLE dbo.Pago (
    PagoID            bigint IDENTITY(1,1) PRIMARY KEY,
    OrdenID           bigint NOT NULL,
    FechaPago         datetime2(0) NOT NULL,
    MetodoPago        varchar(30) NOT NULL,
    Monto             decimal(14,2) NOT NULL,
    CONSTRAINT FK_Pago_Orden
        FOREIGN KEY (OrdenID) REFERENCES dbo.OrdenVenta(OrdenID),
    CONSTRAINT CK_Pago_Metodo
        CHECK (MetodoPago IN ('Efectivo','Tarjeta credito','Tarjeta debito','Transferencia','Billetera digital')),
    CONSTRAINT CK_Pago_Monto CHECK (Monto >= 0)
);

CREATE TABLE dbo.Devolucion (
    DevolucionID      bigint IDENTITY(1,1) PRIMARY KEY,
    DetalleOrdenID    bigint NOT NULL,
    FechaDevolucion   datetime2(0) NOT NULL,
    CantidadDevuelta  int NOT NULL,
    Motivo             varchar(50) NOT NULL,
    MontoReembolso    decimal(14,2) NOT NULL,
    CONSTRAINT FK_Devolucion_Detalle
        FOREIGN KEY (DetalleOrdenID) REFERENCES dbo.DetalleOrden(DetalleOrdenID),
    CONSTRAINT CK_Devolucion_Cantidad CHECK (CantidadDevuelta > 0),
    CONSTRAINT CK_Devolucion_Monto CHECK (MontoReembolso >= 0)
);
GO

/* Índices operacionales básicos */
CREATE INDEX IX_Producto_Categoria ON dbo.Producto(CategoriaID);
CREATE INDEX IX_Producto_Proveedor ON dbo.Producto(ProveedorID);
CREATE INDEX IX_OrdenVenta_Fecha ON dbo.OrdenVenta(FechaOrden);
CREATE INDEX IX_OrdenVenta_Cliente ON dbo.OrdenVenta(ClienteID);
CREATE INDEX IX_DetalleOrden_Orden ON dbo.DetalleOrden(OrdenID);
CREATE INDEX IX_DetalleOrden_Producto ON dbo.DetalleOrden(ProductoID);
CREATE INDEX IX_Pago_Orden ON dbo.Pago(OrdenID);
CREATE INDEX IX_Devolucion_Detalle ON dbo.Devolucion(DetalleOrdenID);
GO

/* =========================
   2. DATOS MAESTROS
   ========================= */

INSERT dbo.Categoria (NombreCategoria)
VALUES
('Alimentos y bebidas'),
('Cuidado personal'),
('Hogar y limpieza'),
('Electrodomesticos'),
('Tecnologia'),
('Papeleria'),
('Deportes'),
('Moda'),
('Mascotas'),
('Bebes');

INSERT dbo.Proveedor (NombreProveedor, Pais, FechaAlta)
SELECT
    CONCAT('Proveedor ', RIGHT('00' + CAST(n AS varchar(2)), 2)),
    CHOOSE(1 + ((n-1) % 6),
           'Republica Dominicana','Mexico','Colombia','Estados Unidos','Espana','Panama'),
    DATEADD(day, -1 * (250 + n * 47), CAST('2023-01-01' AS date))
FROM (
    SELECT TOP (24) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
    FROM sys.all_objects
) s;

INSERT dbo.Tienda (NombreTienda, Ciudad, Provincia, TipoTienda, FechaApertura)
VALUES
('Agora Mall', 'Santo Domingo', 'Distrito Nacional', 'Centro comercial', '2017-03-15'),
('Bella Vista', 'Santo Domingo', 'Distrito Nacional', 'Calle', '2018-06-01'),
('Santo Domingo Este', 'Santo Domingo Este', 'Santo Domingo', 'Express', '2020-09-12'),
('Santo Domingo Norte', 'Santo Domingo Norte', 'Santo Domingo', 'Calle', '2021-02-20'),
('Santiago Centro', 'Santiago', 'Santiago', 'Centro comercial', '2016-11-05'),
('Santiago Norte', 'Santiago', 'Santiago', 'Express', '2022-01-10'),
('La Vega', 'La Vega', 'La Vega', 'Calle', '2019-04-18'),
('San Cristobal', 'San Cristobal', 'San Cristobal', 'Calle', '2020-01-25'),
('Puerto Plata', 'Puerto Plata', 'Puerto Plata', 'Centro comercial', '2018-12-02'),
('La Romana', 'La Romana', 'La Romana', 'Centro comercial', '2019-08-22'),
('Higuey', 'Higuey', 'La Altagracia', 'Express', '2022-07-14'),
('Bani Outlet', 'Bani', 'Peravia', 'Outlet', '2023-03-03');

INSERT dbo.Promocion (NombrePromocion, FechaInicio, FechaFin, PorcentajeDto, CanalPromocion)
VALUES
('San Valentin 2023','2023-02-01','2023-02-14',10,'Todos'),
('Madres 2023','2023-05-15','2023-05-31',12,'Todos'),
('Regreso a clases 2023','2023-08-01','2023-08-31',15,'Todos'),
('Black Friday 2023','2023-11-20','2023-11-30',20,'Todos'),
('San Valentin 2024','2024-02-01','2024-02-14',10,'Todos'),
('Madres 2024','2024-05-15','2024-05-31',12,'Todos'),
('Regreso a clases 2024','2024-08-01','2024-08-31',15,'Todos'),
('Black Friday 2024','2024-11-20','2024-11-30',20,'Todos'),
('San Valentin 2025','2025-02-01','2025-02-14',10,'Todos'),
('Madres 2025','2025-05-15','2025-05-31',12,'Todos'),
('Regreso a clases 2025','2025-08-01','2025-08-31',15,'Todos'),
('Black Friday 2025','2025-11-20','2025-11-30',20,'Todos'),
('San Valentin 2026','2026-02-01','2026-02-14',10,'Todos'),
('Madres 2026','2026-05-15','2026-05-31',12,'Todos'),
('Regreso a clases 2026','2026-08-01','2026-08-31',15,'Todos');
GO

/* =========================
   3. GENERADOR DETERMINISTA
   ========================= */

CREATE TABLE #N (n int NOT NULL PRIMARY KEY);

WITH
E1(n) AS (
    SELECT 1 FROM (VALUES(0),(0),(0),(0),(0),(0),(0),(0),(0),(0)) d(n)
),
E2(n) AS (SELECT 1 FROM E1 a CROSS JOIN E1 b),
E4(n) AS (SELECT 1 FROM E2 a CROSS JOIN E2 b),
E5(n) AS (SELECT 1 FROM E4 a CROSS JOIN E1 b)
INSERT #N(n)
SELECT TOP (100000)
       ROW_NUMBER() OVER (ORDER BY (SELECT NULL))
FROM E5;
GO

/* =========================
   4. CLIENTES Y PRODUCTOS
   ========================= */

INSERT dbo.Cliente
    (Nombre, Apellido, Sexo, FechaNacimiento, Ciudad, Provincia, Segmento, FechaRegistro)
SELECT
    CHOOSE(1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('nombre', n)))) % 16,
           'Ana','Luis','Maria','Jose','Carla','Miguel','Laura','Carlos',
           'Sofia','Andres','Daniela','Rafael','Paola','Javier','Natalia','Pedro'),
    CHOOSE(1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('apellido', n)))) % 16,
           'Rodriguez','Martinez','Garcia','Perez','Sanchez','Ramirez','Torres','Diaz',
           'Reyes','Gomez','Castillo','Mendez','Vargas','Cruz','Herrera','Ortiz'),
    CASE ABS(CONVERT(bigint, CHECKSUM(CONCAT('sexo', n)))) % 20
         WHEN 0 THEN NULL
         WHEN 1 THEN NULL
         ELSE CHOOSE(1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('sexo2', n)))) % 2, 'F','M')
    END,
    DATEADD(day,
            -1 * (6570 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('nac', n)))) % 19000),
            CAST('2026-08-31' AS date)),
    CHOOSE(loc.LocID,
           'Santo Domingo','Santo Domingo Este','Santiago','La Vega',
           'San Cristobal','Puerto Plata','La Romana','Higuey'),
    CHOOSE(loc.LocID,
           'Distrito Nacional','Santo Domingo','Santiago','La Vega',
           'San Cristobal','Puerto Plata','La Romana','La Altagracia'),
    CASE
        WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('seg', n)))) % 100 < 12 THEN 'Corporativo'
        WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('seg', n)))) % 100 < 38 THEN 'Preferente'
        ELSE 'Regular'
    END,
    DATEADD(day,
            ABS(CONVERT(bigint, CHECKSUM(CONCAT('reg', n)))) %
                (DATEDIFF(day, '2021-01-01', '2022-12-31') + 1),
            CAST('2021-01-01' AS date))
FROM #N
CROSS APPLY (
    SELECT 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('loc', n)))) % 8 AS LocID
) loc
WHERE n <= 2500;

INSERT dbo.Producto
    (SKU, NombreProducto, CategoriaID, ProveedorID, Marca,
     CostoUnitario, PrecioLista, FechaLanzamiento, Activo)
SELECT
    CONCAT('SKU-', RIGHT('0000' + CAST(n AS varchar(4)), 4)),
    CONCAT('Producto ', RIGHT('000' + CAST(n AS varchar(3)), 3)),
    1 + ((n - 1) % 10),
    1 + (ABS(CONVERT(bigint, CHECKSUM(CONCAT('provprod', n)))) % 24),
    CHOOSE(1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('marca', n)))) % 12,
           'Altura','Nativo','Horizonte','Nova','Prisma','Origen',
           'Lumen','Cumbre','Arena','Verde','Atlas','Brisa'),
    c.CostoUnitario,
    CAST(ROUND(c.CostoUnitario * (1.20 + (n % 9) * 0.05), 2) AS decimal(12,2)),
    DATEADD(day,
            ABS(CONVERT(bigint, CHECKSUM(CONCAT('launch', n)))) %
                (DATEDIFF(day, '2019-01-01', '2022-12-31') + 1),
            CAST('2019-01-01' AS date)),
    CASE WHEN n % 23 = 0 THEN 0 ELSE 1 END
FROM #N
CROSS APPLY (
    SELECT CAST(ROUND(
        35.00 + (ABS(CONVERT(bigint, CHECKSUM(CONCAT('cost', n)))) % 18000) / 10.0,
        2) AS decimal(12,2)) AS CostoUnitario
) c
WHERE n <= 250;
GO

/* =========================
   5. ORDENES
   ========================= */

;WITH BaseOrden AS (
    SELECT
        n,
        DATEADD(
            minute,
            ABS(CONVERT(bigint, CHECKSUM(CONCAT('min', n)))) % 1440,
            CAST(DATEADD(
                day,
                ABS(CONVERT(bigint, CHECKSUM(CONCAT('dia', n)))) %
                    (DATEDIFF(day, '2023-01-01', '2026-08-15') + 1),
                CAST('2023-01-01' AS date)
            ) AS datetime2(0))
        ) AS FechaOrden
    FROM #N
    WHERE n <= 30000
)
INSERT dbo.OrdenVenta
    (ClienteID, TiendaID, FechaOrden, CanalVenta, EstadoOrden, PromocionID)
SELECT
    CASE
        WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('anon', b.n)))) % 100 < 8 THEN NULL
        ELSE 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('clienteorden', b.n)))) % 2500
    END,
    1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('tiendaorden', b.n)))) % 12,
    b.FechaOrden,
    CASE
        WHEN YEAR(b.FechaOrden) = 2023 THEN
            CASE WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 60 THEN 'Tienda'
                 WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 85 THEN 'Web'
                 ELSE 'App' END
        WHEN YEAR(b.FechaOrden) = 2024 THEN
            CASE WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 53 THEN 'Tienda'
                 WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 80 THEN 'Web'
                 ELSE 'App' END
        WHEN YEAR(b.FechaOrden) = 2025 THEN
            CASE WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 46 THEN 'Tienda'
                 WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 75 THEN 'Web'
                 ELSE 'App' END
        ELSE
            CASE WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 40 THEN 'Tienda'
                 WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('canal', b.n)))) % 100 < 70 THEN 'Web'
                 ELSE 'App' END
    END,
    CASE
        WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('estado', b.n)))) % 100 < 4
            THEN 'Cancelada'
        ELSE 'Completada'
    END,
    p.PromocionID
FROM BaseOrden b
OUTER APPLY (
    SELECT TOP (1) pr.PromocionID
    FROM dbo.Promocion pr
    WHERE CAST(b.FechaOrden AS date) BETWEEN pr.FechaInicio AND pr.FechaFin
    ORDER BY pr.PromocionID
) p;
GO

/* =========================
   6. DETALLES DE ORDEN
   ========================= */

INSERT dbo.DetalleOrden
    (OrdenID, ProductoID, Cantidad, PrecioUnitario, DescuentoMonto)
SELECT
    o.OrdenID,
    p.ProductoID,
    q.Cantidad,
    CAST(ROUND(p.PrecioLista *
        (0.96 + (ABS(CONVERT(bigint, CHECKSUM(CONCAT('precio', o.OrdenID, '-', v.LineaNo)))) % 9) / 100.0), 2) AS decimal(12,2)),
    CAST(ROUND(
        p.PrecioLista * q.Cantidad *
        CASE
            WHEN o.PromocionID IS NOT NULL THEN
                (SELECT PorcentajeDto / 100.0 FROM dbo.Promocion WHERE PromocionID = o.PromocionID)
            WHEN ABS(CONVERT(bigint, CHECKSUM(CONCAT('dto', o.OrdenID, '-', v.LineaNo)))) % 100 < 12 THEN 0.05
            ELSE 0
        END, 2) AS decimal(12,2))
FROM dbo.OrdenVenta o
CROSS JOIN (VALUES(1),(2),(3),(4)) v(LineaNo)
CROSS APPLY (
    SELECT CASE
        WHEN MONTH(o.FechaOrden) = 8
             AND ABS(CONVERT(bigint, CHECKSUM(CONCAT('cat', o.OrdenID, '-', v.LineaNo)))) % 100 < 50 THEN 6
        WHEN MONTH(o.FechaOrden) = 11
             AND ABS(CONVERT(bigint, CHECKSUM(CONCAT('cat', o.OrdenID, '-', v.LineaNo)))) % 100 < 45 THEN 5
        WHEN MONTH(o.FechaOrden) = 12
             AND ABS(CONVERT(bigint, CHECKSUM(CONCAT('cat', o.OrdenID, '-', v.LineaNo)))) % 100 < 35 THEN 4
        ELSE 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('cat', o.OrdenID, '-', v.LineaNo)))) % 10
    END AS CategoriaElegida
) cat
CROSS APPLY (
    SELECT cat.CategoriaElegida
           + 10 * (ABS(CONVERT(bigint, CHECKSUM(CONCAT('prod', o.OrdenID, '-', v.LineaNo)))) % 25) AS ProductoID
) x
JOIN dbo.Producto p
    ON p.ProductoID = x.ProductoID
CROSS APPLY (
    SELECT 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('qty', o.OrdenID, '-', v.LineaNo)))) % 4 AS Cantidad
) q
WHERE v.LineaNo <= 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('lineas', o.OrdenID)))) % 4;
GO

/* =========================
   7. PAGOS
   ========================= */

INSERT dbo.Pago (OrdenID, FechaPago, MetodoPago, Monto)
SELECT
    o.OrdenID,
    DATEADD(minute,
            5 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('pagomin', o.OrdenID)))) % 180,
            o.FechaOrden),
    CHOOSE(
        1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('metodo', o.OrdenID)))) % 5,
        'Efectivo','Tarjeta credito','Tarjeta debito','Transferencia','Billetera digital'
    ),
    CAST(ROUND(SUM(d.Cantidad * d.PrecioUnitario - d.DescuentoMonto), 2) AS decimal(14,2))
FROM dbo.OrdenVenta o
JOIN dbo.DetalleOrden d
    ON d.OrdenID = o.OrdenID
WHERE o.EstadoOrden = 'Completada'
GROUP BY o.OrdenID, o.FechaOrden;
GO

/* =========================
   8. DEVOLUCIONES
   ========================= */

INSERT dbo.Devolucion
    (DetalleOrdenID, FechaDevolucion, CantidadDevuelta, Motivo, MontoReembolso)
SELECT
    d.DetalleOrdenID,
    DATEADD(
        day,
        1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('retday', d.DetalleOrdenID)))) % 20,
        o.FechaOrden
    ),
    CASE WHEN d.Cantidad = 1 THEN 1
         ELSE 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('retqty', d.DetalleOrdenID)))) % d.Cantidad
    END,
    CHOOSE(
        1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('retmot', d.DetalleOrdenID)))) % 5,
        'Producto defectuoso',
        'Producto equivocado',
        'Cambio de opinion',
        'Talla o presentacion',
        'Danado en transporte'
    ),
    CAST(ROUND(
        ((d.Cantidad * d.PrecioUnitario - d.DescuentoMonto) / d.Cantidad) *
        CASE WHEN d.Cantidad = 1 THEN 1
             ELSE 1 + ABS(CONVERT(bigint, CHECKSUM(CONCAT('retqty', d.DetalleOrdenID)))) % d.Cantidad
        END, 2) AS decimal(14,2))
FROM dbo.DetalleOrden d
JOIN dbo.OrdenVenta o
    ON o.OrdenID = d.OrdenID
JOIN dbo.Producto p
    ON p.ProductoID = d.ProductoID
WHERE o.EstadoOrden = 'Completada'
  AND ABS(CONVERT(bigint, CHECKSUM(CONCAT('retflag', d.DetalleOrdenID)))) % 100 <
      CASE
          WHEN p.CategoriaID = 8 THEN 14
          WHEN p.CategoriaID IN (4,5) THEN 10
          ELSE 5
      END;
GO

DROP TABLE #N;
GO

/* =========================
   9. COMPROBACION RAPIDA
   ========================= */

SELECT 'Categoria' AS Tabla, COUNT(*) AS Filas FROM dbo.Categoria
UNION ALL SELECT 'Proveedor', COUNT(*) FROM dbo.Proveedor
UNION ALL SELECT 'Producto', COUNT(*) FROM dbo.Producto
UNION ALL SELECT 'Tienda', COUNT(*) FROM dbo.Tienda
UNION ALL SELECT 'Cliente', COUNT(*) FROM dbo.Cliente
UNION ALL SELECT 'Promocion', COUNT(*) FROM dbo.Promocion
UNION ALL SELECT 'OrdenVenta', COUNT(*) FROM dbo.OrdenVenta
UNION ALL SELECT 'DetalleOrden', COUNT(*) FROM dbo.DetalleOrden
UNION ALL SELECT 'Pago', COUNT(*) FROM dbo.Pago
UNION ALL SELECT 'Devolucion', COUNT(*) FROM dbo.Devolucion;
GO
