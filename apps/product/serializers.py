from decimal import Decimal
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, inline_serializer
from .models import Product, Cart, CartItem

error_response_schema = inline_serializer(
    name="ErrorResponse",
    fields={"error": serializers.CharField()},
)


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

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_subtotal(self, obj) -> Decimal:
        return obj.product.price * obj.quantity


class CartDetailSerializer(serializers.ModelSerializer):
    items = CartItemDetailSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "session_id", "items", "total_price"]

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total_price(self, obj) -> Decimal:
        return sum(item.product.price * item.quantity for item in obj.items.all())
