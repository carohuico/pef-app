GET_GRUPOS = (
	"SELECT g.nombre AS Nombre, g.id_grupo AS ID, g.direccion AS Dirección, g.parent_id AS 'Grupo Padre', "
	"m.nombre AS Municipio "
	"FROM Grupo g "
	"LEFT JOIN Municipio m ON g.id_municipio = m.id_municipio"
)

CREATE_SUBGRUPO = """
-- =====================================================
INSERT INTO Grupo (parent_id, id_municipio, nombre, direccion)
VALUES (@parent_id, @id_municipio, @nombre, @direccion)
"""

CREATE_GRUPO = """
-- =====================================================
INSERT INTO Grupo (id_municipio, nombre, direccion)
VALUES (@id_municipio, @nombre, @direccion)
"""

# Query para eliminar subgrupos
DELETE_SUBGRUPOS = """
    DELETE FROM Grupo 
    WHERE parent_id = @id_grupo
"""

UPDATE_EVALUADOS_A_INDIVIDUALES = """
    UPDATE Evaluado 
    SET id_grupo = NULL 
    WHERE id_grupo IN (
        SELECT id_grupo FROM Grupo WHERE id_grupo = @id_grupo
        UNION
        SELECT id_grupo FROM Grupo WHERE parent_id = @id_grupo
    )
"""

# Query para eliminar grupo principal
DELETE_GRUPO = """
    DELETE FROM Grupo 
    WHERE id_grupo = @id_grupo
"""
UPDATE_GRUPO = """
UPDATE Grupo
SET nombre = @nombre, direccion = @direccion, id_municipio = @id_municipio, parent_id = @parent_id
WHERE id_grupo = @id_grupo
"""
