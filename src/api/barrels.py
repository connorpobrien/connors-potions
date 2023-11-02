from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import json
import random


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
    print(wholesale_catalog)

    with db.engine.begin() as connection:
         # Get gold, red_ml, green_ml, blue_ml, dark_ml from inventory_ledger
        inventory_ledger_query = """SELECT SUM(change) AS total FROM inventory_ledger WHERE type = :type"""
        gold = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "gold"}).first()[0] or 0
        red_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "red_ml"}).first()[0] or 0
        green_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "green_ml"}).first()[0] or 0
        blue_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "blue_ml"}).first()[0] or 0
        dark_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "dark_ml"}).first()[0] or 0
        total_ml = red_ml + green_ml + blue_ml + dark_ml

    # sort catalog by color
    red_catalog = sorted([b for b in wholesale_catalog if b.potion_type == [1, 0, 0, 0]], key=lambda x: x.ml_per_barrel / x.price, reverse=True)
    green_catalog = sorted([b for b in wholesale_catalog if b.potion_type == [0, 1, 0, 0]], key=lambda x: x.ml_per_barrel / x.price, reverse=True)
    blue_catalog = sorted([b for b in wholesale_catalog if b.potion_type == [0, 0, 1, 0]], key=lambda x: x.ml_per_barrel / x.price, reverse=True)
    dark_catalog = sorted([b for b in wholesale_catalog if b.potion_type == [0, 0, 0, 1]], key=lambda x: x.ml_per_barrel / x.price, reverse=True)

    print(len(red_catalog), len(green_catalog), len(blue_catalog), len(dark_catalog))


    # determine budget for each type
    redbudget = greenbudget = bluebudget = darkbudget = 0
    if gold < 200:
        redbudget = gold
    elif gold < 300:
        redbudget, greenbudget = gold-100, 100
    elif 300 <= gold < 400:
        split = gold//3
        redbudget, greenbudget, bluebudget = split, split, split
    else:
        split = gold//4
        redbudget, greenbudget, bluebudget, darkbudget = split, split, split, split

    # if len dark catalog is 0 and darkbudget is greater than 0, then
    # choose a random number 1-3 and assign the gold from darkbudget to either red, green or blue
    if len(dark_catalog) == 0 and darkbudget > 0:
        random_num = random.randint(1, 3)
        if random_num == 1:
            redbudget += darkbudget
        elif random_num == 2:
            greenbudget += darkbudget
        else:
            bluebudget += darkbudget
        darkbudget = 0

    # if current non_dark ml is above 100k, give majority budget to dark_ml
    if total_ml - dark_ml > 76000:
        redbudget, greenbudget, bluebudget = 0, 0, 0
        if gold > 10000:
            darkbudget = 10000
        else:
            darkbudget = gold


    print(f'''Budgets: \n redbudget: {redbudget} \n greenbudget: {greenbudget} \n bluebudget: {bluebudget} \n darkbudget: {darkbudget}''')

    res = {}

    # buy as many reds as possible
    while True:
        barrel_purchased = False
        for barrel in red_catalog:
            if barrel.price <= redbudget and barrel.quantity > 0:
                max_purchase_by_budget = redbudget // barrel.price
                quantity_to_purchase = min(max_purchase_by_budget, barrel.quantity)
                if barrel.sku in res:
                    res[barrel.sku]["quantity"] += quantity_to_purchase
                else:
                    res[barrel.sku] = {
                        "sku": barrel.sku,
                        "quantity": quantity_to_purchase
                    }
                barrel_purchased = True
                redbudget -= barrel.price * quantity_to_purchase
                barrel.quantity -= quantity_to_purchase
                # print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {res[barrel.sku]["quantity"]}''')
        if not barrel_purchased:
            break

    # buy as many greens as possible
    while True:
        barrel_purchased = False
        for barrel in green_catalog:
            if barrel.price <= greenbudget and barrel.quantity > 0:
                max_purchase_by_budget = greenbudget // barrel.price
                quantity_to_purchase = min(max_purchase_by_budget, barrel.quantity)
                if barrel.sku in res:
                    res[barrel.sku]["quantity"] += quantity_to_purchase
                else:
                    res[barrel.sku] = {
                        "sku": barrel.sku,
                        "quantity": quantity_to_purchase
                    }
                barrel_purchased = True
                greenbudget -= barrel.price * quantity_to_purchase
                barrel.quantity -= quantity_to_purchase
                # print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {res[barrel.sku]["quantity"]}''')
        if not barrel_purchased:
            break

    # buy as many blues as possible
    while True:
        barrel_purchased = False
        for barrel in blue_catalog:
            if barrel.price <= bluebudget and barrel.quantity > 0:
                max_purchase_by_budget = bluebudget // barrel.price
                quantity_to_purchase = min(max_purchase_by_budget, barrel.quantity)
                if barrel.sku in res:
                    res[barrel.sku]["quantity"] += quantity_to_purchase
                else:
                    res[barrel.sku] = {
                        "sku": barrel.sku,
                        "quantity": quantity_to_purchase
                    }
                barrel_purchased = True
                bluebudget -= barrel.price * quantity_to_purchase
                barrel.quantity -= quantity_to_purchase
                # print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {res[barrel.sku]["quantity"]}''')
        if not barrel_purchased:
            break

    # buy as many darks as possible
    while True:
        barrel_purchased = False
        for barrel in dark_catalog:
            if barrel.price <= darkbudget and barrel.quantity > 0:
                max_purchase_by_budget = darkbudget // barrel.price
                quantity_to_purchase = min(max_purchase_by_budget, barrel.quantity)
                if barrel.sku in res:
                    res[barrel.sku]["quantity"] += quantity_to_purchase
                else:
                    res[barrel.sku] = {
                        "sku": barrel.sku,
                        "quantity": quantity_to_purchase
                    }
                barrel_purchased = True
                darkbudget -= barrel.price * quantity_to_purchase
                barrel.quantity -= quantity_to_purchase
                # print(f'''Barrel added to purchase plan: \n sku: {barrel.sku} \n ml_per_barrel: {barrel.ml_per_barrel} \n potion_type: {barrel.potion_type} \n price: {barrel.price} \n quantity: {res[barrel.sku]["quantity"]}''')
        if not barrel_purchased:
            break

    print(res.values())
    return list(res.values()) if len(res) > 0 else []