
GET_PRUEBAS_POR_EVALUADO = """
-- =====================================================
-- CONSULTA: GET_PRUEBAS_POR_EVALUADO
-- Descripción: Obtiene las pruebas asociadas a un evaluado
-- Parámetro esperado: id_evaluado (named param for sqlalchemy.text)
-- Devuelve: id_prueba, nombre_archivo, ruta_imagen, formato, fecha (YYYY-MM-DD)
-- Además agrega una columna `resultados_json` con los resultados de cada prueba en formato JSON
-- =====================================================

SELECT
    p.id_prueba,
    p.nombre_archivo,
    p.ruta_imagen,
    p.formato,
    CONVERT(VARCHAR(10), p.fecha, 120) AS fecha,
    (
        SELECT
            r.id_resultado,
            r.id_indicador,
            i.nombre AS nombre_indicador,
            i.significado,
            i.id_categoria,
            c.nombre AS categoria_nombre,
            r.confianza,
            r.x_min,
            r.y_min,
            r.x_max,
            r.y_max
        FROM dbo.Resultado r
        LEFT JOIN dbo.Indicador i ON r.id_indicador = i.id_indicador
        LEFT JOIN dbo.Categoria c ON i.id_categoria = c.id_categoria
        WHERE r.id_prueba = p.id_prueba
        ORDER BY r.id_resultado ASC
        FOR JSON PATH
    ) AS resultados_json
FROM dbo.Prueba p
WHERE p.id_evaluado = :id_evaluado
ORDER BY p.fecha ASC;
"""


GET_RESULTADOS_POR_PRUEBA = """
-- =====================================================
-- CONSULTA: GET_RESULTADOS_POR_PRUEBA
-- Descripción: Obtiene los resultados asociados a una prueba con nombre y significado del indicador
-- Parámetro esperado: id_prueba (named param for sqlalchemy.text)
-- Devuelve: id_resultado, id_indicador, nombre_indicador, significado, confianza, x_min, y_min, x_max, y_max
-- =====================================================
SELECT
    r.id_resultado,
    r.id_indicador,
    i.nombre AS nombre_indicador,
    i.significado,
    i.id_categoria,
    c.nombre AS categoria_nombre,
    r.confianza,
    r.x_min,
    r.y_min,
    r.x_max,
    r.y_max
FROM dbo.Resultado r
LEFT JOIN dbo.Indicador i ON r.id_indicador = i.id_indicador
LEFT JOIN dbo.Categoria c ON i.id_categoria = c.id_categoria
WHERE r.id_prueba = :id_prueba
ORDER BY r.id_resultado ASC;  
"""