# =====================================================
# QUERIES PARA HISTORIAL DE EVALUACIONES/PRUEBAS
# =====================================================

# Query para obtener el listado de todas las pruebas/evaluaciones
LISTADO_HISTORIAL_SQL = """
SELECT 
    p.id_prueba,
    p.id_evaluado,
    p.ruta_imagen,  
    CONCAT(e.nombre, ' ', e.apellido) AS [Nombre del evaluado],
    DATEDIFF(YEAR, e.fecha_nacimiento, GETDATE()) AS Edad,
    e.sexo AS Sexo,
    ISNULL(g.nombre, 'Sin grupo') AS Grupo,
    FORMAT(p.fecha, 'dd/MM/yyyy') AS [Fecha de evaluación]
FROM 
    dbo.Prueba p
    INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
    LEFT JOIN dbo.Grupo g ON e.id_grupo = g.id_grupo
ORDER BY 
    p.fecha DESC, p.id_prueba DESC;
"""

# Query parametrizada para especialistas: filtra por el especialista asignado (e.id_usuario)
LISTADO_HISTORIAL_POR_ESPECIALISTA = """
SELECT 
    p.id_prueba,
    p.id_evaluado,
    p.ruta_imagen,  
    CONCAT(e.nombre, ' ', e.apellido) AS [Nombre del evaluado],
    DATEDIFF(YEAR, e.fecha_nacimiento, GETDATE()) AS Edad,
    e.sexo AS Sexo,
    ISNULL(g.nombre, 'Sin grupo') AS Grupo,
    FORMAT(p.fecha, 'dd/MM/yyyy') AS [Fecha de evaluación]
FROM 
    dbo.Prueba p
    INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
    LEFT JOIN dbo.Grupo g ON e.id_grupo = g.id_grupo
WHERE
    e.id_usuario = :id_usuario
ORDER BY 
    p.fecha DESC, p.id_prueba DESC;
"""

# Query para eliminar pruebas por lista de IDs
ELIMINAR_PRUEBAS = """
DECLARE @ids_table TABLE (id INT);

INSERT INTO @ids_table (id)
SELECT value 
FROM STRING_SPLIT(:ids_csv, ',');

-- Primero eliminar los resultados asociados
DELETE FROM dbo.Resultado
WHERE id_prueba IN (SELECT id FROM @ids_table);

-- Luego eliminar las pruebas
DELETE FROM dbo.Prueba
WHERE id_prueba IN (SELECT id FROM @ids_table);

-- Devolver los IDs eliminados para confirmar
SELECT id AS id_prueba FROM @ids_table;
"""

# Query para obtener detalles de una prueba específica
GET_PRUEBA_DETALLE = """
SELECT 
    p.id_prueba,
    p.id_evaluado,
    p.nombre_archivo,
    p.ruta_imagen,
    p.formato,
    p.fecha,
    e.nombre,
    e.apellido,
    e.fecha_nacimiento,
    e.sexo,
    e.estado_civil,
    e.escolaridad,
    e.ocupacion,
    g.nombre AS grupo
FROM 
    dbo.Prueba p
    INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
    LEFT JOIN dbo.Grupo g ON e.id_grupo = g.id_grupo
WHERE 
    p.id_prueba = :id_prueba;
"""

# Query para obtener los resultados de una prueba
GET_RESULTADOS_PRUEBA = """
SELECT 
    r.id_resultado,
    r.id_indicador,
    i.nombre AS nombre_indicador,
    i.significado,
    r.x_min,
    r.y_min,
    r.x_max,
    r.y_max,
    r.confianza
FROM 
    dbo.Resultado r
    INNER JOIN dbo.Indicador i ON r.id_indicador = i.id_indicador
WHERE 
    r.id_prueba = :id_prueba
ORDER BY 
    r.confianza DESC;
"""

# Query para contar las evaluaciones por evaluado
COUNT_PRUEBAS_POR_EVALUADO = """
SELECT 
    e.id_evaluado,
    CONCAT(e.nombre, ' ', e.apellido) AS nombre_completo,
    COUNT(p.id_prueba) AS total_evaluaciones
FROM 
    dbo.Evaluado e
    LEFT JOIN dbo.Prueba p ON e.id_evaluado = p.id_evaluado
GROUP BY 
    e.id_evaluado, e.nombre, e.apellido
ORDER BY 
    total_evaluaciones DESC;
"""

# Query para obtener evaluaciones recientes (últimas N)
GET_EVALUACIONES_RECIENTES = """
SELECT TOP :n
    p.id_prueba,
    p.id_evaluado,
    CONCAT(e.nombre, ' ', e.apellido) AS nombre_evaluado,
    FORMAT(p.fecha, 'dd/MM/yyyy HH:mm') AS fecha_evaluacion
FROM 
    dbo.Prueba p
    INNER JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
ORDER BY 
    p.fecha DESC;
"""

# Query para obtener estadísticas del historial
GET_ESTADISTICAS_HISTORIAL = """
SELECT 
    COUNT(DISTINCT p.id_evaluado) AS total_evaluados,
    COUNT(p.id_prueba) AS total_evaluaciones,
    COUNT(DISTINCT g.id_grupo) AS total_grupos,
    MIN(p.fecha) AS fecha_primera_evaluacion,
    MAX(p.fecha) AS fecha_ultima_evaluacion
FROM 
    dbo.Prueba p
    LEFT JOIN dbo.Evaluado e ON p.id_evaluado = e.id_evaluado
    LEFT JOIN dbo.Grupo g ON e.id_grupo = g.id_grupo;
"""