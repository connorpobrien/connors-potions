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

    # determine how many were delivered, reduce gold
    # For now, if delivered, reduce gold by cost of one barrel

    # Get the number of red ml and amount of gold in inventory
    with db.engine.begin() as connection:
        sql_query = """SELECT gold, num_red_ml from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))
        first_row = result.first()
        num_red_ml = first_row.num_red_ml
        gold = first_row.gold

    # for each barrel that was delivered, reduce gold and increase red_ml appropriately
    for barrel in barrels_delivered:
         # UPDATE
         pass

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        # Get the number of red potions in inventory
        sql_query = """SELECT num_red_potions from global_inventory"""
        result = connection.execute(sqlalchemy.text(sql_query))  
        first_row = result.first()
        num_red_potions = first_row.num_red_potions

    # Purchase a new small red potion barrel only if the number of potions in inventory is less than 10
    if num_red_potions < 10:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    else:
         return []

