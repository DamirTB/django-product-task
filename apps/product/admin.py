from django.contrib import admin
from .models import Cart, Product, CartItem

admin.site.register([Cart, Product, CartItem])

