/*
===============================================================================
 ICC-321 Inteligencia de Negocios — Práctica 1
 Actividad 4: Implementación del Data Warehouse

 Estudiante: Enger Douglas (ID 10144675)
 Motor: Microsoft SQL Server
 Base fuente: BI_Practica_Retail

 Modelo dimensional de Kimball:
   - FactVentas         grano: línea de detalle de una orden completada
   - FactDevoluciones   grano: devolución de una línea de detalle
   - FactPagos          grano: pago de una orden
 Las claves subrogadas se asignan a partir del identificador del origen y se
 reserva la clave -1 para los miembros desconocidos («No identificado»,
 «Sin promoción»).
===============================================================================
*/

USE master;
GO

IF DB_ID(N'DW_Retail') IS NOT NULL
BEGIN
    ALTER DATABASE DW_Retail SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DW_Retail;
END;
GO

CREATE DATABASE DW_Retail;
GO

USE DW_Retail;
GO

/* =========================================================================
   1. DIMENSIONES
   ========================================================================= */

CREATE TABLE dbo.DimFecha (
    FechaKey          int          NOT NULL PRIMARY KEY,   -- formato AAAAMMDD
    Fecha             date         NOT NULL,
    Anio              smallint     NOT NULL,
    Trimestre         tinyint      NOT NULL,
    NombreTrimestre   varchar(10)  NOT NULL,
    Mes               tinyint      NOT NULL,
    NombreMes         varchar(15)  NOT NULL,
    AnioMes           int          NOT NULL,               -- formato AAAAMM
    DiaMes            tinyint      NOT NULL,
    DiaSemana         tinyint      NOT NULL,
    NombreDiaSemana   varchar(12)  NOT NULL,
    SemanaAnio        tinyint      NOT NULL,
    EsFinDeSemana     bit          NOT NULL
);

CREATE TABLE dbo.DimProducto (
    ProductoKey       int           NOT NULL PRIMARY KEY,
    ProductoID        int           NOT NULL,              -- clave natural del origen
    SKU               varchar(20)   NOT NULL,
    NombreProducto    varchar(120)  NOT NULL,
    Marca             varchar(60)   NOT NULL,
    Categoria         varchar(80)   NOT NULL,
    Proveedor         varchar(120)  NOT NULL,
    PaisProveedor     varchar(60)   NOT NULL,
    CostoUnitario     decimal(12,2) NOT NULL,
    PrecioLista       decimal(12,2) NOT NULL,
    RangoPrecio       varchar(20)   NOT NULL,
    FechaLanzamiento  date          NOT NULL,
    Activo            bit           NOT NULL
);

CREATE TABLE dbo.DimCliente (
    ClienteKey        int           NOT NULL PRIMARY KEY,  -- -1 = No identificado
    ClienteID         int           NULL,
    NombreCompleto    varchar(130)  NOT NULL,
    Sexo              varchar(20)   NOT NULL,              -- M, F o «No especificado»
    GrupoEdad         varchar(20)   NOT NULL,
    Ciudad            varchar(80)   NOT NULL,
    Provincia         varchar(80)   NOT NULL,
    Segmento          varchar(30)   NOT NULL,
    AnioRegistro      smallint      NULL
);

CREATE TABLE dbo.DimTienda (
    TiendaKey         int           NOT NULL PRIMARY KEY,
    TiendaID          int           NOT NULL,
    NombreTienda      varchar(100)  NOT NULL,
    Ciudad            varchar(80)   NOT NULL,
    Provincia         varchar(80)   NOT NULL,
    TipoTienda        varchar(30)   NOT NULL,
    AnioApertura      smallint      NOT NULL
);

CREATE TABLE dbo.DimPromocion (
    PromocionKey      int           NOT NULL PRIMARY KEY,  -- -1 = Sin promoción
    PromocionID       int           NULL,
    NombrePromocion   varchar(100)  NOT NULL,
    PorcentajeDto     decimal(5,2)  NOT NULL,
    CanalPromocion    varchar(20)   NOT NULL,
    FechaInicio       date          NULL,
    FechaFin          date          NULL
);

CREATE TABLE dbo.DimCanal (
    CanalKey          int           NOT NULL PRIMARY KEY,
    CanalVenta        varchar(20)   NOT NULL
);

CREATE TABLE dbo.DimMotivoDevolucion (
    MotivoKey         int           NOT NULL PRIMARY KEY,
    Motivo            varchar(50)   NOT NULL
);

CREATE TABLE dbo.DimMetodoPago (
    MetodoPagoKey     int           NOT NULL PRIMARY KEY,
    MetodoPago        varchar(30)   NOT NULL
);
GO

