# Query para obtener todos los indicadores
GET_ALL_INDICADORES = """
    SELECT i.id_indicador,
           i.nombre,
           i.significado,
           i.id_categoria,
           c.nombre AS categoria
    FROM Indicador i
    LEFT JOIN Categoria c ON i.id_categoria = c.id_categoria
    ORDER BY i.nombre
"""

# Query para obtener un indicador por nombre
GET_INDICADOR_BY_NOMBRE = """
    SELECT id_indicador, nombre, significado
    FROM Indicador
    WHERE nombre = @nombre
"""

# Query para obtener un indicador por ID
GET_INDICADOR_BY_ID = """
    SELECT id_indicador, nombre, significado
    FROM Indicador
    WHERE id_indicador = @id_indicador
"""

# Query para insertar un nuevo indicador
INSERT_INDICADOR = """
    INSERT INTO Indicador (nombre, significado, id_categoria)
    VALUES (@nombre, @significado, @id_categoria)
"""

# Query para actualizar un indicador
UPDATE_INDICADOR = """
    UPDATE Indicador
    SET nombre = @nombre,
        significado = @significado,
        id_categoria = @id_categoria
    WHERE id_indicador = @id_indicador
"""

# Query para eliminar un indicador
DELETE_INDICADOR = """
    DELETE FROM Indicador
    WHERE id_indicador = @id_indicador
"""