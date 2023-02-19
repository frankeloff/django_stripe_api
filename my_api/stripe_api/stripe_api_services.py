from .models import Item, Order
from django.db.models import Sum
from typing import List
import stripe


def get_item_by_id(item_id: int) -> Item:
    item = Item.objects.get(id=item_id)
    return item


def get_all_items() -> List[Item]:
    all_items = Item.objects.all()
    return all_items


def create_customer() -> stripe.Customer:
    customer = stripe.Customer.create()
    return customer


def get_final_order_price_by_session(session_key: str) -> int:
    final_price = Order.objects.filter(session_key=session_key).aggregate(Sum("price"))[
        "price__sum"
    ]

    return final_price


def create_new_order_item(
    session_key: int, item_id: int, nmb: int, total_price: int
) -> Order:
    new_order_item = Order.objects.create(
        session_key=session_key, item_id=item_id, nmb=nmb, price=total_price
    )
    return new_order_item


def get_products_in_basket_by_session(session_key: str) -> list:
    products_in_basket = Order.objects.filter(session_key=session_key)
    return products_in_basket


def get_specific_item_by_session(session_key: str, item_id: int) -> Order:
    item = Order.objects.filter(session_key=session_key, item=item_id)
    return item


def update_item_in_order(new_order_item: Order, nmb: int, total_price: int) -> None:
    new_order_item = new_order_item[0]
    new_order_item.nmb += int(nmb)
    new_order_item.price += int(total_price)
    new_order_item.save(force_update=True)


def empty_the_cart_by_specific_item(session_key: str, item_id: int) -> None:
    products = get_specific_item_by_session(session_key=session_key, item_id=item_id)
    for product in products:
        product.delete()


def empty_the_cart(session_key: str) -> None:
    products = Order.objects.filter(session_key=session_key)
    for product in products:
        product.delete()


def create_payment_intent_for_single_order(
    customer, final_price: int, product_name: str
) -> stripe.PaymentIntent:
    intent = stripe.PaymentIntent.create(
        amount=final_price,
        currency="usd",
        automatic_payment_methods={
            "enabled": True,
        },
        customer=customer["id"],
        setup_future_usage="off_session",
        metadata={
            "items": f"{product_name} 1 piece for {final_price}$",
            "session_key": False,
        },
    )
    return intent


def create_payment_intent_for_multiple_order(
    session_key: str, customer, final_price: int, products_in_basket: list
) -> stripe.PaymentIntent:
    intent = stripe.PaymentIntent.create(
        amount=final_price,
        currency="usd",
        automatic_payment_methods={
            "enabled": True,
        },
        customer=customer["id"],
        setup_future_usage="off_session",
        metadata={
            "items": "".join(
                [
                    f"{product.item.name} {product.nmb} pieces of {product.item.price}$\n"
                    for product in products_in_basket
                ]
            )
            + f"\nFinal price: {final_price}$",
            "session_key": session_key,
        },
    )
    return intent


def get_products_in_basket_and_price_by_session(session_key: str) -> tuple:
    products_in_basket = get_products_in_basket_by_session(session_key=session_key)
    final_price = get_final_order_price_by_session(session_key=session_key)

    return (products_in_basket, final_price)


def get_return_dict_for_basket_adding(products_in_basket: list) -> dict:
    return_dict = {}
    return_dict["items"] = []

    if len(products_in_basket) > 0:
        for product in products_in_basket:
            product_dict = {}
            product_dict["id"] = product.id
            product_dict["name"] = product.item.name
            product_dict["price"] = product.price
            product_dict["nmb"] = product.nmb
            return_dict["items"].append(product_dict)

    return return_dict
