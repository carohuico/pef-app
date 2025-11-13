# Queries para la gestión de usuarios

# Query para obtener todos los usuarios
GET_ALL_USUARIOS = """
    SELECT 
        id_usuario,
        usuario,
        nombre_completo,
        email,
        telefono,
        rol,
        password_hash,
        ultimo_acceso
    FROM Usuario
    ORDER BY id_usuario
"""

# Query para obtener un usuario por ID
GET_USUARIO_BY_ID = """
    SELECT 
        id_usuario,
        usuario,
        nombre_completo,
        email,
        telefono,
        rol,
        password_hash,
        ultimo_acceso
    FROM Usuario
    WHERE id_usuario = :id_usuario
"""

# Query para obtener un usuario por username
GET_USUARIO_BY_USERNAME = """
    SELECT 
        id_usuario,
        usuario,
        nombre_completo,
        email,
        telefono,
        rol,
        password_hash,
        ultimo_acceso
    FROM Usuario
    WHERE usuario = :usuario
"""

# Query para obtener un usuario por email
GET_USUARIO_BY_EMAIL = """
    SELECT 
        id_usuario,
        usuario,
        nombre_completo,
        email,
        telefono,
        rol,
        password_hash,
        ultimo_acceso
    FROM Usuario
    WHERE email = :email
"""

# Query para crear un nuevo usuario
INSERT_USUARIO = """
    INSERT INTO Usuario (usuario, nombre_completo, email, telefono, rol, password_hash)
    VALUES (:usuario, :nombre_completo, :email, :telefono, :rol, :password_hash)
"""

# Query para actualizar un usuario
UPDATE_USUARIO = """
    UPDATE Usuario
    SET usuario = :usuario,
        nombre_completo = :nombre_completo,
        email = :email,
        telefono = :telefono,
        rol = :rol,
        password_hash = :password_hash
    WHERE id_usuario = :id_usuario
"""

# Query para eliminar un usuario
DELETE_USUARIO = """
    DELETE FROM Usuario
    WHERE id_usuario = :id_usuario
"""

# Query para actualizar el último acceso
UPDATE_ULTIMO_ACCESO = """
    UPDATE Usuario
    SET ultimo_acceso = CURRENT_TIMESTAMP
    WHERE id_usuario = :id_usuario
"""

GET_ESPECIALISTAS = """
    SELECT
        id_usuario,
        nombre_completo
    FROM Usuario
    WHERE rol = 'especialista'
    ORDER BY nombre_completo
"""