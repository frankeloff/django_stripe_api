import stripe
from django.core.mail import send_mail
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.db.models import Sum
from .models import Item, Order
import os

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


class SuccessView(TemplateView):
    template_name = "success.html"


class CancelView(TemplateView):
    template_name = "cancel.html"


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        items = Item.objects.all()
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
        item = Item.objects.get(id=item_id)
        context = super(ProductLandingPageView, self).get_context_data(**kwargs)
        context.update(
            {
                "item": item,
                "STRIPE_PUBLIC_KEY": os.environ.get("STRIPE_PUBLIC_KEY"),
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
        item = Item.objects.get(id=item_id)
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
        products_in_basket = Order.objects.filter(session_key=session_key)
        final_price = Order.objects.filter(session_key=session_key).aggregate(
            Sum("price")
        )["price__sum"]
        context.update(
            {
                "session_key": session_key,
                "products_in_basket": products_in_basket,
                "final_price": final_price,
                "STRIPE_PUBLIC_KEY": os.environ.get("STRIPE_PUBLIC_KEY"),
            }
        )
        return context


@csrf_exempt
def strype_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get("STRIPE_WEBHOOK_SECRET")
        )
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
            products = Order.objects.filter(session_key=session_key)
            for product in products:
                product.delete()

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
            customer = stripe.Customer.create()
            session_key = self.kwargs["session_key"]
            products = Order.objects.filter(session_key=session_key)
            final_price = Order.objects.filter(session_key=session_key).aggregate(
                Sum("price")
            )["price__sum"]
            intent = stripe.PaymentIntent.create(
                amount=int(final_price),
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
                            for product in products
                        ]
                    )
                    + f"\nFinal price: {final_price}$",
                    "session_key": session_key,
                },
            )

            return JsonResponse({"clientSecret": intent["client_secret"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}), 403


class StripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:
            customer = stripe.Customer.create()
            item_id = self.kwargs["item_id"]
            item = Item.objects.get(id=item_id)
            intent = stripe.PaymentIntent.create(
                amount=item.price,
                currency="usd",
                automatic_payment_methods={
                    "enabled": True,
                },
                customer=customer["id"],
                setup_future_usage="off_session",
                metadata={
                    "items": f"{item.name} 1 piece for {item.price}$",
                    "session_key": False,
                },
            )
            return JsonResponse({"clientSecret": intent["client_secret"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}), 403


def basket_adding(request):
    return_dict = {}

    session_key = request.session.session_key

    data = request.POST
    item_id = data.get("item_id")
    nmb = int(data.get("nmb"))
    total_price = float(data.get("price")) * nmb
    is_delete = data.get("is_delete")

    if is_delete:
        objects = Order.objects.filter(session_key=session_key, item=item_id)
        for object in objects:
            object.delete()

    else:
        new_order_item = Order.objects.filter(session_key=session_key, item=item_id)

        if len(new_order_item) > 0:
            new_order_item = new_order_item[0]
            new_order_item.nmb += int(nmb)
            new_order_item.price += float(total_price)
            new_order_item.save(force_update=True)
        else:
            new_order_item = Order.objects.create(
                session_key=session_key, item_id=item_id, nmb=nmb, price=total_price
            )

    products_in_basket = Order.objects.filter(session_key=session_key)
    return_dict["items"] = []

    if len(products_in_basket) > 0:
        for product in products_in_basket:
            product_dict = {}
            product_dict["id"] = product.id
            product_dict["name"] = product.item.name
            product_dict["price"] = product.price
            product_dict["nmb"] = product.nmb
            return_dict["items"].append(product_dict)

    return JsonResponse(return_dict)
