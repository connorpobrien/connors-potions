from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    # -- ✅✅✅ -- #
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
        if item.quantity > 0:
            res.append({"sku": item.sku, "name": item.name, "quantity": item.quantity, "price": item.price, "potion_type": [item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml]})
            print(f'''Item in catalog: \n sku: {item.sku} \n name: {item.name} \n quantity: {item.quantity} \n price: {item.price} \n potion_type: {item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml}''')

    return res