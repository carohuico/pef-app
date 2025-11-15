LISTADO_EVALUADOS_SQL = """
-- =====================================================
-- CONSULTA: HISTORIAL DE EVALUADOS
-- =====================================================

SELECT
    e.id_evaluado,
    e.nombre       AS Nombre,
    e.apellido     AS Apellido,
    DATEDIFF(YEAR, e.fecha_nacimiento, GETDATE()) AS Edad,
    e.sexo         AS Sexo,
    e.estado_civil AS [Estado civil],
    e.escolaridad  AS Escolaridad,
    e.ocupacion    AS Ocupacion,
    g.nombre       AS [Grupo],
    e.id_usuario   AS id_usuario,
    u.nombre_completo AS Especialista
FROM Evaluado e
LEFT JOIN Grupo g ON e.id_grupo = g.id_grupo
LEFT JOIN Usuario u ON e.id_usuario = u.id_usuario
ORDER BY e.id_evaluado ASC;
"""

ELIMINAR_EVALUADOS = """
-- =====================================================
-- CONSULTA: ELIMINAR_EVALUADOS
-- Descripción: Elimina evaluados por una lista de ids separados por comas.
-- Parámetros esperados:
--   ids_csv  -> string con ids separados por coma, por ejemplo '1,2,3'
-- Devuelve: rows_deleted (número de filas eliminadas)
-- =====================================================
-- Usamos OUTPUT para devolver los ids borrados en el mismo result set
DELETE FROM Evaluado
OUTPUT DELETED.id_evaluado AS deleted_id
WHERE id_evaluado IN (
    SELECT TRY_CAST(value AS INT) FROM STRING_SPLIT(:ids_csv, ',')
);
"""
