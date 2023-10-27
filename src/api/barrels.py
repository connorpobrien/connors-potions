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
    # TODO: compute logic - test
    # For each barrel delivered, print
    print("Barrels Delivered!")
    for barrel in barrels_delivered:
        print(f'''sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {barrel.quantity}''')

    with db.engine.begin() as connection:
        # count gold paid and ml delivered
        gold_paid, red_ml, green_ml, blue_ml, dark_ml, potion_type = 0, 0, 0, 0, 0, None
        for barrel in barrels_delivered:
            gold_paid += barrel.price * barrel.quantity
            match barrel.potion_type:
                case [1, 0, 0, 0]:
                    red_ml += barrel.ml_per_barrel * barrel.quantity
                    potion_type = "red_ml"
                case [0, 1, 0, 0]:
                    green_ml += barrel.ml_per_barrel * barrel.quantity
                    potion_type = "green_ml"
                case [0, 0, 1, 0]:
                    blue_ml += barrel.ml_per_barrel * barrel.quantity
                    potion_type = "blue_ml"
                case [0, 0, 0, 1]:
                    dark_ml += barrel.ml_per_barrel * barrel.quantity
                    potion_type = "dark_ml"
                case _:
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
            result = connection.execute(sqlalchemy.text(ml_transaction), {"description": f"""{potion_type} delivered: {barrel.ml_per_barrel * barrel.quantity} from {barrel.sku}"""})
            transaction_id = result.fetchone()[0]

            # add ml transaction to inventory_ledger
            ml_inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
            connection.execute(sqlalchemy.text(ml_inventory_ledger), {"type": potion_type, "change": barrel.ml_per_barrel * barrel.quantity, "transaction_id": transaction_id})

        print(f'''Barrels delivered. \n gold_paid: {gold_paid} \n red_ml_received: {red_ml} \n green_ml_received: {green_ml} \n blue_ml_received: {blue_ml} \n dark_ml_received: {dark_ml}''')

    return "OK"
    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("Wholesale Catalog: ")
    for barrel in wholesale_catalog:
        print(f'''sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {barrel.quantity}''')

    with db.engine.begin() as connection:
        # Get gold from inventory_ledger
        inventory_ledger_query = """SELECT SUM(change) AS total FROM inventory_ledger WHERE type = :type"""
        gold = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "gold"}).first()[0] or 0

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
                gold -= barrel.price
                barrel.quantity -= 1
                print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: 1''')
        if not barrel_purchased:
            break

    return res
        
# barrel optimizer - test
