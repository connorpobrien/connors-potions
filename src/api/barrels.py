from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


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
    # -- ✅✅✅ -- #
    """ """
    print(barrels_delivered)
    # store in prints table
    with db.engine.begin() as connection:
        sql_query = """INSERT INTO prints (category, print_statement)
                        VALUES ('barrels', :barrels_delivered)"""
        connection.execute(sqlalchemy.text(sql_query), {"barrels_delivered": barrels_delivered})

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
        
    print(f"gold_paid: {gold_paid} red_ml: {red_ml} green_ml: {green_ml} blue_ml: {blue_ml} dark_ml: {dark_ml}")

    with db.engine.begin() as connection:
        sql_query = sqlalchemy.text("""UPDATE global_inventory SET 
                               gold = gold - :gold_paid,
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml""")
        connection.execute(sql_query, {"gold_paid": gold_paid, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
    
    return "OK"

    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    # -- ✅✅✅ -- #
    """ """
    print(wholesale_catalog)
    # store in prints table
    with db.engine.begin() as connection:
        sql_query = """INSERT INTO prints (category, print_statement)
                        VALUES ('wholesale_catalog', :wholesale_catalog)"""
        connection.execute(sqlalchemy.text(sql_query), {"wholesale_catalog": wholesale_catalog})

    '''
    wholesale_catalog format:
    [
    {
        "sku": "string",
        "ml_per_barrel": 100,
        "potion_type": [
        1, 0, 0, 0
        ],
        "price": 1,
        "quantity": 1
    }
    ]
    '''

    # get gold value from global_inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
        inventory = connection.execute(sqlalchemy.text(sql_query)).first()
        gold, red_ml, green_ml, blue_ml, dark_ml = inventory

    # sort whole sale primarily by catalog ml_per_barrel, small to large
    wholesale_catalog = sorted(wholesale_catalog, key=lambda x: x.ml_per_barrel)
    print(wholesale_catalog)

    res = []
    # if any of red, green, blue, or dark are less than 100 in global inventory, buy the smallest barrel of that type
    if red_ml < 100:
        for barrel in wholesale_catalog:
            if barrel.potion_type == [1, 0, 0, 0]:
                if gold >= barrel.price:
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # spent gold
                    gold -= barrel.price
                    print("Barrel puchased: ", barrel)
                    break
    if green_ml < 100:
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0]:
                if gold >= barrel.price:
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    # spent gold
                    gold -= barrel.price
                    print("Barrel puchased: ", barrel)
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
                    print("Barrel puchased: ", barrel)
                    break

    # iterate through rest of barrels and buy if possible
    for barrel in wholesale_catalog:
        if barrel.price <= gold:
            res.append({
                "sku": barrel.sku,
                "quantity": 1, # only buying one for now
            })
            # spent gold
            gold -= barrel.price
            print("Barrel puchased: ", barrel)
    
    return res
        
