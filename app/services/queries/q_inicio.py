GET_RECIENTES = """
-- =====================================================
-- CONSULTA: GET_RECIENTES
-- Descripción: Obtiene las 3 pruebas más recientemente subidas
-- Devuelve: id_prueba, id_evaluado, nombre, apellido, fecha (DD-MM-YYYY)
-- =====================================================
SELECT TOP (3)
    p.id_prueba,
    e.id_evaluado,
    e.nombre, 
    e.apellido,
    CONVERT(VARCHAR(10), p.fecha, 105) AS fecha
FROM dbo.Prueba p
JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
ORDER BY p.id_prueba DESC;
"""