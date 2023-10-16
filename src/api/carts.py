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

@router.post("/")
def create_cart(new_cart: NewCart):
    """ Creates a new cart for a specific customer. """
    with db.engine.begin() as connection:
        sql_query = """INSERT INTO carts (customer_name)
                        VALUES (:customer) 
                        RETURNING cart_id"""
        result = connection.execute(sqlalchemy.text(sql_query), {"customer": new_cart.customer})
    
        # The cart id is generated by the database
        cart_id = result.first().cart_id

    return {"cart_id": str(cart_id)}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ Returns the items in a customer's cart."""
    # retrieve customer's cart based on the cart_id from cart_items table
    with db.engine.begin() as connection:
        sql_query = """SELECT item_sku, quantity FROM cart_items WHERE cart_id = :cart_id"""
        result = connection.execute(sqlalchemy.text(sql_query), {"cart_id": cart_id})
        cart_items = result.fetchall()
    return cart_items

    
class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ Updates the quantity of a specific item in a cart. """

    with db.engine.begin() as connection:
        # Check if the item is already in the cart
        sql_query = """SELECT quantity FROM cart_items WHERE cart_id = :cart_id AND item_sku = :item_sku"""
        result = connection.execute(sqlalchemy.text(sql_query), {"cart_id": cart_id, "item_sku": item_sku})
        existing_item = result.fetchone()

        if existing_item:
            # If the item exists, update the quantity
            sql_query = """UPDATE cart_items SET quantity = :quantity WHERE cart_id = :cart_id AND item_sku = :item_sku"""
        else:
            # If the item doesn't exist, insert it
            sql_query = """INSERT INTO cart_items (cart_id, item_sku, quantity) VALUES (:cart_id, :item_sku, :quantity)"""

        connection.execute(sqlalchemy.text(sql_query), {"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity})
    
    return {"success": True}


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Handles the checkout process for a specific cart. """
    # Get the items in the cart
    with db.engine.begin() as connection:
        sql_query = """SELECT item_sku, quantity FROM cart_items WHERE cart_id = :cart_id"""
        result = connection.execute(sqlalchemy.text(sql_query), {"cart_id": cart_id})
        cart_items = result.fetchall()

        # update catalog
        for potion in cart_items:
            pass
            

        # calculate purchase amount - join with catalog

        purchase_cost = 0

        # update gold in global_inventory
        sql_query = """UPDATE global_inventory SET gold = gold + :purchase_cost"""  
        connection.execute(sqlalchemy.text(sql_query), {"purchase_cost": purchase_cost})

    return {"total_potions_bought": 0, "total_gold_paid": purchase_cost}

