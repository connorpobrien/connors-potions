from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

with db.engine.begin() as connection:
        result = connection.execute("SELECT * FROM global_inventory")

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]

with db.engine.begin() as connection:
        result = connection.execute("SELECT * FROM global_inventory")
