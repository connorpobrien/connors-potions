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
    """ """
    print(barrels_delivered)

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
                               gold = gold + :gold_paid,
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml""")
        connection.execute(sql_query, {"gold_paid": gold_paid, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
    
    return "OK"

    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    # get gold value from global_inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold from global_inventory"""
        gold = connection.execute(sqlalchemy.text(sql_query)).first().gold

    res = []
    # iterate through barrels and buy if possible
    for barrel in wholesale_catalog:
        if barrel.price <= gold:
            res.append({
                "sku": barrel.sku,
                "quantity": 1, # only buying one for now
            })
            # spent gold
            gold -= barrel.price
            
    # Update global_inventory with new gold value
    with db.engine.begin() as connection:
        query = sqlalchemy.text("""UPDATE global_inventory SET gold = :gold""")
        connection.execute(query, {"gold": gold})
    
    return res
        
