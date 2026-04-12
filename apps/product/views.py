from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from .models import Product
from .filters import ProductFilter
from .serializers import (
    CartDetailSerializer,
    CartItemDetailSerializer,
    ProductSerializer,
    error_response_schema,
)
from .services import (
    CartServiceError,
    add_to_cart,
    delete_cart_item,
    get_cart_item,
    get_or_create_cart,
    update_cart_item_quantity,
)


@extend_schema(tags=["Products"])
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name"]
    ordering = ["name"]


@extend_schema(tags=["Products"])
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


@extend_schema(tags=["Cart"])
class CartView(APIView):
    @extend_schema(
        summary="Get cart",
        description="Returns all items in the current session's cart along with the total price.",
        responses={200: CartDetailSerializer},
    )
    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartDetailSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Add product to cart",
        description="Adds a product to the cart. If the product already exists, its quantity is increased.",
        request=inline_serializer(
            name="AddToCartRequest",
            fields={
                "product_id": drf_serializers.IntegerField(),
                "quantity": drf_serializers.IntegerField(default=1),
            },
        ),
        responses={
            201: CartItemDetailSerializer,
            200: CartItemDetailSerializer,
            400: error_response_schema,
            404: error_response_schema,
        },
    )
    def post(self, request):
        cart = get_or_create_cart(request)
        try:
            cart_item, created = add_to_cart(cart, request.data)
        except CartServiceError as exc:
            return Response({"error": exc.detail}, status=exc.status_code)

        serializer = CartItemDetailSerializer(cart_item)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=response_status)


@extend_schema(tags=["Cart"])
class CartItemView(APIView):
    @extend_schema(
        summary="Update cart item quantity",
        request=inline_serializer(
            name="UpdateCartItemRequest",
            fields={"quantity": drf_serializers.IntegerField()},
        ),
        responses={
            200: CartItemDetailSerializer,
            400: error_response_schema,
            404: error_response_schema,
        },
    )
    def put(self, request, item_id):
        cart_item = get_cart_item(request.session.session_key, item_id)
        if cart_item is None:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            update_cart_item_quantity(cart_item, request.data)
        except CartServiceError as exc:
            return Response({"error": exc.detail}, status=exc.status_code)

        return Response(CartItemDetailSerializer(cart_item).data)

    @extend_schema(
        summary="Remove item from cart",
        responses={
            204: None,
            404: error_response_schema,
        },
    )
    def delete(self, request, item_id):
        cart_item = get_cart_item(request.session.session_key, item_id)
        if cart_item is None:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        delete_cart_item(cart_item)
        return Response(status=status.HTTP_204_NO_CONTENT)
