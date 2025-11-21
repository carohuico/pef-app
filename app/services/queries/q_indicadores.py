# Query para obtener todos los indicadores
GET_ALL_INDICADORES = """
    SELECT id_indicador, nombre, significado
    FROM Indicador
    ORDER BY nombre
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
    INSERT INTO Indicador (nombre, significado)
    VALUES (@nombre, @significado)
"""

# Query para actualizar un indicador
UPDATE_INDICADOR = """
    UPDATE Indicador
    SET nombre = @nombre,
        significado = @significado
    WHERE id_indicador = @id_indicador
"""

# Query para eliminar un indicador
DELETE_INDICADOR = """
    DELETE FROM Indicador
    WHERE id_indicador = @id_indicador
"""