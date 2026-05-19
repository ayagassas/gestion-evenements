from django.conf import settings
from django.db import models
from django.urls import reverse


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:detail', args=[self.pk])

    @property
    def participants_count(self):
        return self.registrations.filter(status=Registration.STATUS_CONFIRMED).count()


class Registration(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_CONFIRMED, 'Confirmé'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"


class Ticket(models.Model):
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name='ticket',
    )
    qr_code = models.ImageField(upload_to='tickets/qr/', null=True, blank=True)
    pdf_path = models.FileField(upload_to='tickets/pdf/', null=True, blank=True)
    code = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.code}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:40]}"
