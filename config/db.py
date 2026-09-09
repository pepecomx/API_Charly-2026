import os

from sqlalchemy import MetaData, create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api.db")
engine = create_engine(DATABASE_URL)

meta_data=MetaData()
