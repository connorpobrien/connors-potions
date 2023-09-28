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
        sql_query = """SELECT num_red_potions from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))  
        first_row = result.first()
        num_red_potions = first_row.num_red_potions

    # Can return a max of 20 items, but for now we will only return 1

    if num_red_potions > 0:
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    
    return []

