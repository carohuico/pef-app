LISTADO_EVALUADOS_SQL = """
-- =====================================================
-- CONSULTA: LISTADO GENERAL DE EVALUADOS
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
    g.nombre       AS [Grupo]
FROM Evaluado e
LEFT JOIN Grupo g ON e.id_grupo = g.id_grupo
ORDER BY e.id_evaluado ASC;
"""
