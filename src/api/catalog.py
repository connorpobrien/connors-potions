from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Retrieves the catalog of items. Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
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
                            """
        catalog = connection.execute(sqlalchemy.text(combined_query)).fetchall()

        # build output list
        res = []
        for item in catalog:
            sku, name, price, red_ml, green_ml, blue_ml, dark_ml, quantity = item
            if item.quantity > 0:
                res.append({"sku": item.sku, "name": item.name, "quantity": item.quantity, "price": item.price, "potion_type": [item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml]})
                print(f'''Item in catalog: \n sku: {item.sku} \n name: {item.name} \n quantity: {item.quantity} \n price: {item.price} \n potion_type: {item.num_red_ml, item.num_green_ml, item.num_blue_ml, item.num_dark_ml}''')

        return res