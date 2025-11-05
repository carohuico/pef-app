# =====================================================
# QUERIES CON FILTROS PARA ESTADÍSTICAS
# =====================================================

# ==================== QUERIES BASE (SIN FILTROS) ====================

GET_EVALUACIONES_TOTALES = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_TOTALES
-- Descripción: Obtiene el total de evaluaciones (pruebas) registradas
-- Devuelve: total_evaluaciones (int)
-- =====================================================
SELECT COUNT(*) AS total_evaluaciones
FROM dbo.Prueba;
"""

GET_CANTIDAD_EVALUADOS = """
-- =====================================================
-- CONSULTA: GET_CANTIDAD_EVALUADOS
-- Descripción: Cantidad de evaluados registrados (únicos)
-- Devuelve: cantidad_evaluados (int)
-- =====================================================
SELECT COUNT(*) AS cantidad_evaluados
FROM dbo.Evaluado;
"""

GET_EVALUACIONES_POR_PERSONA = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_PERSONA
-- Descripción: Promedio de evaluaciones por evaluado
-- Devuelve: promedio_evaluaciones (decimal)
-- =====================================================
SELECT AVG(evaluacion_count * 1.0) AS promedio_evaluaciones
FROM (
    SELECT COUNT(*) AS evaluacion_count
    FROM dbo.Prueba
    GROUP BY id_evaluado
) AS subquery;
"""

GET_EVALUACIONES_POR_MES = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_MES
-- Descripción: Cantidad de evaluaciones por mes para un año dado
-- Parámetro: anio (int)
-- Devuelve: mes_num (1-12), mes_nombre, cantidad
-- =====================================================
SELECT
    DATEPART(MONTH, fecha) AS mes_num,
    DATENAME(MONTH, fecha) AS mes_nombre,
    COUNT(*) AS cantidad
FROM dbo.Prueba
WHERE YEAR(fecha) = :anio
GROUP BY DATEPART(MONTH, fecha), DATENAME(MONTH, fecha)
ORDER BY mes_num;
"""

GET_EVALUACIONES_POR_ANIO = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_ANIO
-- Descripción: Cantidad de evaluaciones agrupadas por año
-- Devuelve: anio, cantidad
-- =====================================================
SELECT
    YEAR(fecha) AS anio,
    COUNT(*) AS cantidad
FROM dbo.Prueba
GROUP BY YEAR(fecha)
ORDER BY anio;
"""


# ==================== QUERIES CON FILTROS ====================

GET_EVALUACIONES_TOTALES_FILTERED = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_TOTALES_FILTERED
-- Descripción: Obtiene el total de evaluaciones filtradas
-- Parámetros: id_evaluado, sexo, id_grupo, fecha_inicio, fecha_fin (opcionales)
-- Devuelve: total_evaluaciones (int)
-- =====================================================
SELECT COUNT(*) AS total_evaluaciones
FROM dbo.Prueba p
INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
WHERE 1=1
    AND (:id_evaluado IS NULL OR e.id_evaluado = :id_evaluado)
    AND (:sexo IS NULL OR e.sexo = :sexo)
    AND (:id_grupo IS NULL OR e.id_grupo = :id_grupo)
    AND (:fecha_inicio IS NULL OR p.fecha >= :fecha_inicio)
    AND (:fecha_fin IS NULL OR p.fecha <= :fecha_fin);
