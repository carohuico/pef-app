
GET_PRUEBAS_POR_EVALUADO = """
-- =====================================================
-- CONSULTA: GET_PRUEBAS_POR_EVALUADO
-- Descripción: Obtiene las pruebas asociadas a un evaluado
-- Parámetro esperado: id_evaluado (named param for sqlalchemy.text)
-- Devuelve: id_prueba, nombre_archivo, ruta_imagen, formato, fecha (YYYY-MM-DD)
-- =====================================================

SELECT
    id_prueba,
    nombre_archivo,
    ruta_imagen,
    formato,
    CONVERT(VARCHAR(10), fecha, 120) AS fecha
FROM dbo.Prueba
WHERE id_evaluado = :id_evaluado
ORDER BY fecha DESC;
"""
