from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """"""
    # Get values from database
    with db.engine.begin() as connection:
        # Get gold, red_ml, green_ml, blue_ml, dark_ml from inventory_ledger
        inventory_ledger_query = """SELECT SUM(change) AS total FROM inventory_ledger WHERE type = :type"""
        gold = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "gold"}).first()[0] or 0
        red_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "red_ml"}).first()[0] or 0
        green_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "green_ml"}).first()[0] or 0
        blue_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "blue_ml"}).first()[0] or 0
        dark_ml = connection.execute(sqlalchemy.text(inventory_ledger_query), {"type": "dark_ml"}).first()[0] or 0
        total_ml = red_ml + green_ml + blue_ml + dark_ml

        # get total_potions from catalog_ledger
        catalog_ledger_query = """SELECT SUM(change) AS total FROM catalog_ledger"""
        total_potions = connection.execute(sqlalchemy.text(catalog_ledger_query)).total

    print(f'''CURRENT INVENTORY: \n number_of_potions: {total_potions} \n ml_in_barrels: {total_ml} \n gold: {gold}''')
    
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(f'''AUDIT: \n gold_match: {audit_explanation.gold_match} \n barrels_match: {audit_explanation.barrels_match} \n potions_match: {audit_explanation.potions_match}''')
    return "OK"
