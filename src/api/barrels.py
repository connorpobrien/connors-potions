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

    # good to have copius logs
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
        query = sqlalchemy.text("""UPDATE global_inventory SET 
                               gold = gold + :gold_paid,
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml""")
        connection.execute(query, {"gold_paid": gold_paid, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
    

    return "OK"

    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # print(wholesale_catalog)

    # I need more gold !!
    with db.engine.begin() as connection:
        # add gold to inventory
        sql_query = """UPDATE global_inventory SET gold = gold + 10000"""
        connection.execute(sqlalchemy.text(sql_query))


    with db.engine.begin() as connection:
        # Get the number of potions in inventory for each color
        sql_query = """SELECT num_red_potions, num_green_potions, num_blue_potions from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))  
        first_row = result.first()
        num_red_potions = first_row.num_red_potions
        num_green_potions = first_row.num_green_potions
        num_blue_potions = first_row.num_blue_potions

    # Purchase a new small potion barrel only if the number of potions in inventory is less than 10
    res = []
    if num_red_potions < 10:
        res.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        })
    if num_green_potions < 10:
        res.append({
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        })
    if num_blue_potions < 10:
        res.append({
            "sku": "SMALL_BLUE_BARREL",
            "quantity": 1,
        })

    # Temporarily hard coding
    # return res
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1000,
        },
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1000,
        },
        {
            "sku": "SMALL_BLUE_BARREL",
            "quantity": 1000,
        },
    ]

