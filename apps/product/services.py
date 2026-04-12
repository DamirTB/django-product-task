from rest_framework import status

from .models import Cart, CartItem, Product


class CartServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_or_create_cart(request):
    session_id = _ensure_session_key(request)
    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def add_to_cart(cart, data):
    product_id = data.get("product_id")
    if not product_id:
        raise CartServiceError("product_id is required")

    try:
        quantity = int(data.get("quantity", 1))
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise CartServiceError("quantity must be a positive integer")

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise CartServiceError("Product not found", status.HTTP_404_NOT_FOUND)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return cart_item, created


def get_cart_item(session_key, item_id):
    if not session_key:
        return None
    try:
        return CartItem.objects.select_related("product").get(
            pk=item_id,
            cart__session_id=session_key,
        )
    except CartItem.DoesNotExist:
        return None


def update_cart_item_quantity(cart_item, data):
    try:
        quantity = int(data.get("quantity"))
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise CartServiceError("quantity must be a positive integer")

    cart_item.quantity = quantity
    cart_item.save()
    return cart_item


def delete_cart_item(cart_item):
    cart_item.delete()
