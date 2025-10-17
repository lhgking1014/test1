from __future__ import annotations

from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "is_active", "total_amount", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "price", "quantity", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total_amount", "created_at", "tracking_number")
    list_filter = ("status",)
    search_fields = ("number", "user__email")
    inlines = [OrderItemInline]
    actions = ["mark_fulfilled"]

    def mark_fulfilled(self, request, queryset):
        count = queryset.update(status=Order.Status.FULFILLED)
        self.message_user(request, f"{count} orders marked as fulfilled.")

    mark_fulfilled.short_description = "Mark selected orders as fulfilled"