/* =========================================================================
   2. TABLAS DE HECHOS
   ========================================================================= */

/* Grano: una línea de detalle de una orden de venta COMPLETADA */
CREATE TABLE dbo.FactVentas (
    VentaKey          bigint        NOT NULL PRIMARY KEY,  -- = DetalleOrdenID del origen
    FechaKey          int           NOT NULL,
    ProductoKey       int           NOT NULL,
    ClienteKey        int           NOT NULL,
    TiendaKey         int           NOT NULL,
    PromocionKey      int           NOT NULL,
    CanalKey          int           NOT NULL,
    OrdenID           bigint        NOT NULL,              -- dimensión degenerada
    CantidadVendida   int           NOT NULL,
    PrecioUnitario    decimal(12,2) NOT NULL,              -- no aditiva: solo promedios
    MontoBruto        decimal(14,2) NOT NULL,              -- Cantidad * PrecioUnitario
    DescuentoMonto    decimal(14,2) NOT NULL,
    MontoNeto         decimal(14,2) NOT NULL,              -- MontoBruto - DescuentoMonto
    CostoTotal        decimal(14,2) NOT NULL,              -- Cantidad * CostoUnitario
    MargenBruto       decimal(14,2) NOT NULL,              -- MontoNeto - CostoTotal
    CONSTRAINT FK_FactVentas_Fecha     FOREIGN KEY (FechaKey)     REFERENCES dbo.DimFecha(FechaKey),
    CONSTRAINT FK_FactVentas_Producto  FOREIGN KEY (ProductoKey)  REFERENCES dbo.DimProducto(ProductoKey),
    CONSTRAINT FK_FactVentas_Cliente   FOREIGN KEY (ClienteKey)   REFERENCES dbo.DimCliente(ClienteKey),
    CONSTRAINT FK_FactVentas_Tienda    FOREIGN KEY (TiendaKey)    REFERENCES dbo.DimTienda(TiendaKey),
    CONSTRAINT FK_FactVentas_Promocion FOREIGN KEY (PromocionKey) REFERENCES dbo.DimPromocion(PromocionKey),
    CONSTRAINT FK_FactVentas_Canal     FOREIGN KEY (CanalKey)     REFERENCES dbo.DimCanal(CanalKey),
    CONSTRAINT CK_FactVentas_Cantidad  CHECK (CantidadVendida > 0)
);

/* Grano: una devolución de una línea de detalle */
CREATE TABLE dbo.FactDevoluciones (
    DevolucionKey     bigint        NOT NULL PRIMARY KEY,  -- = DevolucionID del origen
    FechaKey          int           NOT NULL,              -- fecha de la devolución
    ProductoKey       int           NOT NULL,
    ClienteKey        int           NOT NULL,
    TiendaKey         int           NOT NULL,
    MotivoKey         int           NOT NULL,
    DetalleOrdenID    bigint        NOT NULL,              -- dimensión degenerada
    CantidadDevuelta  int           NOT NULL,
    MontoReembolso    decimal(14,2) NOT NULL,
    CONSTRAINT FK_FactDev_Fecha     FOREIGN KEY (FechaKey)    REFERENCES dbo.DimFecha(FechaKey),
    CONSTRAINT FK_FactDev_Producto  FOREIGN KEY (ProductoKey) REFERENCES dbo.DimProducto(ProductoKey),
    CONSTRAINT FK_FactDev_Cliente   FOREIGN KEY (ClienteKey)  REFERENCES dbo.DimCliente(ClienteKey),
    CONSTRAINT FK_FactDev_Tienda    FOREIGN KEY (TiendaKey)   REFERENCES dbo.DimTienda(TiendaKey),
    CONSTRAINT FK_FactDev_Motivo    FOREIGN KEY (MotivoKey)   REFERENCES dbo.DimMotivoDevolucion(MotivoKey),
    CONSTRAINT CK_FactDev_Cantidad  CHECK (CantidadDevuelta > 0)
);

/* Grano: el pago de una orden */
CREATE TABLE dbo.FactPagos (
    PagoKey           bigint        NOT NULL PRIMARY KEY,  -- = PagoID del origen
    FechaKey          int           NOT NULL,
    ClienteKey        int           NOT NULL,
    TiendaKey         int           NOT NULL,
    CanalKey          int           NOT NULL,
    MetodoPagoKey     int           NOT NULL,
    OrdenID           bigint        NOT NULL,              -- dimensión degenerada
    MontoPagado       decimal(14,2) NOT NULL,
    CONSTRAINT FK_FactPagos_Fecha   FOREIGN KEY (FechaKey)      REFERENCES dbo.DimFecha(FechaKey),
    CONSTRAINT FK_FactPagos_Cliente FOREIGN KEY (ClienteKey)    REFERENCES dbo.DimCliente(ClienteKey),
    CONSTRAINT FK_FactPagos_Tienda  FOREIGN KEY (TiendaKey)     REFERENCES dbo.DimTienda(TiendaKey),
    CONSTRAINT FK_FactPagos_Canal   FOREIGN KEY (CanalKey)      REFERENCES dbo.DimCanal(CanalKey),
    CONSTRAINT FK_FactPagos_Metodo  FOREIGN KEY (MetodoPagoKey) REFERENCES dbo.DimMetodoPago(MetodoPagoKey)
);
GO

