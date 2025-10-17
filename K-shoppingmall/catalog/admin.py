from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Product, ProductMedia, VisionJob


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "inventory", "status", "created_at", "preview")
    list_filter = ("status",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductMediaInline]
    actions = ["create_vision_job"]

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" />', obj.image.url)
        return "-"

    def create_vision_job(self, request, queryset):
        created = 0
        for product in queryset:
            if product.image:
                VisionJob.objects.create(product=product)
                created += 1
        self.message_user(request, f"{created} vision jobs queued.")

    create_vision_job.short_description = "Queue Google Vision analysis"


@admin.register(VisionJob)
class VisionJobAdmin(admin.ModelAdmin):
    list_display = ("product", "status", "created_at", "updated_at")
    list_filter = ("status",)
    readonly_fields = ("response_payload", "error_message")

