from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from notifications.services import notify, notify_many
from .forms import (
    TicketAssignForm, TicketAttachmentForm, TicketCommentForm,
    TicketCreateForm, TicketFeedbackForm,
)
from .models import Ticket, TicketHistory


def _log(ticket, actor, action):
    TicketHistory.objects.create(ticket=ticket, actor=actor, action=action)


def _can_view(user, ticket):
    if user.is_admin_role:
        return True
    if user.is_agent:
        return True
    return ticket.created_by_id == user.id


@login_required
def ticket_list(request):
    user = request.user
    tickets = Ticket.objects.select_related('category', 'assigned_to', 'created_by')

    if user.is_employee:
        tickets = tickets.filter(created_by=user)
    elif user.is_agent:
        scope = request.GET.get('scope', 'mine')
        if scope == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        elif scope == 'all':
            pass
        else:
            tickets = tickets.filter(assigned_to=user)
    # Admins see everything by default.

    status = request.GET.get('status')
    priority = request.GET.get('priority')
    q = request.GET.get('q')
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if q:
        tickets = tickets.filter(subject__icontains=q)

    paginator = Paginator(tickets, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tickets/ticket_list.html', {
        'page_obj': page_obj,
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
        'current_status': status or '',
        'current_priority': priority or '',
        'q': q or '',
        'scope': request.GET.get('scope', 'mine'),
    })


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketCreateForm(request.POST)
        attachment_form = TicketAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            if request.FILES.get('file'):
                if attachment_form.is_valid():
                    attachment = attachment_form.save(commit=False)
                    attachment.ticket = ticket
                    attachment.uploaded_by = request.user
                    attachment.save()
            _log(ticket, request.user, 'Ticket created')
            agents = User.objects.filter(role=User.Role.AGENT)
            notify_many(agents, f'New ticket {ticket.ticket_number}: {ticket.subject}', ticket.get_absolute_url())
            messages.success(request, f'Ticket {ticket.ticket_number} created successfully.')
            return redirect('tickets:detail', pk=ticket.pk)
    else:
        form = TicketCreateForm()
        attachment_form = TicketAttachmentForm()
    return render(request, 'tickets/ticket_form.html', {'form': form, 'attachment_form': attachment_form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('category', 'assigned_to', 'created_by'), pk=pk)
    if not _can_view(request.user, ticket):
        messages.error(request, "You don't have permission to view that ticket.")
        return redirect('tickets:list')

    comment_form = TicketCommentForm()
    assign_form = TicketAssignForm(instance=ticket) if request.user.is_agent or request.user.is_admin_role else None
    feedback_form = TicketFeedbackForm()

    comments = ticket.comments.select_related('author')
    if request.user.is_employee:
        comments = comments.filter(is_internal_note=False)

    if request.method == 'POST' and 'submit_comment' in request.POST:
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            if request.user.is_employee:
                comment.is_internal_note = False
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            if not ticket.first_response_at and request.user.id != ticket.created_by_id:
                ticket.first_response_at = timezone.now()
                ticket.save(update_fields=['first_response_at'])
            _log(ticket, request.user, 'Comment added')
            notify_target = ticket.created_by if request.user.id != ticket.created_by_id else ticket.assigned_to
            if notify_target:
                notify(notify_target, f'New comment on {ticket.ticket_number}', ticket.get_absolute_url())
            messages.success(request, 'Comment added.')
            return redirect('tickets:detail', pk=ticket.pk)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'assign_form': assign_form,
        'feedback_form': feedback_form,
        'history': ticket.history.select_related('actor')[:20],
    })


@login_required
def ticket_assign(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not (request.user.is_agent or request.user.is_admin_role):
        messages.error(request, 'Only agents or admins can assign/update tickets.')
        return redirect('tickets:detail', pk=pk)

    if request.method == 'POST':
        form = TicketAssignForm(request.POST, instance=ticket)
        if form.is_valid():
            old_status = ticket.status
            old_assignee = ticket.assigned_to_id
            ticket = form.save(commit=False)
            if ticket.assigned_to_id and ticket.status == Ticket.Status.NEW:
                ticket.status = Ticket.Status.ASSIGNED
            if ticket.status == Ticket.Status.RESOLVED and old_status != Ticket.Status.RESOLVED:
                ticket.resolved_at = timezone.now()
            if ticket.status == Ticket.Status.CLOSED and old_status != Ticket.Status.CLOSED:
                ticket.closed_at = timezone.now()
            ticket.save()

            if ticket.assigned_to_id and ticket.assigned_to_id != old_assignee:
                _log(ticket, request.user, f'Assigned to {ticket.assigned_to}')
                notify(ticket.assigned_to, f'Ticket {ticket.ticket_number} assigned to you', ticket.get_absolute_url())
            if ticket.status != old_status:
                _log(ticket, request.user, f'Status changed to {ticket.get_status_display()}')
                notify(ticket.created_by, f'Ticket {ticket.ticket_number} is now {ticket.get_status_display()}', ticket.get_absolute_url())
            messages.success(request, 'Ticket updated.')
    return redirect('tickets:detail', pk=pk)


@login_required
def ticket_resolve_response(request, pk):
    """Employee accepts (closes) or rejects (reopens) a resolved ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    if ticket.created_by_id != request.user.id:
        messages.error(request, 'Only the ticket creator can confirm resolution.')
        return redirect('tickets:detail', pk=pk)

    action = request.POST.get('action')
    if action == 'accept':
        ticket.status = Ticket.Status.CLOSED
        ticket.closed_at = timezone.now()
        ticket.save(update_fields=['status', 'closed_at'])
        _log(ticket, request.user, 'Employee accepted resolution — ticket closed')
        if ticket.assigned_to:
            notify(ticket.assigned_to, f'{ticket.ticket_number} was accepted and closed by the employee', ticket.get_absolute_url())
        messages.success(request, 'Thanks for confirming — the ticket is now closed.')

        feedback_form = TicketFeedbackForm(request.POST)
        if feedback_form.is_valid() and feedback_form.cleaned_data.get('rating'):
            feedback = feedback_form.save(commit=False)
            feedback.ticket = ticket
            feedback.save()
    elif action == 'reject':
        ticket.status = Ticket.Status.REOPENED
        ticket.resolved_at = None
        ticket.save(update_fields=['status', 'resolved_at'])
        _log(ticket, request.user, 'Employee rejected resolution — ticket reopened')
        if ticket.assigned_to:
            notify(ticket.assigned_to, f'{ticket.ticket_number} was reopened by the employee', ticket.get_absolute_url())
        messages.warning(request, 'Ticket reopened. The support team has been notified.')
    return redirect('tickets:detail', pk=pk)
