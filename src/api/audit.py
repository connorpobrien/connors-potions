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
    """ """
    # Call database to update return
    with db.engine.begin() as connection:
        sql_query = """SELECT 
                            SUM(num_red_potions + num_green_potions + num_blue_potions) AS total_potions,
                            SUM(num_red_ml + num_green_ml + num_blue_ml) AS total_ml,
                            SUM(gold) AS gold
                        FROM 
                            global_inventory;
                        """
        results = connection.execute(sqlalchemy.text(sql_query))
        first_row = results.first()
    
    return {"number_of_potions": first_row.total_potions, "ml_in_barrels": first_row.total_ml, "gold": first_row.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
