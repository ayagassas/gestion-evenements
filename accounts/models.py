from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_USER = 'user'
    ROLE_ORGANIZER = 'organizer'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ORGANIZER, 'Organizer'),
        (ROLE_ADMIN, 'Admin'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['email']

    @property
    def is_organizer(self):
        return self.role == self.ROLE_ORGANIZER or self.is_superuser

    @property
    def is_app_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
