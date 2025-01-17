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
    # for potion in potions_delivered:
    #     print(f'''potion_type: {potion.potion_type} \n quantity: {potion.quantity}''')

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red_ml, green_ml, blue_ml, dark_ml = potion.potion_type
            quantity = potion.quantity

            # add transaction to transactions table
            potion_transaction = """INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(potion_transaction), {"description": f"""Delivered {quantity} of potion type {potion.potion_type}"""})
            transaction_id = result.fetchone()[0]

            # for each type of ml, add a row to inventory_ledger
            inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
            connection.execute(sqlalchemy.text(inventory_ledger), {"type": "red_ml", "change": (-1) * red_ml * quantity, "transaction_id": transaction_id})
            connection.execute(sqlalchemy.text(inventory_ledger), {"type": "green_ml", "change": (-1) * green_ml * quantity, "transaction_id": transaction_id})
            connection.execute(sqlalchemy.text(inventory_ledger), {"type": "blue_ml", "change": (-1) * blue_ml * quantity, "transaction_id": transaction_id})
            connection.execute(sqlalchemy.text(inventory_ledger), {"type": "dark_ml", "change": (-1) * dark_ml * quantity, "transaction_id": transaction_id})

            # find catalog_id, sku from catalog table
            catalog_id_query = """SELECT catalog_id, sku FROM catalog WHERE red_ml = :red_ml AND green_ml = :green_ml AND blue_ml = :blue_ml AND dark_ml = :dark_ml"""
            result = connection.execute(sqlalchemy.text(catalog_id_query), {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
            catalog_id, sku = result.fetchone()

            # add potion transaction to catalog_ledger
            catalog_ledger = """INSERT INTO catalog_ledger (transaction_id, catalog_id, change, sku) VALUES (:transaction_id, :catalog_id, :change, :sku)"""
            connection.execute(sqlalchemy.text(catalog_ledger), {"transaction_id": transaction_id, "catalog_id": catalog_id, "change": quantity, "sku": sku})

        return "OK"
    

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        # Get gold, red_ml, green_ml, blue_ml, dark_ml from inventory_ledger
        inventory_ledger_query = """SELECT SUM(change) AS total FROM inventory_ledger WHERE type = :type"""
        gold = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "gold"}).first()[0] or 0
        inventory_red_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "red_ml"}).first()[0] or 0
        inventory_green_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "green_ml"}).first()[0] or 0
        inventory_blue_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "blue_ml"}).first()[0] or 0
        inventory_dark_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "dark_ml"}).first()[0] or 0

        # form catalog
        combined_query = """SELECT 
                                catalog.sku, 
                                catalog.name, 
                                catalog.price, 
                                catalog.red_ml, 
                                catalog.green_ml, 
                                catalog.blue_ml, 
                                catalog.dark_ml,
                                COALESCE(ledger.total, 0) AS quantity
                            FROM 
                                catalog
                            LEFT JOIN 
                                (SELECT 
                                    sku, 
                                    SUM(change) AS total 
                                FROM 
                                    catalog_ledger 
                                GROUP BY 
                                    sku) AS ledger
                            ON 
                                catalog.sku = ledger.sku
                            WHERE 
                                catalog.sku IN ('100_0_0_0', '0_100_0_0', '0_0_100_0', '0_0_0_100', '50_50_0_0', '50_0_50_0', '50_0_0_50', '0_50_0_50', '0_0_50_50')
                        """
        catalog = connection.execute(sqlalchemy.text(combined_query)).fetchall()

        # get total_potions from catalog_ledger
        catalog_ledger_query = """SELECT SUM(change) AS total FROM catalog_ledger"""
        total_potions = connection.execute(sqlalchemy.text(catalog_ledger_query)).first()[0] or 0

    # sort to find potions to replenish
    catalog = sorted(catalog, key=lambda x: x.quantity)

    print(catalog)

    bottle_plan = {}

    # Make as many potions as possible
    while total_potions < 300:
        create_potion = False
        
        # make potions
        for item in catalog:
            # get attributes
            sku, name, price, red_ml, green_ml, blue_ml, dark_ml, quantity = item

            # if there are enough ml
            if (inventory_red_ml >= red_ml) and (inventory_green_ml >= green_ml) and (inventory_blue_ml >= blue_ml) and (inventory_dark_ml >= dark_ml):

                # define potion type
                potion_type = (red_ml, green_ml, blue_ml, dark_ml)

                # if potion type is not in bottle plan and there are already 6 types of potions, skip
                if potion_type not in bottle_plan and len(bottle_plan) == 6:
                    continue

                # increment
                if potion_type in bottle_plan:
                    bottle_plan[potion_type]["quantity"] += 1

                # initialize
                else:
                    bottle_plan[potion_type] = {"potion_type": potion_type, "quantity": 1}
                    
                create_potion = True
                # update inventory
                inventory_red_ml -= red_ml
                inventory_green_ml -= green_ml
                inventory_blue_ml -= blue_ml
                inventory_dark_ml -= dark_ml

                # increase total potions
                total_potions += 1

            if total_potions == 300:
                break
        if not create_potion:
            break

    print(bottle_plan.values())

    # return bottle plan, max length 6
    return list(bottle_plan.values())