from common.models import Base
from django.db import models

class Product(Base):
  name = models.CharField(null=False, blank=False, max_length=255)  
  description = models.TextField(null=False, blank=False)
  price = models.DecimalField(max_digits=10, decimal_places=2)
  image = models.ImageField()
  category = models.CharField(null=False, blank=False, max_length=255)


class Cart(Base):
  session_id = models.CharField(null=False, blank=False, max_length=255)


class CartItem(Base):
  product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
  quantity = models.IntegerField()
  cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
