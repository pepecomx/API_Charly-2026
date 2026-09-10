import os

from sqlalchemy import MetaData, create_engine


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Falta DATABASE_URL. Configure la conexion MySQL antes de iniciar la API; "
        "no se utilizara una SQLite vacia como reemplazo."
    )
connect_args = {}
if DATABASE_URL.startswith("mysql+pymysql:"):
    connect_args = {"connect_timeout": 10, "read_timeout": 30, "write_timeout": 30}
engine = create_engine(
    DATABASE_URL, pool_pre_ping=True, hide_parameters=True, connect_args=connect_args
)

meta_data=MetaData()
