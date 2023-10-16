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
            connection.execute(sqlalchemy.text(sql_query), {"red_ml": red_ml * quantity, "green_ml": green_ml * quantity, "blue_ml": blue_ml * quantity, "dark_ml": dark_ml * quantity})

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    '''
    return: [
    {
        "potion_type": [r, g, b, d],
        "quantity": "integer"
    }
    ]
    '''

    bottle_plan = []

    with db.engine.begin() as connection:
        # query global
        sql_query = """SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
        global_inventory = connection.execute(sqlalchemy.text(sql_query)).first()
        inventory_red_ml, inventory_green_ml, inventory_blue_ml, inventory_dark_ml = global_inventory

    while True:
        with db.engine.begin() as connection:
            # query catalog
            sql_query = """SELECT sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM catalog"""
            catalog = connection.execute(sqlalchemy.text(sql_query)).fetchall()
        
        # sort to find potions to replenish
        catalog = sorted(catalog, key=lambda x: x.quantity)
        print(catalog)

        # if all potions already in stock
        if all(item.quantity != 0 for item in catalog):
            break

        updated = False  # flag to check if any row was updated in this iteration
        for item in catalog:
            sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml = item
            # if possible
            if (inventory_red_ml >= red_ml) and (inventory_green_ml >= green_ml) and (inventory_blue_ml >= blue_ml) and (inventory_dark_ml >= dark_ml):
                print(f"""inventory_red_ml: {inventory_red_ml} red_ml: {red_ml}, inventory_green_ml: {inventory_green_ml} green_ml: {green_ml}, inventory_blue_ml: {inventory_blue_ml} blue_ml: {blue_ml}, inventory_dark_ml: {inventory_dark_ml} dark_ml: {dark_ml}""")
                # add to bottle plan
                bottle_plan.append({"potion_type": [red_ml, green_ml, blue_ml, dark_ml], "quantity": 1})

                # update inventory
                inventory_red_ml -= red_ml
                inventory_green_ml -= green_ml
                inventory_blue_ml -= blue_ml
                inventory_dark_ml -= dark_ml

                # update catalog
                with db.engine.begin() as connection:
                    sql_query = """UPDATE catalog SET quantity = quantity + 1 WHERE sku = :sku"""
                    connection.execute(sqlalchemy.text(sql_query), {"sku": sku})

                updated = True
                break

        if not updated:  # if no row was updated, break the loop
            break


    # while True:
    #     with db.engine.begin() as connection:
    #         # query catalog
    #         sql_query = """SELECT sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM catalog"""
    #         catalog = connection.execute(sqlalchemy.text(sql_query)).fetchall()
        
    #     catalog = sorted(catalog, key=lambda x: x.quantity)

    #     # if all already have a quantity of 1, break
    #     if catalog[0].quantity == 1:
    #         break

    #     i = 0
    #     for item in catalog:
    #         sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml = item
    #         # if possible
    #         if inventory_red_ml > red_ml and inventory_green_ml > green_ml and inventory_blue_ml > blue_ml and inventory_dark_ml > dark_ml:
    #             # add to bottle plan
    #             bottle_plan.append({"potion_type": [red_ml, green_ml, blue_ml, dark_ml], "quantity": 1})

    #             # update inventory
    #             inventory_red_ml -= red_ml
    #             inventory_green_ml -= green_ml
    #             inventory_blue_ml -= blue_ml
    #             inventory_dark_ml -= dark_ml

    #             # update catalog
    #             with db.engine.begin() as connection:
    #                 sql_query = """UPDATE catalog SET quantity = quantity - 1 WHERE sku = :sku"""
    #                 connection.execute(sqlalchemy.text(sql_query), {"sku": sku})

    #             break

    #     i += 1
    #     if i == len(catalog):
    #         break

    # update global
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_ml = :red_ml, num_green_ml = :green_ml, num_blue_ml = :blue_ml, num_dark_ml = :dark_ml"""
        connection.execute(sqlalchemy.text(sql_query), {"red_ml": inventory_red_ml, "green_ml": inventory_green_ml, "blue_ml": inventory_blue_ml, "dark_ml": inventory_dark_ml})

    return bottle_plan

    

