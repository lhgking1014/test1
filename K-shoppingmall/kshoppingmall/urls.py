from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


from catalog.views import HomePageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/catalog/", include("catalog.api_urls")),
    path("api/orders/", include("orders.api_urls")),
    path("api/payments/", include("payments.api_urls")),
    path("api/core/", include("core.api_urls")),
    path("", HomePageView.as_view(), name="home"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

