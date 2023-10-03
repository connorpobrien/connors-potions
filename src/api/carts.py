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
    # generate id
    global count
    global carts
    count += 1

    # add id -> customer to carts
    carts[count] = new_cart.customer
    return count


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # retrieve customer's cart based on the cart_id
    global count
    global carts

    # return carts[cart_id]
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global count
    global carts

    if cart_id not in carts:
        return "Cart does not exist"
    
    # else update quantity
    # else: 
    #     carts[cart_id] = cart_item.quantity

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

