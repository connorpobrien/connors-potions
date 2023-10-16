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
    """ """
    print(potions_delivered)

    # Based on how many potions were delivered, update the catalog and global_inventory
    for potion in potions_delivered:
        red_ml, green_ml, blue_ml, dark_ml = potion.potion_type
        quantity = potion.quantity

        # update catalog
        with db.engine.begin() as connection:
            # lambda function that generates a sku
            generate_sku = (lambda: ''.join(random.choice(string.ascii_letters + string.digits + "_") for _ in range(random.randint(1, 20))))
            # ensure sku is unique
            while True:
                sku = generate_sku()
                sql_query = """SELECT sku FROM catalog WHERE sku = :sku"""
                result = connection.execute(sqlalchemy.text(sql_query), {"sku": sku})
                if not result.first():
                    break
            
            # insert values into catalog
            pass
    

        # Update global_inventory
        with db.engine.begin() as connection:
            sql_query = f"""UPDATE global_inventory SET 
                               num_red_ml = num_red_ml + :red_ml,
                               num_green_ml = num_green_ml + :green_ml,
                               num_blue_ml = num_blue_ml + :blue_ml,
                               num_dark_ml = num_dark_ml + :dark_ml"""
            connection.execute(sql_query, {"red_ml": red_ml * quantity, "green_ml": green_ml * quantity, "blue_ml": blue_ml * quantity, "dark_ml": dark_ml * quantity})

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # query global

    # query catalog - determine which potions in catalog need more bottles

    # update catalog

    # update global

    # return bottle plan

    
    # [100, 0, 0, 0]
    # [0, 100, 0, 0]
    # [0, 0, 100, 0]
    # [0, 0, 0, 100]
    # [50, 50, 0, 0]
    # [50, 0, 50, 0]
    # [50, 0, 0, 50]
    # [0, 50, 50, 0]
    # [0, 50, 0, 50]
    # [0, 0, 50, 50]

