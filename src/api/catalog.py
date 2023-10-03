from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # Get the number of potions available
    with db.engine.begin() as connection:
        sql_query = """SELECT num_red_potions, num_green_potions, num_blue_potions from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))  
        first_row = result.first()
        num_red_potions = first_row.num_red_potions
        num_green_potions = first_row.num_green_potions
        num_blue_potions = first_row.num_blue_potions

    # Adding logic for buying red, green, and blue potions
    # For now only can buy one

    res = []
    
    if num_red_potions > 0:
        res.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": 1,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        })

    if num_green_potions > 0:
        res.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": 1,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })

    if num_blue_potions > 0:
        res.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": 1,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        })
    
    return res
