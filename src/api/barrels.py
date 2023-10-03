from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """

    # Determine how many were delivered, reduce gold and increase num_ml appropriately

    # Get the number of ml for each color and amount of gold in inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold, num_red_ml, num_green_ml, num_blue_ml from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))
        first_row = result.first()
        num_red_ml = first_row.num_red_ml
        num_green_ml = first_row.num_green_ml
        num_blue_ml = first_row.num_blue_ml
        gold = first_row.gold

    # for each barrel that was delivered, reduce gold and increase red_ml appropriately
    for barrel in barrels_delivered:
        # Red
        if barrel.potion_type == [100, 0, 0, 0]:
            # Reduce gold
            new_gold = gold - barrel.price
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET gold = {new_gold}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Update num_red_ml
            new_red_ml = num_red_ml + barrel.ml_per_barrel
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_red_ml = {new_red_ml}"""
                connection.execute(sqlalchemy.text(sql_query))
        # Green
        elif barrel.potion_type == [0, 100, 0, 0]:
            # Reduce gold
            new_gold = gold - barrel.price
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET gold = {new_gold}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Update num_green_ml
            new_green_ml = num_green_ml + barrel.ml_per_barrel
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_green_ml = {new_green_ml}"""
                connection.execute(sqlalchemy.text(sql_query))
        # Blue
        elif barrel.potion_type == [0, 0, 100, 0]:
            # Reduce gold
            new_gold = gold - barrel.price
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET gold = {new_gold}"""
                connection.execute(sqlalchemy.text(sql_query))

            # Update num_blue_ml
            new_blue_ml = num_blue_ml + barrel.ml_per_barrel
            with db.engine.begin() as connection:
                sql_query = f"""UPDATE global_inventory SET num_blue_ml = {new_blue_ml}"""
                connection.execute(sqlalchemy.text(sql_query))
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # print(wholesale_catalog)

    with db.engine.begin() as connection:
        # Get the number of potions in inventory for each color
        sql_query = """SELECT num_red_potions, num_green_potions, num_blue_potions from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))  
        first_row = result.first()
        num_red_potions = first_row.num_red_potions
        num_green_potions = first_row.num_green_potions
        num_blue_potions = first_row.num_blue_potions

    # Purchase a new small potion barrel only if the number of potions in inventory is less than 10
    res = []
    if num_red_potions < 10:
        res.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        })
    if num_green_potions < 10:
        res.append({
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        })
    if num_blue_potions < 10:
        res.append({
            "sku": "SMALL_BLUE_BARREL",
            "quantity": 1,
        })

    return res

