from __future__ import annotations

from django.db.models import Q\nfrom django.views.generic import TemplateView
from rest_framework import generics

from .models import Product
from .serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(status=Product.Status.ACTIVE)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"
    queryset = Product.objects.filter(status__in=[Product.Status.ACTIVE, Product.Status.DRAFT])



class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.filter(status=Product.Status.ACTIVE)[:6]
        return context

