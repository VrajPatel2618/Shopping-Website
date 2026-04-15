from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("earbuds/", views.earbuds, name="earbuds"),
    path("headphones/", views.headphones, name="headphones"),
    path("watches/", views.watches, name="watches"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("search/", views.search, name="search"),
    path("search/suggest/", views.search_suggest, name="search_suggest"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.user_panel, name="user_panel"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("add_to_cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/increase/<int:item_id>/", views.increase_quantity, name="increase_quantity"),
    path("cart/decrease/<int:item_id>/", views.decrease_quantity, name="decrease_quantity"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("pos/", views.pos_view, name="pos"),
    path("invoice/<int:order_id>/", views.generate_invoice, name="invoice_detail"),
]
