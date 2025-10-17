from __future__ import annotations

from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "transaction_id", "status", "created_at")
    list_filter = ("method", "status")
    search_fields = ("order__number", "transaction_id")

