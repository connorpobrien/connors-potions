from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        # Reset gold to 100. Set all ml to 0
        sql_query = """UPDATE global_inventory SET gold = 10000,
                                                num_red_ml = 0,
                                                num_blue_ml = 0,
                                                num_green_ml = 0,
                                                num_dark_ml = 0"""
        connection.execute(sqlalchemy.text(sql_query))

        # Set number of potions to 0


        # Delete all carts and cart items
        sql_query = """DELETE FROM carts"""
        connection.execute(sqlalchemy.text(sql_query))

        sql_query = """DELETE FROM cart_items"""
        connection.execute(sqlalchemy.text(sql_query))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    return {
        "shop_name": "connors-potions",
        "shop_owner": "Connor OBrien",
    }

