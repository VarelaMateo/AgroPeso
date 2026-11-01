import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DB_NAME = os.getenv("DB_NAME")
if not DB_NAME:
    raise RuntimeError("Falta DB_NAME en el archivo .env")


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER","root"),
    password=os.getenv("DB_PASSWORD",""),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=DB_NAME,
)

#Create your databases
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

#Entrega una sesión nueva por cada petición y la cierra al terminar, aunque haya habido un error.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

