from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm, UsernameAuthenticationForm


class UsernameLoginView(LoginView):
    authentication_form = UsernameAuthenticationForm
    template_name = "login.html"


@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                username = form.cleaned_data["username"]
                if get_user_model().objects.filter(username=username).exists():
                    form.add_error(
                        "username",
                        "Este nombre de usuario ya está registrado.",
                    )
                else:
                    raise
            else:
                messages.success(
                    request,
                    "Tu cuenta fue creada. Ya puedes iniciar sesión.",
                )
                return redirect("login")
    else:
        form = RegistrationForm()

    return render(request, "login.html", {"form": form})
