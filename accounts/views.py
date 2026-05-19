from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from events.models import Registration
from .forms import LoginForm, RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('events:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès. Bienvenue !")
            return redirect('events:home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class AppLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    next_page = reverse_lazy('events:home')


@login_required
def profile_view(request):
    registrations = (
        Registration.objects
        .filter(user=request.user)
        .select_related('event')
        .order_by('-created_at')
    )
    return render(request, 'accounts/profile.html', {'registrations': registrations})
