
GET_GRUPOS = """
-- =====================================================
-- CONSULTA: LISTADO DE GRUPOS
-- Devuelve id_grupo y nombre para popular desplegables
-- =====================================================

SELECT id_grupo, nombre
FROM Grupo
ORDER BY nombre ASC;
"""
CREAR_EVALUADO = """
-- =====================================================
-- CONSULTA: CREAR_EVALUADO
-- =====================================================

INSERT INTO Evaluado (
    nombre,
    apellido,
    fecha_nacimiento,
    sexo,
    estado_civil,
    escolaridad,
    ocupacion,
    id_grupo,
    id_usuario
)
OUTPUT INSERTED.id_evaluado AS id_evaluado
VALUES (
    :nombre,
    :apellido,
    :fecha_nacimiento,
    :sexo,
    :estado_civil,
    :escolaridad,
    :ocupacion,
    :id_grupo,
    :id_usuario
);
"""

POST_PRUEBA = """
-- =====================================================
-- CONSULTA: POST_PRUEBA 
-- Descripción: Registra una nueva prueba en la base de datos Y RETORNA su id.
-- Parámetros esperados:
    INSERT INTO Prueba (id_evaluado, nombre_archivo, ruta_imagen, formato, fecha)
    OUTPUT INSERTED.id_prueba AS id_prueba
    VALUES (:id_evaluado, :nombre_archivo, :ruta_imagen, :formato, :fecha);
-- Devuelve: id_prueba (el id de la prueba recién creada)
"""

POST_RESULTADO = """
-- =====================================================
-- CONSULTA: POST_RESULTADO
-- Descripción: Registra un resultado (indicador detectado) asociado a una prueba.
-- Parámetros esperados:
    INSERT INTO Resultado (id_prueba, id_indicador, confianza, x_min, x_max, y_min, y_max)
    VALUES (:id_prueba, :id_indicador, :confianza, :x_min, :x_max, :y_min, :y_max);
"""