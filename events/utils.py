import io
import uuid

import qrcode
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .models import Notification, Ticket


def _make_qr_image(payload: str):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def _make_pdf(ticket: Ticket, qr_buf: io.BytesIO):
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A5)
    width, height = A5
    reg = ticket.registration
    event = reg.event
    user = reg.user

    # Header
    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(1.5 * cm, height - 1.6 * cm, 'TICKET D\'EVENEMENT')

    # Body
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(1.5 * cm, height - 3.6 * cm, event.title[:50])

    c.setFont('Helvetica', 11)
    y = height - 4.5 * cm
    lines = [
        f"Participant : {user.username}",
        f"Email       : {user.email}",
        f"Date        : {event.date.strftime('%d/%m/%Y %H:%M')}",
        f"Lieu        : {event.location}",
        f"Code ticket : {ticket.code}",
        f"Statut      : {reg.get_status_display()}",
    ]
    for line in lines:
        c.drawString(1.5 * cm, y, line)
        y -= 0.7 * cm

    # QR
    qr_img = ImageReader(qr_buf)
    c.drawImage(qr_img, width - 5.5 * cm, 1.5 * cm, 4 * cm, 4 * cm)

    c.setFont('Helvetica-Oblique', 8)
    c.drawString(1.5 * cm, 1.2 * cm, 'Présentez ce ticket (ou le QR) à l\'entrée.')

    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return pdf_buf


def generate_ticket_for(registration) -> Ticket:
    """Generate (or regenerate) a Ticket for a Registration."""
    ticket, _ = Ticket.objects.get_or_create(
        registration=registration,
        defaults={'code': uuid.uuid4().hex[:16].upper()},
    )
    if not ticket.code:
        ticket.code = uuid.uuid4().hex[:16].upper()

    payload = f"TICKET:{ticket.code}|REG:{registration.id}|EVT:{registration.event_id}"
    qr_buf = _make_qr_image(payload)
    ticket.qr_code.save(f'qr_{ticket.code}.png', ContentFile(qr_buf.getvalue()), save=False)

    qr_buf.seek(0)
    pdf_buf = _make_pdf(ticket, qr_buf)
    ticket.pdf_path.save(f'ticket_{ticket.code}.pdf', ContentFile(pdf_buf.getvalue()), save=False)
    ticket.save()
    return ticket


def send_confirmation_email(registration, ticket: Ticket):
    user = registration.user
    event = registration.event
    if not user.email:
        return
    body = (
        f"Bonjour {user.username},\n\n"
        f"Votre inscription à l'événement « {event.title} » est confirmée.\n"
        f"Date  : {event.date.strftime('%d/%m/%Y %H:%M')}\n"
        f"Lieu  : {event.location}\n"
        f"Code  : {ticket.code}\n\n"
        f"Votre ticket est en pièce jointe.\n\n"
        f"— Event Manager"
    )
    msg = EmailMessage(
        subject=f"Confirmation : {event.title}",
        body=body,
        to=[user.email],
    )
    if ticket.pdf_path:
        try:
            ticket.pdf_path.open('rb')
            msg.attach(f'ticket_{ticket.code}.pdf', ticket.pdf_path.read(), 'application/pdf')
            ticket.pdf_path.close()
        except Exception:
            pass
    msg.send(fail_silently=True)


def notify(user, message: str, url: str = ''):
    Notification.objects.create(user=user, message=message, url=url)
