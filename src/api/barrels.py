from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

with db.engine.begin() as connection:
        result = connection.execute("SELECT * FROM global_inventory")

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

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    # Get the number of red potions available
    with db.engine.begin() as connection:
           result = connection.execute("SELECT num_red_potions FROM global_inventory")   
           inventory = result.fetchone()    
           quantity_available = inventory[0]

    # Purchase a new small red potion barrel only if the number of potions in inventory is less than 10
    if quantity_available < 10:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    else:
         return []

