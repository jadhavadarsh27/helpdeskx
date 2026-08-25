from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SLAPolicy(models.Model):
    """Defines the response/resolution time window for each priority level."""

    class Priority(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    priority = models.CharField(max_length=20, choices=Priority.choices, unique=True)
    response_time_minutes = models.PositiveIntegerField(help_text='Minutes allowed for first response.')
    resolution_time_minutes = models.PositiveIntegerField(help_text='Minutes allowed to fully resolve.')

    class Meta:
        verbose_name = 'SLA Policy'
        verbose_name_plural = 'SLA Policies'

    def __str__(self):
        return f"{self.get_priority_display()} — respond in {self.response_time_minutes}m / resolve in {self.resolution_time_minutes}m"


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
        REOPENED = 'REOPENED', 'Reopened'

    class Priority(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True, help_text='SLA resolution deadline.')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject}"

    def get_absolute_url(self):
        return reverse('tickets:detail', args=[self.pk])

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.ticket_number:
            self.ticket_number = f"HDX-{timezone.now().strftime('%y%m%d')}-{Ticket.objects.count() + 1:04d}"
        super().save(*args, **kwargs)
        if is_new and not self.due_at:
            self.set_sla_due_date()

    def set_sla_due_date(self):
        policy = SLAPolicy.objects.filter(priority=self.priority).first()
        minutes = policy.resolution_time_minutes if policy else {
            'CRITICAL': 30, 'HIGH': 120, 'MEDIUM': 480, 'LOW': 1440,
        }.get(self.priority, 480)
        Ticket.objects.filter(pk=self.pk).update(due_at=self.created_at + timedelta(minutes=minutes))

    @property
    def is_overdue(self):
        if self.status in (self.Status.RESOLVED, self.Status.CLOSED):
            return False
        return bool(self.due_at) and timezone.now() > self.due_at

    @property
    def is_open(self):
        return self.status not in (self.Status.CLOSED,)


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='ticket_attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name.split('/')[-1]


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_internal_note = models.BooleanField(
        default=False, help_text='Visible to agents/admins only, hidden from the employee.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"


class TicketHistory(models.Model):
    """Audit trail of every change made to a ticket."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Ticket histories'

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.action}"


class TicketFeedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(help_text='1 (poor) to 5 (excellent)')
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.ticket.ticket_number}: {self.rating}/5"
