from rest_framework import serializers
from .models import Product, Cart, CartItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category", "image"]
        read_only_fields = ["id"]


class CartItemDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "subtotal"]

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity


class CartDetailSerializer(serializers.ModelSerializer):
    items = CartItemDetailSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "session_id", "items", "total_price"]

    def get_total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())
