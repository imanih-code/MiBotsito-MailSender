

# --- Configuración y Uso ---
# Por ejemplo, para usar con SQLite (para pruebas rápidas)
# SQLALCHEMY_DATABASE_URL = "sqlite:///././test.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Para PostgreSQL (recomendado para producción)
# Ajusta estos valores a tu configuración real
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"
# engine = create_engine(SQLALCHEMY_DATABASE_URL)


# Crear las tablas en la base de datos
# Base.metadata.create_all(bind=engine)

# Configurar la sesión
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Para usarlo:
# db = SessionLocal()
# try:
#     # Crear un nuevo mensaje
#     new_message = Message(
#         subject="Mi primer correo con SQLAlchemy y Markdown",
#         to_recipients="receptor@example.com",
#         markdown_content="""Hola mundo! 👋 Este es un mensaje de **prueba** con *Markdown* y emojis.
#         \n
#         - Ítem 1
#         - Ítem 2
#         \n
#         ¡Funciona! ✨
#         """,
#         read_from_path="/path/to/my/message1.md"
#     )
#     db.add(new_message)
#     db.commit()
#     db.refresh(new_message)
#     print(f"Mensaje creado: {new_message}")

#     # Añadir una acción para el mensaje
#     new_action = MessageAction(
#         message_id=new_message.id,
#         action_type='attempt_send',
#         details={"attempt_number": 1, "service": "mailjet"},
#         next_step='wait_for_response',
#         is_successful=False
#     )
#     db.add(new_action)
#     db.commit()
#     db.refresh(new_action)
#     print(f"Acción registrada: {new_action}")

#     # Ejemplo de lectura de un mensaje y sus acciones
#     message_from_db = db.query(Message).filter(Message.id == new_message.id).first()
#     print(f"\nRecuperado: {message_from_db}")
#     for action in message_from_db.actions:
#         print(f"  - Acción: {action.action_type} @ {action.timestamp}")

# finally:
#     db.close()