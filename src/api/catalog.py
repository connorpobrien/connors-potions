from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Retrieves the catalog of items. Each unique item combination must have only a single price.
    """
    # query catalog
    with db.engine.begin() as connection:
        sql_query = """SELECT sku, name, quantity, price, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM catalog"""
        catalog = connection.execute(sqlalchemy.text(sql_query))
        catalog = catalog.fetchall()

    # For each row, if quantity > 0, add to return
    res = []
    for item in catalog:
        # NEW - quantity will no longer be stored in catalog table. Need to SUM() from catalog ledger using potion sku
        # find quantity based on sku from catalog_ledger table
        sql_query = """SELECT SUM(change) AS total FROM catalog_ledger WHERE sku = :sku"""
        result = connection.execute(sqlalchemy.text(sql_query), {"sku": item.sku})
        quantity = result.first().total

        if item.quantity > 0:
            res.append({"sku": item.sku, "name": item.name, "quantity": item.quantity, "price": item.price, "potion_type": [item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml]})
            print(f'''Item in catalog: \n sku: {item.sku} \n name: {item.name} \n quantity: {item.quantity} \n price: {item.price} \n potion_type: {item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml}''')

    return res