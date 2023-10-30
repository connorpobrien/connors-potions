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
    """
    A call to reset shop will delete all inventory and in-flight 
    carts and reset gold back to 100.
    """
    with db.engine.begin() as connection:
        # DELETE cart_items, carts, catalog, catalog_ledger, inventory_ledger, transactions
        delete_cart_items = """DELETE FROM cart_items"""
        connection.execute(sqlalchemy.text(delete_cart_items))
        delete_carts = """DELETE FROM carts"""
        connection.execute(sqlalchemy.text(delete_carts))
        delete_catalog_ledger = """DELETE FROM catalog_ledger"""
        connection.execute(sqlalchemy.text(delete_catalog_ledger))
        delete_inventory_ledger = """DELETE FROM inventory_ledger"""
        connection.execute(sqlalchemy.text(delete_inventory_ledger))
        delete_transactions = """DELETE FROM transactions"""
        connection.execute(sqlalchemy.text(delete_transactions))
        delete_catalog = """DELETE FROM catalog"""
        connection.execute(sqlalchemy.text(delete_catalog))



        print("Successfully deleted all tables")

        # Process gold transaction - set to 100
        gold_transaction = """INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"""
        result = connection.execute(sqlalchemy.text(gold_transaction), {"description": f"""Reset gold to 100"""})
        transaction_id = result.fetchone()[0]
        # add gold transaction to inventory_ledger
        gold_inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
        connection.execute(sqlalchemy.text(gold_inventory_ledger), {"type": "gold", "change": 100, "transaction_id": transaction_id})

        # Rebuild catalog
        possible_potions = [[100, 0, 0, 0],
                            [0, 100, 0, 0],
                            [0, 0, 100, 0],
                            [0, 0, 0, 100],
                            [50, 50, 0, 0],
                            [50, 0, 50, 0],
                            [50, 0, 0, 50],
                            [0, 50, 0, 50],
                            [0, 0, 50, 50],
                            [25, 25, 25, 25],
                            [25, 0, 25, 50],
                            [25, 25, 50, 0],
                            [25, 50, 25, 0],
                            [25, 50, 0, 25],
                            [50, 25, 25, 0],
                            [50, 25, 0, 25],
                            [50, 0, 25, 25],
                            [75, 0, 0, 25],
                            [75, 0, 25, 0],
                            [75, 25, 0, 0]]

        for i in range(len(possible_potions)):
            red_ml, green_ml, blue_ml, dark_ml = possible_potions[i]
            sku = name = f"{red_ml}_{green_ml}_{blue_ml}_{dark_ml}"
            quantity = 0
            price = 50

            # add to catalog table
            build_catalog = """INSERT INTO catalog (sku, name, price, red_ml, green_ml, blue_ml, dark_ml)
                            VALUES (:sku, :name, :price, :red_ml, :green_ml, :blue_ml, :dark_ml)
                            RETURNING catalog_id"""
            result = connection.execute(sqlalchemy.text(build_catalog), {"sku": sku, "name": name, "price": price, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
            catalog_id = result.fetchone()[0]

            # Process transaction
            rebuild_potion_transaction = """INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(rebuild_potion_transaction), {"description": f"""Catalog: {sku} added with quantity {quantity}"""})
            transaction_id = result.fetchone()[0]

            # Add transaction to catalog_ledger
            rebuild_potion_catalog_ledger = """INSERT INTO catalog_ledger (transaction_id, catalog_id, change, sku) VALUES (:transaction_id, :catalog_id, :change, :sku)"""
            connection.execute(sqlalchemy.text(rebuild_potion_catalog_ledger), {"transaction_id": transaction_id, "catalog_id": catalog_id, "change": quantity, "sku": sku})

        print("Successfully rebuilt catalog")

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    print("Successfully retrieved shop info")
    return {
        "shop_name": "connors-potions",
        "shop_owner": "Connor OBrien",
    }

