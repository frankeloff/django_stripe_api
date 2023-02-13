from django.contrib import admin
from django.urls import path
from stripe_api.views import (
    ProductLandingPageView,
    SuccessView,
    CancelView,
    strype_webhook,
    StripeIntentView,
    MultipleStripeIntentView,
    HomePageView,
    ProductPageView,
    ShoppingCartPayment,
    basket_adding,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "create-payment-intent/<int:item_id>/",
        StripeIntentView.as_view(),
        name="create-payment-intent",
    ),
    path(
        "create-multiple-payment-intent/<str:session_key>/",
        MultipleStripeIntentView.as_view(),
        name="create-multiple-payment-intent",
    ),
    path("basket-adding/", basket_adding, name="basket-adding"),
    path(
        "product-page-view/<int:item_id>",
        ProductPageView.as_view(),
        name="product-page-view",
    ),
    path("cart-payment/", ShoppingCartPayment.as_view(), name="cart-payment"),
    path("webhooks/stripe/", strype_webhook, name="stripe-webhook"),
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", CancelView.as_view(), name="cancel"),
    path("home/<int:item_id>", ProductLandingPageView.as_view(), name="landing-page"),
    path("", HomePageView.as_view(), name="home-page"),
]
