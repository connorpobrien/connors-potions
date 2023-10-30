from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum
from sqlalchemy import func

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    # set offsets
    offset = int(search_page) if search_page != "" else 0
    previous = "" if offset - 5 < 0 else str(offset - 5)
    next = 0

    # load tables from database
    metadata_obj = sqlalchemy.MetaData()
    carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=db.engine)
    catalog = sqlalchemy.Table("catalog", metadata_obj, autoload_with=db.engine)
    transactions = sqlalchemy.Table("transactions", metadata_obj, autoload_with=db.engine)
    catalog_ledger = sqlalchemy.Table("catalog_ledger", metadata_obj, autoload_with=db.engine)
    
    # set order by
    if sort_col is search_sort_options.customer_name:
        order_by = carts.c.customer_name
    elif sort_col is search_sort_options.item_sku:
        order_by = catalog.c.name
    elif sort_col is search_sort_options.line_item_total:
        order_by = 'total'
    elif sort_col is search_sort_options.timestamp:
        order_by = transactions.c.created_at
    else:
        assert False

    # set sort order
    if sort_order is search_sort_order.asc:
        order_by = sqlalchemy.asc(order_by)
    elif sort_order is search_sort_order.desc:
        order_by = sqlalchemy.desc(order_by)
    else:
        assert False

    with db.engine.begin() as connection:
        stmt = (
            sqlalchemy.select(
                transactions.c.transaction_id,
                transactions.c.created_at,
                catalog.c.sku,
                carts.c.customer_name,
                catalog_ledger.c.change,
                catalog.c.price,
                func.abs((catalog_ledger.c.change * catalog.c.price)).label('total'),
            )
            .join(catalog_ledger, catalog_ledger.c.transaction_id == transactions.c.transaction_id)
            .join(catalog, catalog.c.catalog_id == catalog_ledger.c.catalog_id)
            .join(carts, carts.c.cart_id == transactions.c.cart_id)
            .offset(offset)
            .order_by(order_by, transactions.c.transaction_id)
            .limit(5)
        )

        if customer_name != "":
            stmt = stmt.where(carts.c.customer_name.ilike(f"%{customer_name}%"))
        
        if potion_sku != "":
            stmt = stmt.where(catalog.c.sku.ilike(f"%{potion_sku}%"))

        res = []
        result = connection.execute(stmt)
        start = offset + 1
        for row in result:
            transaction_id, created_at, sku, name, change, price, total = row
            res.append({
                "line_item_id": start,
                "item_sku": sku,
                "customer_name": name,
                "line_item_total": total,
                "timestamp": created_at,
            })
            start += 1
        
        # set offset for next page
        next = str(offset + 5) if len(res) == 5 else ""
    

    return {
        "previous": previous,
        "next": next,
        "results": res,
    }

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

    print(f'''Cart generated for {new_cart.customer} with cart_id: {cart_id}''')
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ Returns the items in a customer's cart."""
    return {}

    
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

    print(f'''Item {item_sku} quantity updated to {cart_item.quantity} in cart with id = {cart_id}''')
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

        total_gold_paid = 0
        total_potions_bought = 0

        # form catalog 
        combined_query = """SELECT 
                                catalog.sku, 
                                catalog.name, 
                                catalog.price, 
                                catalog.red_ml, 
                                catalog.green_ml, 
                                catalog.blue_ml, 
                                catalog.dark_ml,
                                COALESCE(ledger.total, 0) AS quantity
                            FROM 
                                catalog
                            LEFT JOIN 
                                (SELECT 
                                    sku, 
                                    SUM(change) AS total 
                                FROM 
                                    catalog_ledger 
                                GROUP BY 
                                    sku) AS ledger
                            ON 
                                catalog.sku = ledger.sku
                            WHERE
                                catalog.sku = :item_sku
                        """
        
        for item_sku, quantity in cart_items:
            # get price
            result = connection.execute(sqlalchemy.text(combined_query), {"item_sku": item_sku})
            price = result.first().price
            total_gold_paid += price * quantity
            total_potions_bought += quantity

            # add gold transaction transactions table
            gold_transaction = """INSERT INTO transactions (description, cart_id) VALUES (:description, :cart_id) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(gold_transaction), {"description": f"""Gold spend on {item_sku}: {price * quantity}""", "cart_id": cart_id})
            transaction_id = result.fetchone()[0]

            # add gold transaction to inventory_ledger
            gold_inventory_ledger = """INSERT INTO inventory_ledger (type, change, transaction_id) VALUES (:type, :change, :transaction_id)"""
            connection.execute(sqlalchemy.text(gold_inventory_ledger), {"type": "gold", "change": price * quantity, "transaction_id": transaction_id})

            # add potion transaction to transactions table
            potion_transaction = """INSERT INTO transactions (description, cart_id) VALUES (:description, :cart_id) RETURNING transaction_id"""
            result = connection.execute(sqlalchemy.text(potion_transaction), {"description": f"""{quantity} of potion type {item_sku} sold.""", "cart_id": cart_id})

            # find catalog_id, sku from catalog table
            catalog_id_query = """SELECT catalog_id FROM catalog WHERE sku = :sku"""
            result = connection.execute(sqlalchemy.text(catalog_id_query), {"sku": item_sku})
            catalog_id = result.fetchone()[0]

            # add potion transaction to catalog_ledger
            catalog_ledger = """INSERT INTO catalog_ledger (transaction_id, catalog_id, change, sku) VALUES (:transaction_id, :catalog_id, :change, :sku)"""
            connection.execute(sqlalchemy.text(catalog_ledger), {"transaction_id": transaction_id, "catalog_id": catalog_id, "change": (-1) * quantity, "sku": item_sku})

            # set cart checked out to true
            sql_query = """UPDATE carts SET checked_out = true WHERE cart_id = :cart_id"""
            connection.execute(sqlalchemy.text(sql_query), {"cart_id": cart_id})

    print(f'''Cart with id = {cart_id} checked out with payment method {cart_checkout.payment}''')
    print(f'''Total gold paid: {total_gold_paid}''')
    print(f'''Total potions bought: {total_potions_bought}''')

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
