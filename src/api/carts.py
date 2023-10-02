from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class NewCart(BaseModel):
    customer: str

carts = {}
count = 0


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global count
    global carts
    count += 1
    return {count: new_cart.customer}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    global count
    global carts
    print(carts)

    return carts[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global count
    global carts

    carts[cart_id][item_sku] = cart_item.quantity

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global count
    global carts

    # for now customers will only be able to buy 1 red potion
    # Update gold
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET gold = gold + 50"""
        connection.execute(sqlalchemy.text(sql_query))

    # Update number of potions
    with db.engine.begin() as connection:
        sql_query = """UPDATE global_inventory SET num_red_potions = num_red_potions + 1"""
        connection.execute(sqlalchemy.text(sql_query))

    return {"total_potions_bought": 1, "total_gold_paid": 50}

