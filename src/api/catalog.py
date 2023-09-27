from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # Get the number of red potions available
    with db.engine.begin() as connection:
           result = connection.execute("SELECT num_red_potions FROM global_inventory")   
           inventory = result.fetchone()    
           quantity_available = inventory[0]

    # Can return a max of 20 items
    quantity_available = min(quantity_available, 20) 

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": quantity_available,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]

