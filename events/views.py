from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EventForm, EventSearchForm
from .models import Event, Notification, Registration, Ticket
from .utils import generate_ticket_for, notify, send_confirmation_email


def _organizer_required(user):
    return user.is_authenticated and (user.is_organizer or user.is_app_admin)


def _admin_required(user):
    return user.is_authenticated and user.is_app_admin


def home(request):
    form = EventSearchForm(request.GET or None)
    qs = Event.objects.all()
    if form.is_valid():
        q = form.cleaned_data.get('q')
        loc = form.cleaned_data.get('location')
        date_from = form.cleaned_data.get('date_from')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if loc:
            qs = qs.filter(location__icontains=loc)
        if date_from:
            qs = qs.filter(date__date__gte=date_from)
    qs = qs.annotate(reg_count=Count('registrations'))
    return render(request, 'events/home.html', {'events': qs, 'form': form})


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    user_registration = None
    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(user=request.user, event=event).first()
    return render(request, 'events/detail.html', {
        'event': event,
        'user_registration': user_registration,
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id == request.user.id:
        messages.error(request, "Vous ne pouvez pas vous inscrire à votre propre événement.")
        return redirect('events:detail', pk=event.pk)

    registration, created = Registration.objects.get_or_create(
        user=request.user,
        event=event,
        defaults={'status': Registration.STATUS_CONFIRMED},
    )
    if not created:
        messages.info(request, "Vous êtes déjà inscrit à cet événement.")
        return redirect('events:detail', pk=event.pk)

    ticket = generate_ticket_for(registration)
    send_confirmation_email(registration, ticket)
    notify(request.user, f"Inscription confirmée à « {event.title} ».",
           url=f"/events/{event.pk}/")
    notify(event.organizer, f"Nouveau participant à « {event.title} » : {request.user.username}.",
           url=f"/events/{event.pk}/participants/")
    messages.success(request, "Inscription confirmée ! Votre ticket est disponible.")
    return redirect('events:detail', pk=event.pk)


@login_required
def unregister_from_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    Registration.objects.filter(user=request.user, event=event).delete()
    messages.success(request, "Désinscription effectuée.")
    return redirect('events:detail', pk=event.pk)


@login_required
def download_ticket(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    if registration.user_id != request.user.id and not request.user.is_app_admin:
        return HttpResponseForbidden()
    ticket = getattr(registration, 'ticket', None)
    if ticket is None or not ticket.pdf_path:
        ticket = generate_ticket_for(registration)
    try:
        f = ticket.pdf_path.open('rb')
    except FileNotFoundError:
        ticket = generate_ticket_for(registration)
        f = ticket.pdf_path.open('rb')
    return FileResponse(f, as_attachment=True, filename=f'ticket_{ticket.code}.pdf')


# ---- Organizer dashboard ---------------------------------------------------

@login_required
@user_passes_test(_organizer_required)
def organizer_dashboard(request):
    events = (
        Event.objects.filter(organizer=request.user)
        .annotate(reg_count=Count('registrations'))
        .order_by('-date')
    )
    total_registrations = sum(e.reg_count for e in events)
    return render(request, 'events/organizer/dashboard.html', {
        'events': events,
        'total_events': events.count(),
        'total_registrations': total_registrations,
    })


@login_required
@user_passes_test(_organizer_required)
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, "Événement créé.")
            return redirect('events:organizer_dashboard')
    else:
        form = EventForm()
    return render(request, 'events/organizer/event_form.html', {'form': form, 'mode': 'create'})


@login_required
@user_passes_test(_organizer_required)
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.id and not request.user.is_app_admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Événement modifié.")
            return redirect('events:organizer_dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/organizer/event_form.html',
                  {'form': form, 'mode': 'update', 'event': event})


@login_required
@user_passes_test(_organizer_required)
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.id and not request.user.is_app_admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Événement supprimé.")
        return redirect('events:organizer_dashboard')
    return render(request, 'events/organizer/event_confirm_delete.html', {'event': event})


@login_required
@user_passes_test(_organizer_required)
def event_participants(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.id and not request.user.is_app_admin:
        return HttpResponseForbidden()
    registrations = event.registrations.select_related('user').order_by('-created_at')
    return render(request, 'events/organizer/participants.html', {
        'event': event,
        'registrations': registrations,
    })


@login_required
@user_passes_test(_organizer_required)
def check_in(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    event = registration.event
    if event.organizer_id != request.user.id and not request.user.is_app_admin:
        return HttpResponseForbidden()
    if not registration.checked_in:
        registration.checked_in = True
        registration.checked_in_at = timezone.now()
        registration.save()
        notify(registration.user, f"Check-in effectué pour « {event.title} ».")
        messages.success(request, f"{registration.user.username} : check-in OK.")
    else:
        messages.info(request, "Déjà checké.")
    return redirect('events:participants', pk=event.pk)


@login_required
@user_passes_test(_organizer_required)
def stats_dashboard(request):
    events = Event.objects.filter(organizer=request.user)
    data = (
        events.annotate(
            confirmed=Count('registrations', filter=Q(registrations__status=Registration.STATUS_CONFIRMED)),
            checked=Count('registrations', filter=Q(registrations__checked_in=True)),
        )
        .order_by('-date')
    )
    totals = {
        'events': events.count(),
        'registrations': Registration.objects.filter(event__organizer=request.user).count(),
        'check_ins': Registration.objects.filter(event__organizer=request.user, checked_in=True).count(),
    }
    return render(request, 'events/organizer/stats.html', {'rows': data, 'totals': totals})


# ---- Admin ----------------------------------------------------------------

@login_required
@user_passes_test(_admin_required)
def admin_users(request):
    from accounts.models import User as AppUser
    users = AppUser.objects.all().order_by('-created_at')
    return render(request, 'events/admin/users.html', {'users': users})


@login_required
@user_passes_test(_admin_required)
def admin_user_set_role(request, user_id):
    from accounts.models import User as AppUser
    user = get_object_or_404(AppUser, pk=user_id)
    role = request.POST.get('role')
    if role in dict(AppUser.ROLE_CHOICES):
        user.role = role
        user.save()
        messages.success(request, f"Rôle de {user.username} mis à jour : {user.get_role_display()}.")
    return redirect('events:admin_users')


@login_required
@user_passes_test(_admin_required)
def admin_user_delete(request, user_id):
    from accounts.models import User as AppUser
    user = get_object_or_404(AppUser, pk=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas vous supprimer vous-même.")
    else:
        user.delete()
        messages.success(request, "Utilisateur supprimé.")
    return redirect('events:admin_users')


@login_required
@user_passes_test(_admin_required)
def admin_events(request):
    events = Event.objects.annotate(reg_count=Count('registrations')).order_by('-date')
    return render(request, 'events/admin/events.html', {'events': events})


@login_required
@user_passes_test(_admin_required)
def admin_event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.success(request, "Événement supprimé.")
    return redirect('events:admin_events')


# ---- Notifications --------------------------------------------------------

@login_required
def notifications_list(request):
    qs = request.user.notifications.all()
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'events/notifications.html', {'notifications': qs})
