from __future__ import annotations

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_field, user_username


class AccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to enforce email-only authentication."""

    def clean_username(self, username, shallow=False):
        return super().clean_username(username or "")

    def save_user(self, request, user, form, commit=True):
        user_email(user, form.cleaned_data.get("email"))
        user_field(user, "first_name", form.cleaned_data.get("first_name"))
        user_field(user, "last_name", form.cleaned_data.get("last_name"))
        user_username(user, "")
        if commit:
            user.save()
        return user

