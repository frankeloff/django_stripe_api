import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.views import View
from .stripe_api_services import (
    get_all_items,
    get_item_by_id,
    get_products_in_basket_and_price_by_session,
    empty_the_cart,
    create_customer,
    create_payment_intent_for_multiple_order,
    create_payment_intent_for_single_order,
    empty_the_cart_by_specific_item,
    get_specific_item_by_session,
    update_item_in_order,
    create_new_order_item,
    get_return_dict_for_basket_adding,
    get_products_in_basket_by_session,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


class SuccessView(TemplateView):
    template_name = "success.html"


class CancelView(TemplateView):
    template_name = "cancel.html"


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        items = get_all_items()
        context = super(HomePageView, self).get_context_data(**kwargs)
        context.update(
            {
                "items": items,
            }
        )
        return context


class ProductLandingPageView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        item_id = self.kwargs["item_id"]
        item = get_item_by_id(item_id=item_id)
        context = super(ProductLandingPageView, self).get_context_data(**kwargs)
        context.update(
            {
                "item": item,
                "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
            }
        )
        return context


class ProductPageView(TemplateView):
    template_name = "product.html"

    def get_context_data(self, **kwargs):
        item_id = self.kwargs["item_id"]
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.cycle_key()
        item = get_item_by_id(item_id=item_id)
        context = super(ProductPageView, self).get_context_data(**kwargs)
        context.update(
            {
                "session_key": session_key,
                "item": item,
            }
        )
        return context


class ShoppingCartPayment(TemplateView):
    template_name = "cart_payment.html"

    def get_context_data(self, **kwargs):
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.cycle_key()
        context = super(ShoppingCartPayment, self).get_context_data(**kwargs)
        products_in_basket, final_price = get_products_in_basket_and_price_by_session(
            session_key=session_key
        )
        context.update(
            {
                "session_key": session_key,
                "products_in_basket": products_in_basket,
                "final_price": final_price,
                "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
            }
        )
        return context


@csrf_exempt
def strype_webhook(request):
    payload = request.body
    event = None

    try:
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except KeyError as e:
        return HttpResponse(status=400)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        items = intent["metadata"]["items"]
        session_key = intent["metadata"]["session_key"]
        customer_email = intent["receipt_email"]

        if session_key:
            empty_the_cart(session_key=session_key)

        send_mail(
            subject="Here is your product",
            message="Thanks for your purchase. Your products:\n" + items,
            recipient_list=[customer_email],
            from_email="mrsheepeeper@gmail.com",
        )

    return HttpResponse(status=200)


class MultipleStripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:
            customer = create_customer()
            session_key = self.kwargs["session_key"]
            (
                products_in_basket,
                final_price,
            ) = get_products_in_basket_and_price_by_session(session_key=session_key)
            intent = create_payment_intent_for_multiple_order(
                session_key=session_key,
                customer=customer,
                final_price=final_price,
                products_in_basket=products_in_basket,
            )

            return JsonResponse({"clientSecret": intent["client_secret"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}), 403


class StripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:
            customer = create_customer()
            item_id = self.kwargs["item_id"]
            item = get_item_by_id(item_id=item_id)
            intent = create_payment_intent_for_single_order(
                customer=customer, final_price=item.price, product_name=item.name
            )
            return JsonResponse({"clientSecret": intent["client_secret"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}), 403


def basket_adding(request):
    session_key = request.session.session_key

    data = request.POST
    item_id = data.get("item_id")
    nmb = int(data.get("nmb"))
    total_price = int(data.get("price")) * nmb
    is_delete = data.get("is_delete")

    if is_delete:
        empty_the_cart_by_specific_item(session_key=session_key, item_id=item_id)

    else:
        new_order_item = get_specific_item_by_session(
            session_key=session_key, item_id=item_id
        )

        if len(new_order_item) > 0:
            update_item_in_order(
                new_order_item=new_order_item, nmb=nmb, total_price=total_price
            )
        else:
            create_new_order_item(
                session_key=session_key,
                item_id=item_id,
                nmb=nmb,
                total_price=total_price,
            )

    return_dict = get_return_dict_for_basket_adding(
        products_in_basket=get_products_in_basket_by_session(session_key=session_key)
    )

    return JsonResponse(return_dict)
