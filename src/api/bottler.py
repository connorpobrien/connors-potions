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
    # print(potions_delivered)

    # Based on how many potions were delivered, update the inventory

    for potion in potions_delivered:
        # Red potions
        if potion.potion_type == [100, 0, 0, 0]:
            # Reduce num_red_ml
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_red_ml = num_red_ml - {potion.quantity*100}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Increase num_red_potions
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_red_potions = num_red_potions + {potion.quantity}"""
                connection.execute(sqlalchemy.text(sql_query))

        # Green Potions
        if potion.potion_type == [0, 100, 0, 0]:
            # Reduce num_green_ml
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_green_ml = num_green_ml - {potion.quantity*100}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Increase num_green_potions
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_green_potions = num_green_potions + {potion.quantity}"""
                connection.execute(sqlalchemy.text(sql_query))

        # Blue potions
        if potion.potion_type == [0, 0, 100, 0]:
            # Reduce num_blue_ml
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_blue_ml = num_blue_ml - {potion.quantity*100}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Increase num_blue_potions
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potion.quantity}"""
                connection.execute(sqlalchemy.text(sql_query))

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

    # New logic to create red, green, and blue potions

    # Get the num_ml for each color that is available
    with db.engine.begin() as connection:
        sql_query = """SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))   
        first_row = result.first()  
        num_red_ml_available = first_row.num_red_ml
        num_green_ml_available = first_row.num_green_ml
        num_blue_ml_available = first_row.num_blue_ml

    # Bottle as many as possible for each color
    res = []
    if num_red_ml_available > 99:
        res.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": num_red_ml_available // 100
        })
        # Update table to deduct the number of red ml
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET num_red_ml = num_red_ml - {num_red_ml_available // 100 * 100}"""
            connection.execute(sqlalchemy.text(sql_query))

    if num_green_ml_available > 99:
        res.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": num_green_ml_available // 100
        })
        # Update table to deduct the number of green ml
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET num_green_ml = num_green_ml - {num_green_ml_available // 100 * 100}"""
            connection.execute(sqlalchemy.text(sql_query))

    if num_blue_ml_available > 99:
        res.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": num_blue_ml_available // 100
        })
        # Update table to deduct the number of blue ml
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET num_blue_ml = num_blue_ml - {num_blue_ml_available // 100 * 100}"""
            connection.execute(sqlalchemy.text(sql_query))
    
    return res