/* Índices sobre las claves foráneas de los hechos */
CREATE INDEX IX_FactVentas_Fecha     ON dbo.FactVentas(FechaKey);
CREATE INDEX IX_FactVentas_Producto  ON dbo.FactVentas(ProductoKey);
CREATE INDEX IX_FactVentas_Cliente   ON dbo.FactVentas(ClienteKey);
CREATE INDEX IX_FactVentas_Tienda    ON dbo.FactVentas(TiendaKey);
CREATE INDEX IX_FactVentas_Promocion ON dbo.FactVentas(PromocionKey);
CREATE INDEX IX_FactDev_Fecha        ON dbo.FactDevoluciones(FechaKey);
CREATE INDEX IX_FactDev_Producto     ON dbo.FactDevoluciones(ProductoKey);
CREATE INDEX IX_FactPagos_Fecha      ON dbo.FactPagos(FechaKey);
GO

/* =========================================================================
   3. CARGA DE LA DIMENSIÓN DE TIEMPO
   Se genera de forma independiente, con todos los días del período 2023-2026.
   ========================================================================= */

WITH Numeros AS (
    SELECT TOP (DATEDIFF(day, '2023-01-01', '2026-12-31') + 1)
           ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
),
Fechas AS (
    SELECT DATEADD(day, n, CAST('2023-01-01' AS date)) AS Fecha FROM Numeros
)
INSERT INTO dbo.DimFecha
    (FechaKey, Fecha, Anio, Trimestre, NombreTrimestre, Mes, NombreMes, AnioMes,
     DiaMes, DiaSemana, NombreDiaSemana, SemanaAnio, EsFinDeSemana)
SELECT
    CONVERT(int, FORMAT(Fecha, 'yyyyMMdd')),
    Fecha,
    YEAR(Fecha),
    DATEPART(quarter, Fecha),
    CONCAT('T', DATEPART(quarter, Fecha)),
    MONTH(Fecha),
    CHOOSE(MONTH(Fecha), 'Enero','Febrero','Marzo','Abril','Mayo','Junio',
                         'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'),
    CONVERT(int, FORMAT(Fecha, 'yyyyMM')),
    DAY(Fecha),
    DATEPART(weekday, Fecha),
    CHOOSE(DATEPART(weekday, Fecha), 'Domingo','Lunes','Martes','Miercoles','Jueves','Viernes','Sabado'),
    DATEPART(week, Fecha),
    CASE WHEN DATEPART(weekday, Fecha) IN (1, 7) THEN 1 ELSE 0 END
FROM Fechas;
GO

/* =========================================================================
   4. MIEMBROS ESPECIALES PARA LOS NULOS DEL ORIGEN
   ========================================================================= */

INSERT INTO dbo.DimCliente
    (ClienteKey, ClienteID, NombreCompleto, Sexo, GrupoEdad, Ciudad, Provincia, Segmento, AnioRegistro)
VALUES
    (-1, NULL, 'No identificado', 'No especificado', 'No aplica', 'No aplica', 'No aplica', 'No identificado', NULL);

INSERT INTO dbo.DimPromocion
    (PromocionKey, PromocionID, NombrePromocion, PorcentajeDto, CanalPromocion, FechaInicio, FechaFin)
VALUES
    (-1, NULL, 'Sin promocion', 0.00, 'No aplica', NULL, NULL);
GO

/* =========================================================================
   5. VERIFICACIÓN
   ========================================================================= */

SELECT 'DimFecha' AS Tabla, COUNT(*) AS Filas, MIN(Fecha) AS Desde, MAX(Fecha) AS Hasta FROM dbo.DimFecha
UNION ALL
SELECT 'DimCliente (miembro -1)', COUNT(*), NULL, NULL FROM dbo.DimCliente WHERE ClienteKey = -1
UNION ALL
SELECT 'DimPromocion (miembro -1)', COUNT(*), NULL, NULL FROM dbo.DimPromocion WHERE PromocionKey = -1;
GO
