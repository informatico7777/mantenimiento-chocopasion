from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from apps.core.audit import registrar_auditoria

from .forms import LoginForm


@never_cache
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["usuario_login"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            registrar_auditoria(
                request, "usuarios", user.pk, "LOGIN",
                f"Inicio de sesión de {user.usuario_login}",
            )
            messages.success(request, f"Bienvenido, {user.nombres}.")
            next_url = request.GET.get("next") or "core:dashboard"
            return redirect(next_url)
        messages.error(request, "Usuario o contraseña incorrectos, o cuenta inactiva.")

    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        registrar_auditoria(
            request, "usuarios", request.user.pk, "LOGOUT",
            f"Cierre de sesión de {request.user.usuario_login}",
        )
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("accounts:login")
