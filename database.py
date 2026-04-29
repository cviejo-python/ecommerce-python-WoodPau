
#Conexion con SQLite

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

#es la función que conecta SQLAlchemy con tu base de datos
engine = create_engine("sqlite:///database/productos.db", echo=False)

#Creamos la Session
SessionLocal = sessionmaker(bind=engine)

# Declaramos Base para modelos
class Base(DeclarativeBase):
    pass