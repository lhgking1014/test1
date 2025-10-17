from __future__ import annotations

from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, views, viewsets
from rest_framework.response import Response

from catalog.models import Product
from payments.gateway import PaymentGateway
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartItemSerializer, CartSerializer, OrderSerializer
from .utils import generate_order_number


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def _get_cart(self, request) -> Cart:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
            if cart.session_key != session_key:
                cart.session_key = session_key
                cart.save(update_fields=["session_key"])
            return cart
        cart, _ = Cart.objects.get_or_create(session_key=session_key, is_active=True)
        return cart

    def list(self, request):
        cart = self._get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def create(self, request):
        cart = self._get_cart(request)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product: Product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = item.quantity + quantity if not created else quantity
        item.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        cart = self._get_cart(request)
        item = get_object_or_404(cart.items, pk=pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = (
            Cart.objects.filter(user=request.user, is_active=True)
            .prefetch_related("items__product")
            .first()
        )
        if not cart or not cart.items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data
        payment_method = (payload.get("payment_method") or "").lower()
        if not payment_method:
            return Response({"detail": "Select a payment method."}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ["shipping_phone", "shipping_address1", "shipping_postal_code", "shipping_city"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            return Response(
                {"detail": f"Missing shipping details: {', '.join(missing)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    number=generate_order_number(),
                    total_amount=int(cart.total_amount),
                    shipping_name=payload.get("shipping_name", request.user.get_full_name()),
                    shipping_phone=payload.get("shipping_phone"),
                    shipping_address1=payload.get("shipping_address1"),
                    shipping_address2=payload.get("shipping_address2", ""),
                    shipping_postal_code=payload.get("shipping_postal_code"),
                    shipping_city=payload.get("shipping_city"),
                    shipping_request=payload.get("shipping_request", ""),
                )

                for item in cart.items.select_related("product"):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                    item.product.inventory = max(item.product.inventory - item.quantity, 0)
                    item.product.save(update_fields=["inventory", "updated_at"])

                gateway = PaymentGateway()
                payment_result = gateway.process(
                    order=order,
                    method=payment_method,
                    payload=payload.get("payment_payload", {}),
                )
                if not payment_result.get("success"):
                    raise ValueError(payment_result.get("message", "Payment failed."))

                order.status = Order.Status.PAID
                order.save(update_fields=["status", "updated_at"])
                cart.is_active = False
                cart.save(update_fields=["is_active", "updated_at"])

        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        send_mail(
            subject="Your order has been received",
            message=f"{request.user.get_full_name() or request.user.email}, order number {order.number} has been received.",
            from_email=None,
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

