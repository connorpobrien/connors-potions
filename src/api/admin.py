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
    # Set gold to 100
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET gold = 100"""
        connection.execute(sqlalchemy.text(sql_query))

    # Set num_red_ml to 0
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_ml = 0"""
        connection.execute(sqlalchemy.text(sql_query))

    # Set num_red_potions to 0
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_potions = 0"""
        connection.execute(sqlalchemy.text(sql_query))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    # TODO: Change me!
    return {
        "shop_name": "connors-potions",
        "shop_owner": "Connor OBrien",
    }

