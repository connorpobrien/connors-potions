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
    """"""
    print("Bottles Delivered!")

    # Based on how many potions were delivered, update the catalog and global_inventory
    for potion in potions_delivered:
        print(f'''potion_type: {potion.potion_type} \n quantity: {potion.quantity}''')
        red_ml, green_ml, blue_ml, dark_ml = potion.potion_type
        quantity = potion.quantity

        # update catalog
        with db.engine.begin() as connection:
            # insert values into catalog - conflict based on id 
            sql_query = """UPDATE catalog SET quantity = quantity + :quantity
                           WHERE 
                           num_red_ml = :red_ml AND 
                           num_green_ml = :green_ml AND 
                           num_blue_ml = :blue_ml AND 
                           num_dark_ml = :dark_ml"""
            connection.execute(sqlalchemy.text(sql_query), {"quantity": quantity, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})

        # Update global_inventory
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET 
                            num_red_ml = num_red_ml - :red_ml,
                            num_green_ml = num_green_ml - :green_ml,
                            num_blue_ml = num_blue_ml - :blue_ml,
                            num_dark_ml = num_dark_ml - :dark_ml"""
            connection.execute(sqlalchemy.text(sql_query), {"red_ml": red_ml * quantity, "green_ml": green_ml * quantity, "blue_ml": blue_ml * quantity, "dark_ml": dark_ml * quantity})

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        # query global
        sql_query = """SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
        global_inventory = connection.execute(sqlalchemy.text(sql_query)).first()
        inventory_red_ml, inventory_green_ml, inventory_blue_ml, inventory_dark_ml = global_inventory
        print(f'''Inventory: red_ml: {inventory_red_ml} green_ml: {inventory_green_ml} blue_ml: {inventory_blue_ml} dark_ml: {inventory_dark_ml}''')

    with db.engine.begin() as connection:
        # query catalog
        sql_query = """SELECT sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM catalog"""
        catalog = connection.execute(sqlalchemy.text(sql_query)).fetchall()
        
    # sort to find potions to replenish
    catalog = sorted(catalog, key=lambda x: x.quantity)
    # disregard potions that have dark_ml for now
    catalog = [item for item in catalog if item.num_dark_ml == 0]

    bottle_plan = {}

    # Make as many potions as possible
    while True:
        create_potion = False
        # make potions
        for item in catalog:
            sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml = item
            # if possible
            if (inventory_red_ml >= red_ml) and (inventory_green_ml >= green_ml) and (inventory_blue_ml >= blue_ml) and (inventory_dark_ml >= dark_ml):
                print(f"""inventory_red_ml: {inventory_red_ml} red_ml: {red_ml}, inventory_green_ml: {inventory_green_ml} green_ml: {green_ml}, inventory_blue_ml: {inventory_blue_ml} blue_ml: {blue_ml}, inventory_dark_ml: {inventory_dark_ml} dark_ml: {dark_ml}""")
                # add to bottle plan
                potion_type = (red_ml, green_ml, blue_ml, dark_ml)
                if potion_type not in bottle_plan and len(bottle_plan) == 6:
                    continue
                if potion_type in bottle_plan:
                    bottle_plan[potion_type]["quantity"] += 1
                else:
                    bottle_plan[potion_type] = {"potion_type": potion_type, "quantity": 1}
                    
                create_potion = True
                # update inventory
                inventory_red_ml -= red_ml
                inventory_green_ml -= green_ml
                inventory_blue_ml -= blue_ml
                inventory_dark_ml -= dark_ml
            if len(bottle_plan) == 6:
                break
        if not create_potion:
            break
        # randomize order of catalog for next iteration
        random.shuffle(catalog)

    # print bottle plan
    for bottle in bottle_plan.values():
        print(f'''potion_type: {bottle["potion_type"]} quantity: {bottle["quantity"]}''')

    # return bottle plan, max length 6
    return list(bottle_plan.values())[:6]

    

