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
    count += 1
    carts[count] = {"customer": new_cart.customer, "items": {}}
    return {"cart_id": count}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    # retrieve customer's cart based on the cart_id
    global carts
    if cart_id not in carts:
        print("Cart does not exist")
        return 0
    return carts[cart_id]

    
class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global count
    global carts

    if cart_id not in carts:
        print("Cart does not exist")
        return 0
    carts[cart_id]["items"][item_sku] = cart_item.quantity

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global count
    global carts

    if cart_id not in carts:
        print("Cart does not exist")
        return 0

    cart = carts[cart_id]

    # count number of potions bought
    num_potions = sum(cart["items"].values())

    # count amount of gold paid
    amount_gold = num_potions * 1 # cost = 1 for now


    # reset cart
    carts[cart_id]["items"] = {}

    return {"total_potions_bought": num_potions, "total_gold_paid": amount_gold}

