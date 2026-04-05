from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.product.models import Product, Cart, CartItem


def make_product(**kwargs) -> Product:
    defaults = {
        "name": "Test Product",
        "description": "Test description",
        "price": Decimal("10.00"),
        "category": "electronics",
        "image": "",
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


class ProductListViewTests(APITestCase):
    url = reverse("product-list")

    def setUp(self):
        self.laptop = make_product(name="Laptop", price=Decimal("999.99"), category="electronics")
        self.phone = make_product(name="Phone", price=Decimal("499.99"), category="electronics")
        self.chair = make_product(name="Office Chair", price=Decimal("199.99"), category="furniture")

    def test_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_all_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 3)

    def test_response_has_expected_fields(self):
        response = self.client.get(self.url)
        product = response.data["results"][0]
        for field in ["id", "name", "description", "price", "category", "image"]:
            self.assertIn(field, product)

    def test_filter_by_category(self):
        response = self.client.get(self.url, {"category": "furniture"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Office Chair")

    def test_filter_by_price_range(self):
        response = self.client.get(self.url, {"min_price": "500", "max_price": "1000"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Laptop")

    def test_search_by_name(self):
        response = self.client.get(self.url, {"search": "Phone"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Phone")

    def test_ordering_by_price_ascending(self):
        response = self.client.get(self.url, {"ordering": "price"})
        prices = [Decimal(r["price"]) for r in response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_ordering_by_price_descending(self):
        response = self.client.get(self.url, {"ordering": "-price"})
        prices = [Decimal(r["price"]) for r in response.data["results"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_pagination_limit(self):
        response = self.client.get(self.url, {"page_size": 2})
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])


class ProductDetailViewTests(APITestCase):

    def setUp(self):
        self.product = make_product(name="Laptop", price=Decimal("999.99"), category="electronics")
        self.url = reverse("product-detail", kwargs={"pk": self.product.pk})

    def test_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_correct_product(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["id"], self.product.pk)
        self.assertEqual(response.data["name"], "Laptop")

    def test_returns_404_for_nonexistent_product(self):
        url = reverse("product-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartViewTests(APITestCase):
    url = reverse("cart")

    def setUp(self):
        self.product = make_product(name="Laptop", price=Decimal("999.99"), category="electronics")
        self.product2 = make_product(name="Phone", price=Decimal("499.99"), category="electronics")

    def test_get_empty_cart_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total_price"], Decimal("0"))

    def test_post_adds_product_to_cart(self):
        response = self.client.post(self.url, {"product_id": self.product.id, "quantity": 2})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product"]["id"], self.product.id)
        self.assertEqual(response.data["quantity"], 2)
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("1999.98"))

    def test_post_existing_product_increases_quantity(self):
        self.client.post(self.url, {"product_id": self.product.id, "quantity": 1})
        response = self.client.post(self.url, {"product_id": self.product.id, "quantity": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 3)

    def test_post_without_product_id_returns_400(self):
        response = self.client.post(self.url, {"quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_post_with_invalid_quantity_returns_400(self):
        response = self.client.post(self.url, {"product_id": self.product.id, "quantity": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_nonexistent_product_returns_404(self):
        response = self.client.post(self.url, {"product_id": 99999, "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_cart_returns_items_and_total(self):
        self.client.post(self.url, {"product_id": self.product.id, "quantity": 1})
        self.client.post(self.url, {"product_id": self.product2.id, "quantity": 2})
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 2)
        expected_total = Decimal("999.99") + Decimal("499.99") * 2
        self.assertEqual(Decimal(response.data["total_price"]), expected_total)


class CartItemViewTests(APITestCase):

    def setUp(self):
        self.product = make_product(name="Laptop", price=Decimal("999.99"), category="electronics")
        self.cart_url = reverse("cart")
        add_response = self.client.post(self.cart_url, {"product_id": self.product.id, "quantity": 1})
        self.item_id = add_response.data["id"]
        self.item_url = reverse("cart-item", kwargs={"item_id": self.item_id})

    def test_put_updates_quantity(self):
        response = self.client.put(self.item_url, {"quantity": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 5)

    def test_put_with_invalid_quantity_returns_400(self):
        response = self.client.put(self.item_url, {"quantity": -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_nonexistent_item_returns_404(self):
        url = reverse("cart-item", kwargs={"item_id": 99999})
        response = self.client.put(url, {"quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_item(self):
        response = self.client.delete(self.item_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        get_response = self.client.get(self.cart_url)
        self.assertEqual(get_response.data["items"], [])

    def test_delete_nonexistent_item_returns_404(self):
        url = reverse("cart-item", kwargs={"item_id": 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_access_another_sessions_cart_item(self):
        other_client = self.client_class()
        other_product = make_product(name="Chair", price=Decimal("99.99"), category="furniture")
        other_client.post(self.cart_url, {"product_id": other_product.id, "quantity": 1})
        response = other_client.put(self.item_url, {"quantity": 10})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
