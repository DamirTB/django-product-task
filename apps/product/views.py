from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers
from .models import Product, Cart, CartItem
from .serializers import ProductSerializer, CartItemDetailSerializer, CartDetailSerializer
from .filters import ProductFilter


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


_error_serializer = inline_serializer(
    name="ErrorResponse",
    fields={"error": drf_serializers.CharField()},
)


@extend_schema(tags=["Cart"])
class CartView(APIView):
    def _get_or_create_cart(self, request):
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
        return cart

    @extend_schema(
        summary="Get cart",
        description="Returns all items in the current session's cart along with the total price.",
        responses={200: CartDetailSerializer},
    )
    def get(self, request):
        cart = self._get_or_create_cart(request)
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
            400: _error_serializer,
            404: _error_serializer,
        },
    )
    def post(self, request):
        cart = self._get_or_create_cart(request)

        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(request.data.get("quantity", 1))
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemDetailSerializer(cart_item)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=response_status)


@extend_schema(tags=["Cart"])
class CartItemView(APIView):
    def _get_cart_item(self, request, item_id):
        if not request.session.session_key:
            return None
        try:
            return CartItem.objects.select_related("product").get(
                pk=item_id,
                cart__session_id=request.session.session_key,
            )
        except CartItem.DoesNotExist:
            return None

    @extend_schema(
        summary="Update cart item quantity",
        request=inline_serializer(
            name="UpdateCartItemRequest",
            fields={"quantity": drf_serializers.IntegerField()},
        ),
        responses={
            200: CartItemDetailSerializer,
            400: _error_serializer,
            404: _error_serializer,
        },
    )
    def put(self, request, item_id):
        cart_item = self._get_cart_item(request, item_id)
        if cart_item is None:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            quantity = int(request.data.get("quantity"))
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemDetailSerializer(cart_item).data)

    @extend_schema(
        summary="Remove item from cart",
        responses={
            204: None,
            404: _error_serializer,
        },
    )
    def delete(self, request, item_id):
        cart_item = self._get_cart_item(request, item_id)
        if cart_item is None:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
