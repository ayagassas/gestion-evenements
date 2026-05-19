from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=[(User.ROLE_USER, 'Participant'), (User.ROLE_ORGANIZER, 'Organisateur')],
        widget=forms.RadioSelect,
        initial=User.ROLE_USER,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    pass