"""

GET_CANTIDAD_EVALUADOS_FILTERED = """
-- =====================================================
-- CONSULTA: GET_CANTIDAD_EVALUADOS_FILTERED
-- Descripción: Cantidad de evaluados únicos que cumplen con los filtros
-- Parámetros: id_evaluado, sexo, id_grupo, fecha_inicio, fecha_fin (opcionales)
-- Devuelve: cantidad_evaluados (int)
-- =====================================================
SELECT COUNT(DISTINCT e.id_evaluado) AS cantidad_evaluados
FROM dbo.Evaluado e
LEFT JOIN dbo.Prueba p ON e.id_evaluado = p.id_evaluado
WHERE 1=1
    AND (:id_evaluado IS NULL OR e.id_evaluado = :id_evaluado)
    AND (:sexo IS NULL OR e.sexo = :sexo)
    AND (:id_grupo IS NULL OR e.id_grupo = :id_grupo)
    AND (
        (:fecha_inicio IS NULL AND :fecha_fin IS NULL) 
        OR (p.fecha >= :fecha_inicio AND p.fecha <= :fecha_fin)
        OR (p.id_prueba IS NULL)
    );
"""

GET_EVALUACIONES_POR_PERSONA_FILTERED = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_PERSONA_FILTERED
-- Descripción: Promedio de evaluaciones por evaluado filtrado
-- Parámetros: id_evaluado, sexo, id_grupo, fecha_inicio, fecha_fin (opcionales)
-- Devuelve: promedio_evaluaciones (decimal)
-- =====================================================
SELECT 
    CASE 
        WHEN COUNT(DISTINCT e.id_evaluado) = 0 THEN 0
        ELSE CAST(COUNT(p.id_prueba) AS FLOAT) / COUNT(DISTINCT e.id_evaluado)
    END AS promedio_evaluaciones
FROM dbo.Evaluado e
LEFT JOIN dbo.Prueba p ON e.id_evaluado = p.id_evaluado
    AND (:fecha_inicio IS NULL OR p.fecha >= :fecha_inicio)
    AND (:fecha_fin IS NULL OR p.fecha <= :fecha_fin)
WHERE 1=1
    AND (:id_evaluado IS NULL OR e.id_evaluado = :id_evaluado)
    AND (:sexo IS NULL OR e.sexo = :sexo)
    AND (:id_grupo IS NULL OR e.id_grupo = :id_grupo);
"""

GET_EVALUACIONES_POR_MES_FILTERED = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_MES_FILTERED
-- Descripción: Cantidad de evaluaciones por mes para un año dado con filtros
-- Parámetros: anio (requerido), id_evaluado, sexo, id_grupo (opcionales)
-- Devuelve: mes_num (1-12), mes_nombre, cantidad
-- =====================================================
SELECT
    DATEPART(MONTH, p.fecha) AS mes_num,
    DATENAME(MONTH, p.fecha) AS mes_nombre,
    COUNT(*) AS cantidad
FROM dbo.Prueba p
INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
WHERE YEAR(p.fecha) = :anio
    AND (:id_evaluado IS NULL OR e.id_evaluado = :id_evaluado)
    AND (:sexo IS NULL OR e.sexo = :sexo)
    AND (:id_grupo IS NULL OR e.id_grupo = :id_grupo)
GROUP BY DATEPART(MONTH, p.fecha), DATENAME(MONTH, p.fecha)
ORDER BY mes_num;
"""

GET_EVALUACIONES_POR_ANIO_FILTERED = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_ANIO_FILTERED
-- Descripción: Cantidad de evaluaciones agrupadas por año con filtros
-- Parámetros: id_evaluado, sexo, id_grupo, fecha_inicio, fecha_fin (opcionales)
-- Devuelve: anio, cantidad
-- =====================================================
SELECT
    YEAR(p.fecha) AS anio,
    COUNT(*) AS cantidad
FROM dbo.Prueba p
INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
WHERE 1=1
    AND (:id_evaluado IS NULL OR e.id_evaluado = :id_evaluado)
    AND (:sexo IS NULL OR e.sexo = :sexo)
    AND (:id_grupo IS NULL OR e.id_grupo = :id_grupo)
    AND (:fecha_inicio IS NULL OR p.fecha >= :fecha_inicio)
    AND (:fecha_fin IS NULL OR p.fecha <= :fecha_fin)
GROUP BY YEAR(p.fecha)
ORDER BY anio;
"""


