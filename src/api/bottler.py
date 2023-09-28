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
        num_red_ml_available = result[0]

    # Find how many red potions can be created
    create_potions = num_red_ml_available // 100

    # Update num_red_potions in inventory
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_potions = num_red_potions + :create_potions"""
        connection.execute(sqlalchemy.text(sql_query), create_potions=create_potions)

    # Update num_red_ml in inventory
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_ml = num_red_ml - :num_red_ml_available"""
        connection.execute(sqlalchemy.text(sql_query), num_red_ml_available=num_red_ml_available)
    
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": create_potions
            }
        ]

