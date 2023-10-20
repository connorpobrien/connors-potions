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

    with db.engine.begin() as connection:
        # count gold paid and ml delivered
        gold_paid, red_ml, green_ml, blue_ml, dark_ml, type = 0, 0, 0, 0, 0, None
        for barrel in barrels_delivered:
            gold_paid += gold_paid
            if barrel.potion_type == [1, 0, 0, 0]: # Red barrel
                red_ml += barrel.ml_per_barrel * barrel.quantity
                type = "red_ml"
            elif barrel.potion_type == [0, 1, 0, 0]: # Green barrel
                green_ml += barrel.ml_per_barrel * barrel.quantity
                type = "green_ml"
            elif barrel.potion_type == [0, 0, 1, 0]: # Blue barrel
                blue_ml += barrel.ml_per_barrel * barrel.quantity
                type = "blue_ml"
            elif barrel.potion_type == [0, 0, 0, 1]: # Dark barrel
                dark_ml += barrel.ml_per_barrel * barrel.quantity
                type = "dark_ml"
            else:
                raise Exception("Invalid potion type")
            
            # add gold transaction to transaction table
            gold_transaction = """INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(gold_transaction), {"description": f"""Gold spend on {barrel.sku}: {barrel.price * barrel.quantity}"""})
            transaction_id = result.fetchone()[0]

            # add gold transaction to inventory_ledger 
            gold_inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
            connection.execute(sqlalchemy.text(gold_inventory_ledger), {"type": "gold", "change": (-1) * barrel.price * barrel.quantity, "transaction_id": transaction_id})

            # add ml transaction to transaction table
            ml_transaction = """INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(ml_transaction), {"description": f"""{type} delivered: {barrel.ml_per_barrel * barrel.quantity} from {barrel.sku}"""})
            transaction_id = result.fetchone()[0]

            # add ml transaction to inventory_ledger
            ml_inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
            connection.execute(sqlalchemy.text(ml_inventory_ledger), {"type": type, "change": barrel.ml_per_barrel * barrel.quantity, "transaction_id": transaction_id})

        print(f'''Barrels delivered. \n gold_paid: {gold_paid} \n red_ml_received: {red_ml} \n green_ml_received: {green_ml} \n blue_ml_received: {blue_ml} \n dark_ml_received: {dark_ml}''')

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

    # Use inventory ledger to get gold and ml 
    # inventory_ledger_query = """SELECT type, SUM(change) AS total FROM inventory_ledger GROUP BY type"""
    # inventory_ledger = connection.execute(sqlalchemy.text(inventory_ledger_query))
    # inventory = {row.type: row.total for row in inventory_ledger}
    # gold = inventory.get("gold", 0)
    # num_red_ml = inventory.get("red_ml", 0)
    # num_green_ml = inventory.get("green_ml", 0)
    # num_blue_ml = inventory.get("blue_ml", 0)
    # num_dark_ml = inventory.get("dark_ml", 0)
    # print(f'''Inventory calculated from ledger: \n gold: {gold} \n num_red_ml: {num_red_ml} \n num_green_ml: {num_green_ml} \n num_blue_ml: {num_blue_ml} \n num_dark_ml: {num_dark_ml}''')

    # get gold value from global_inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
        inventory = connection.execute(sqlalchemy.text(sql_query)).first()
        gold, red_ml, green_ml, blue_ml, dark_ml = inventory

    print(f'''Current global inventory: \n gold: {gold} \n red_ml: {red_ml} \n green_ml: {green_ml} \n blue_ml: {blue_ml} \n dark_ml: {dark_ml}''')

    # sort whole sale primarily by catalog
    wholesale_catalog = sorted(wholesale_catalog, key=lambda x: x.price)

    # buy as many barrels as possible
    res = []
    while True:
        barrel_purchased = False
        for barrel in wholesale_catalog:
            if barrel.price <= gold and barrel.quantity > 0:
                res.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
                barrel_purchased = True
                # update tracking gold and barrels quanitity in catalog
                gold -= barrel.price
                barrel.quantity -= 1
                print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')
        if not barrel_purchased:
            break


    return res
        
