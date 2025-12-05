GET_INDICADORES = """
-- =====================================================
-- CONSULTA: GET_INDICADORES
-- Descripción: Obtiene la lista de indicadores disponibles
-- Devuelve: id_indicador, nombre, significado
-- =====================================================
SELECT
    id_indicador,
    nombre,
    significado
FROM Indicador

"""

GET_INDICADORES_POR_IDS = """
-- =====================================================
-- CONSULTA: GET_INDICADORES_POR_IDS
-- Descripción: Obtiene nombre y significado de indicadores por una lista de ids
-- Parámetro: ids_csv (csv de ids)
-- =====================================================
SELECT i.id_indicador,
       i.nombre,
       i.significado,
       i.id_categoria,
       c.nombre AS categoria_nombre
FROM Indicador i
LEFT JOIN Categoria c ON i.id_categoria = c.id_categoria
WHERE i.id_indicador IN (
    SELECT TRY_CAST(value AS INT) FROM STRING_SPLIT(@ids_csv, ',')
);
"""

