from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    # Based on how many potions were delivered, update the inventory

    for potion in potions_delivered:
        # Dealing with red potions only now
        if potion.potion_type == [100, 0, 0, 0]:
            # Reduce num_red_ml
            with db.engine.begin() as connection:
                sql_query = """UPDATE global_inventory SET num_red_ml = num_red_ml - :quantity"""
                connection.execute(sqlalchemy.text(sql_query), quantity=potion.quantity*100)

            # Increase num_red_potions
            with db.engine.begin() as connection:
                sql_query = """UPDATE global_inventory SET num_red_potions = num_red_potions + :quantity"""
                connection.execute(sqlalchemy.text(sql_query), quantity=potion.quantity)

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    # Get the number of red_ml available
    with db.engine.begin() as connection:
        sql_query = """SELECT num_red_ml FROM global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))   
        first_row = result.first()  
        num_red_ml_available = first_row.num_red_ml

    # Find how many red potions can be created
    create_potions = num_red_ml_available // 100
    
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": create_potions
            }
        ]

