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

    with db.engine.begin() as connection:
        # count gold paid and ml delivered
        gold_paid, red_ml, green_ml, blue_ml, dark_ml = 0, 0, 0, 0, 0
        for barrel_delivered in barrels_delivered:
            gold_paid += barrel_delivered.price * barrel_delivered.quantity
            if barrel_delivered.potion_type == [1, 0, 0, 0]: # Red barrel
                red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
                # add gold transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Gold spend on {barrel_delivered.sku}: {barrel_delivered.price * barrel_delivered.quantity}"})

                # add gold transaction to inventory ledger - use primary key 'transaction_id' created from transaction table as foreign key
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('gold', :gold_paid, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"gold_paid": barrel_delivered.price * barrel_delivered.quantity})

                # add red_ml transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Red ml delivered: {barrel_delivered.ml_per_barrel * barrel_delivered.quantity}"})

                # add red_ml transaction to inventory ledger - use primary key 'transaction_id' created from transaction table as foreign key
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('red_ml', :red_ml, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"red_ml": barrel_delivered.ml_per_barrel * barrel_delivered.quantity})

            elif barrel_delivered.potion_type == [0, 1, 0, 0]: # Green barrel
                green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
                # add gold transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Gold spend on {barrel_delivered.sku}: {barrel_delivered.price * barrel_delivered.quantity}"})

                # add gold transaction to inventory ledger - use primary key 'transaction_id' created from transaction table as foreign key
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('gold', :gold_paid, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"gold_paid": barrel_delivered.price * barrel_delivered.quantity})

                # add green_ml transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Green ml delivered: {barrel_delivered.ml_per_barrel * barrel_delivered.quantity}"})

                # add green_ml transaction to inventory ledger - use primary key 'transaction_id' created from transaction table as foreign key
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('green_ml', :green_ml, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"green_ml": barrel_delivered.ml_per_barrel * barrel_delivered.quantity})

            elif barrel_delivered.potion_type == [0, 0, 1, 0]: # Blue barrel
                blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
                # add gold transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Gold spend on {barrel_delivered.sku}: {barrel_delivered.price * barrel_delivered.quantity}"})

                # add gold transaction to inventory ledger - use primary key 'transaction_id' created from transaction table as foreign key
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('gold', :gold_paid, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"gold_paid": barrel_delivered.price * barrel_delivered.quantity})

                # add blue_ml transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Blue ml delivered: {barrel_delivered.ml_per_barrel * barrel_delivered.quantity}"})

                # add blue_ml transaction to inventory ledger 
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('blue_ml', :blue_ml, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"blue_ml": barrel_delivered.ml_per_barrel * barrel_delivered.quantity})

            elif barrel_delivered.potion_type == [0, 0, 0, 1]: # Dark barrel
                dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
                # add gold transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Gold spend on {barrel_delivered.sku}: {barrel_delivered.price * barrel_delivered.quantity}"})

                # add gold transaction to inventory ledger 
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('gold', :gold_paid, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"gold_paid": barrel_delivered.price * barrel_delivered.quantity})

                # add dark_ml transaction to transaction table
                sql_query = sqlalchemy.text("""INSERT INTO transactions (description)
                                                VALUES (:description)""")
                connection.execute(sql_query, {"description": f"Dark ml delivered: {barrel_delivered.ml_per_barrel * barrel_delivered.quantity}"})

                # add dark_ml transaction to inventory ledger 
                sql_query = sqlalchemy.text("""INSERT INTO inventory_ledger (type, change, transaction_id)
                                                VALUES ('dark_ml', :dark_ml, (SELECT MAX(transaction_id) FROM transactions))""")
                connection.execute(sql_query, {"dark_ml": barrel_delivered.ml_per_barrel * barrel_delivered.quantity})
                
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
        
