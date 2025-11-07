GET_GRUPOS = (
	"SELECT g.nombre AS Nombre, g.id_grupo AS ID, g.direccion AS Dirección, g.parent_id AS 'Grupo Padre', "
	"m.nombre AS Municipio "
	"FROM Grupo g "
	"LEFT JOIN Municipio m ON g.id_municipio = m.id_municipio"
)

CREATE_SUBGRUPO = """
-- =====================================================
INSERT INTO Grupo (parent_id, id_municipio, nombre, direccion)
VALUES (%s, %s, %s, %s)
"""

CREATE_GRUPO = """
-- =====================================================
INSERT INTO Grupo (id_municipio, nombre, direccion)
VALUES (%s, %s, %s)
"""