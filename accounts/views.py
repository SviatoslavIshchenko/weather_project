from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import UserRegisterForm


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Реєстрація успішна! Тепер увійдіть у свій акаунт."
            )

            return redirect("login")

    else:
        form = UserRegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )
