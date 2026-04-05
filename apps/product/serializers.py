from rest_framework import serializers
from .models import Product, Cart, CartItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category", "image"]
        read_only_fields = ["id"]


class CartSerializer(serializers.ModelSerializer):
  class Meta:
    model = Cart
    fields = "__all__"
    read_only_fields = ["id", "is_deleted", "order"]


class CartItemSerializer(serializers.ModelSerializer):
  class Meta:
    model = CartItem
    fields = "__all__"
    read_only_fields = ["id", "is_deleted", "order"]
