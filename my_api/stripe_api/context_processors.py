from .stripe_api_services import get_products_in_basket_by_session

def getting_basket_info(request):
    session_key = request.session.session_key
    if not session_key:
        request.session["session_key"] = 123
        request.session.cycle_key()

    products_in_basket = get_products_in_basket_by_session(session_key=session_key)
    products_total_nmb = products_in_basket.count()

    return {
        "products_in_basket": products_in_basket,
        "products_total_nmb": products_total_nmb,
    }
