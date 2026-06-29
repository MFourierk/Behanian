from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .forms import LoginForm
from utils.permissions import is_kds_only


def _redirection_post_login(user):
    """Retourne l'URL de redirection adaptée au rôle de l'utilisateur."""
    if is_kds_only(user):
        return 'restaurant:kds'
    return 'dashboard:index'


@never_cache
@csrf_protect
def login_view(request):
    # Si déjà connecté, rediriger selon le rôle
    if request.user.is_authenticated:
        return redirect(_redirection_post_login(request.user))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password'),
            )
            if user is not None:
                login(request, user)
                return redirect(_redirection_post_login(user))
        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@never_cache
def logout_view(request):
    logout(request)
    return redirect('login')
