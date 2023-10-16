from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
import string

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

    # query catalog
    with db.engine.begin() as connection:
        sql_query = """SELECT id, sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM catalog"""
        catalog = connection.execute(sqlalchemy.text(sql_query)).fetchall()

    # Based on how many potions were delivered, update the catalog and global_inventory
    for potion in potions_delivered:
        red_ml, green_ml, blue_ml, dark_ml = potion.potion_type
        sku = name = f"{red_ml}_{green_ml}_{blue_ml}_{dark_ml}"
        quantity = potion.quantity

        # determine id from catalog based on sku
        for item in catalog:
            if item.sku == sku:
                id = item.id
                break

        # update catalog
        with db.engine.begin() as connection:
            # insert values into catalog - conflict based on id 
            sql_query = """INSERT INTO catalog (id, sku, name, price, quantity, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml)
                            VALUES (:id, :sku, :name, :quantity, :price, :red_ml, :green_ml, :blue_ml, :dark_ml) 
                            ON CONFLICT (id) DO UPDATE SET quantity = catalog.quantity + :quantity"""
            connection.execute(sqlalchemy.text(sql_query), {"id": id, "sku": sku, "name": name, "price": 1, "quantity": quantity, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})

        # Update global_inventory
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET 
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml"""
            connection.execute(sql_query, {"red_ml": red_ml * quantity, "green_ml": green_ml * quantity, "blue_ml": blue_ml * quantity, "dark_ml": dark_ml * quantity})

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

    # query global

    # query catalog - determine which potions in catalog need more bottles

    # update catalog

    # update global

    # return bottle plan

    return "OK"

