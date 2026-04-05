from django.db import models
from django.core.validators import MinValueValidator
from common.models import Base
from decimal import Decimal


class Product(Base):
  name = models.CharField(null=False, blank=False, max_length=255)  
  description = models.TextField(null=False, blank=False)
  price = models.DecimalField(
    max_digits=10, 
    decimal_places=2,
    validators=[MinValueValidator(Decimal("0.01"))])
  
  image = models.ImageField(upload_to="products/", blank=True)
  category = models.CharField(null=False, blank=False, max_length=255)

  def __str__(self):
    return f"{self.name}"


class Cart(Base):
  session_id = models.CharField(
    null=False, 
    blank=False, 
    max_length=255, 
    unique=True, 
    db_index=True)

  def __str__(self):
    return f"Cart {self.id} with session {self.session_id}"


class CartItem(Base):
  product = models.ForeignKey(
    Product, 
    on_delete=models.CASCADE, 
    related_name='cart_items')
  quantity = models.PositiveIntegerField()
  cart = models.ForeignKey(
    Cart, 
    on_delete=models.CASCADE, 
    related_name='items'
  )

  class Meta:
    unique_together = ('cart', 'product')

  def __str__(self):
    return f"{self.product.name} x {self.quantity}"


