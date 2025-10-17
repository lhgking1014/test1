from __future__ import annotations

from django.contrib import admin

from .models import SavedPaymentMethod, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname", "phone", "city", "marketing_opt_in", "updated_at")
    search_fields = ("user__email", "nickname", "phone")


@admin.register(SavedPaymentMethod)
class SavedPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "last4", "provider_id", "is_default", "updated_at")
    list_filter = ("method", "is_default")
    search_fields = ("user__email", "provider_id")

