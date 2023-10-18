from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import json


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
    # For each barrel delivered, print
    print("Barrels Delivered!")
    for barrel in barrels_delivered:
        print(f'''sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {barrel.quantity}''')

    # store in prints table
    barrels_json = json.dumps([barrel.dict() for barrel in barrels_delivered])
    with db.engine.begin() as connection:
        sql_query = """INSERT INTO prints (category, print_statement)
                        VALUES ('barrels', :barrels_delivered)"""
        connection.execute(sqlalchemy.text(sql_query), {"barrels_delivered": barrels_json})

    # count gold paid and ml delivered
    gold_paid, red_ml, green_ml, blue_ml, dark_ml = 0, 0, 0, 0, 0
    for barrel_delivered in barrels_delivered:
        gold_paid += barrel_delivered.price * barrel_delivered.quantity
        if barrel_delivered.potion_type == [1, 0, 0, 0]:
            red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0, 1, 0, 0]:
            green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0, 0, 1, 0]:
            blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0, 0, 0, 1]:
            dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        else:
            raise Exception("Invalid potion type")
        
    print(f"BARRELS DELIEVERD! \n gold_paid: {gold_paid} \n red_ml_received: {red_ml} \n green_ml_received: {green_ml} \n blue_ml_received: {blue_ml} \n dark_ml_received: {dark_ml}")

    # update global_inventory based on barrels that were delivered
    with db.engine.begin() as connection:
        sql_query = sqlalchemy.text("""UPDATE global_inventory SET 
                               gold = gold - :gold_paid,
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml""")
        connection.execute(sql_query, {"gold_paid": gold_paid, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
    
    print("Global inventory updated - Success")
    
    return "OK"

    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("Wholesale Catalog: ")
    for barrel in wholesale_catalog:
        print(f'''sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {barrel.quantity}''')

    # store in prints table
    wholesale_catalog_json = json.dumps([barrel.dict() for barrel in wholesale_catalog])
    with db.engine.begin() as connection:
        sql_query = """INSERT INTO prints (category, print_statement)
                        VALUES ('wholesale_catalog', :wholesale_catalog)"""
        connection.execute(sqlalchemy.text(sql_query), {"wholesale_catalog": wholesale_catalog_json})

    # get gold value from global_inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
        inventory = connection.execute(sqlalchemy.text(sql_query)).first()
        gold, red_ml, green_ml, blue_ml, dark_ml = inventory

    print(f'''Current global inventory: \n gold: {gold} \n red_ml: {red_ml} \n green_ml: {green_ml} \n blue_ml: {blue_ml} \n dark_ml: {dark_ml}''')

    # sort whole sale primarily by catalog ml_per_barrel, small to large
    wholesale_catalog = sorted(wholesale_catalog, key=lambda x: x.ml_per_barrel)

    res = []
    # if any of red, green, blue, or dark are less than 100 in global inventory, buy the smallest barrel of that type
    if red_ml < 100:
        for barrel in wholesale_catalog:
            if barrel.potion_type == [1, 0, 0, 0]:
                if gold >= barrel.price and barrel.quantity > 0:
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # spent gold
                    gold -= barrel.price
                    barrel.quantity -= 1
                    print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')
                    break
    if green_ml < 100:
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0]:
                if gold >= barrel.price and barrel.quantity > 0:
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # spent gold
                    gold -= barrel.price
                    barrel.quantity -= 1
                    print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')
                    break
    if blue_ml < 100:
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 0, 1, 0]:
                if gold >= barrel.price:
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # spent gold
                    gold -= barrel.price
                    barrel.quantity -= 1
                    print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')
                    break

    # iterate through rest of barrels and buy if possible
    for barrel in wholesale_catalog:
        if barrel.price <= gold and barrel.quantity > 0:
            res.append({
                "sku": barrel.sku,
                "quantity": 1, # only buying one for now
            })
            # spent gold
            gold -= barrel.price
            barrel.quantity -= 1
            print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')

    return res
        
