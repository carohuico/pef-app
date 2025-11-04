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
SELECT id_indicador, nombre, significado
FROM Indicador
WHERE id_indicador IN (
    SELECT TRY_CAST(value AS INT) FROM STRING_SPLIT(:ids_csv, ',')
);
"""

