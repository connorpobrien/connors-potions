import os
import dotenv
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

def database_connection_url():
    # Retrieve the POSTGRES_URI from environment variables
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
