import os
import dotenv
from sqlalchemy import create_engine
import sqlalchemy
from src import database as db
from dotenv import load_dotenv 

def database_connection_url():
    load_dotenv() # load from .env file

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)