from django.contrib import admin
from .models import Cart, CartItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "price", "is_active", "is_deleted"]
    list_filter = ["category", "is_active", "is_deleted"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    list_editable = ["is_active"]
    list_per_page = 25


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["product", "quantity"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "session_id", "item_count", "is_active", "created"]
    search_fields = ["session_id"]
    list_filter = ["is_active", "is_deleted"]
    readonly_fields = ["session_id", "created", "updated"]
    inlines = [CartItemInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "product", "quantity"]
    search_fields = ["product__name", "cart__session_id"]
    list_filter = ["product__category"]
    list_select_related = ["cart", "product"]