# ==================== QUERIES AUXILIARES PARA FILTROS ====================

GET_LISTA_EVALUADOS = """
-- =====================================================
-- CONSULTA: GET_LISTA_EVALUADOS
-- Descripción: Lista de evaluados para el selector de filtro
-- Devuelve: id_evaluado, nombre_completo
-- =====================================================
SELECT 
    id_evaluado,
    CONCAT(nombre, ' ', apellido) AS nombre_completo
FROM dbo.Evaluado
ORDER BY nombre, apellido;
"""

GET_LISTA_GRUPOS = """
-- =====================================================
-- CONSULTA: GET_LISTA_GRUPOS
-- Descripción: Lista de grupos disponibles para el filtro
-- Devuelve: id_grupo, nombre
-- =====================================================
SELECT 
    id_grupo,
    nombre
FROM dbo.Grupo
ORDER BY nombre;
"""

GET_LISTA_SEXOS = """
-- =====================================================
-- CONSULTA: GET_LISTA_SEXOS
-- Descripción: Lista de valores únicos de sexo disponibles
-- Devuelve: sexo
-- =====================================================
SELECT DISTINCT sexo
FROM dbo.Evaluado
WHERE sexo IS NOT NULL
ORDER BY sexo;
"""

GET_RANGO_FECHAS = """
-- =====================================================
-- CONSULTA: GET_RANGO_FECHAS
-- Descripción: Obtiene el rango de fechas disponible en las evaluaciones
-- Devuelve: fecha_min, fecha_max
-- =====================================================
SELECT 
    MIN(fecha) AS fecha_min,
    MAX(fecha) AS fecha_max
FROM dbo.Prueba;
"""


# ==================== QUERIES ADICIONALES ====================

GET_EVALUACIONES_POR_GRUPO = """
-- =====================================================
-- CONSULTA: GET_EVALUACIONES_POR_GRUPO
-- Descripción: Cuenta de evaluaciones por grupo de evaluados
-- Devuelve: id_grupo, nombre_grupo, cantidad
-- =====================================================
SELECT
    g.id_grupo,
    g.nombre AS nombre_grupo,
    COUNT(p.id_prueba) AS cantidad
FROM dbo.Grupo g
LEFT JOIN dbo.Evaluado e ON e.id_grupo = g.id_grupo
LEFT JOIN dbo.Prueba p ON p.id_evaluado = e.id_evaluado
GROUP BY g.id_grupo, g.nombre
ORDER BY cantidad DESC;
"""

GET_DISTRIBUCION_SEXO = """
-- =====================================================
-- CONSULTA: GET_DISTRIBUCION_SEXO
-- Descripción: Distribución de evaluaciones por sexo del evaluado
-- Devuelve: sexo, cantidad
-- =====================================================
SELECT
    ISNULL(e.sexo, 'No especificado') AS sexo,
    COUNT(p.id_prueba) AS cantidad
FROM dbo.Evaluado e
LEFT JOIN dbo.Prueba p ON p.id_evaluado = e.id_evaluado
GROUP BY ISNULL(e.sexo, 'No especificado');
"""

GET_TOP_INDICADORES = """
-- =====================================================
-- CONSULTA: GET_TOP_INDICADORES
-- Descripción: Indicadores más detectados en los resultados
-- Parámetro: top_n (int)
-- Devuelve: id_indicador, nombre, significado, apariciones
-- Nota: Se usa OFFSET/FETCH para poder pasar top_n como parámetro
-- =====================================================
SELECT
    i.id_indicador,
    i.nombre,
    i.significado,
    COUNT(r.id_resultado) AS apariciones
FROM dbo.Resultado r
INNER JOIN dbo.Indicador i ON i.id_indicador = r.id_indicador
GROUP BY i.id_indicador, i.nombre, i.significado
ORDER BY apariciones DESC
OFFSET 0 ROWS
FETCH NEXT :top_n ROWS ONLY;
"""