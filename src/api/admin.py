from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
import string

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    # -- ✅✅✅ -- #
    """
    A call to reset shop will delete all inventory and in-flight 
    carts and reset gold back to 100.
    """
    with db.engine.begin() as connection:
        # Reset gold to 100. Set all ml to 0
        reset_global_inventory = """UPDATE global_inventory SET gold = 10000,
                                                num_red_ml = 0,
                                                num_blue_ml = 0,
                                                num_green_ml = 0,
                                                num_dark_ml = 0"""
        connection.execute(sqlalchemy.text(reset_global_inventory))
        print("Reset global inventory - Success")

        # Clear and reset catalog
        reset_catalog = """DELETE FROM catalog"""
        connection.execute(sqlalchemy.text(reset_catalog))

        possible_potions = [[100, 0, 0, 0],
                            [0, 100, 0, 0],
                            [0, 0, 100, 0],
                            [0, 0, 0, 100],
                            [50, 50, 0, 0],
                            [50, 0, 50, 0],
                            [50, 0, 0, 50],
                            [0, 50, 50, 0],
                            [0, 50, 0, 50],
                            [0, 0, 50, 50]] # I think more potion types will be added in future? Will adjust
        build_catalog = """INSERT INTO catalog (sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml)
                            VALUES (:sku, :name, :quantity, :price, :red_ml, :green_ml, :blue_ml, :dark_ml)"""
        for i in range(len(possible_potions)):
            red_ml, green_ml, blue_ml, dark_ml = possible_potions[i]
            sku = name = f"{red_ml}_{green_ml}_{blue_ml}_{dark_ml}"
            quantity = 0
            price = 1
            connection.execute(sqlalchemy.text(build_catalog), {"sku": sku, "name": name, "quantity": quantity, "price": price, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})

        print("Reset catalog - Success")

        # Delete all carts and cart items
        reset_carts_items = """DELETE FROM cart_items"""
        connection.execute(sqlalchemy.text(reset_carts_items))

        print("Reset cart items - Success")

        reset_carts = """DELETE FROM carts"""
        connection.execute(sqlalchemy.text(reset_carts))

        print("Reset carts - Success")

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    # -- ✅✅✅ -- #
    """ """
    print("Get shop info - Success")
    return {
        "shop_name": "connors-potions",
        "shop_owner": "Connor OBrien",
    }

