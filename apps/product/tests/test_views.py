from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.product.models import Product


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
        response = self.client.get(self.url, {"limit": 2})
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
