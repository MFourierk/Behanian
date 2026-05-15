from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .forms import LoginForm


@never_cache
@csrf_protect
def login_view(request):
    # Si déjà connecté, rediriger directement
    if request.user.is_authenticated:
        return redirect('dashboard:index')

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
                return redirect('dashboard:index')
        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@never_cache
def logout_view(request):
    logout(request)
    return redirect('login')
