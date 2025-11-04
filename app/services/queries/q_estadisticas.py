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
