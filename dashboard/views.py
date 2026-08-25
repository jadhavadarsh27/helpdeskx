from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, ExpressionWrapper, F, DurationField, Q
from django.shortcuts import render
from django.utils import timezone

from tickets.models import Ticket, Category
from accounts.models import User


@login_required
def home(request):
    user = request.user
    tickets = Ticket.objects.all()

    if user.is_employee:
        tickets = tickets.filter(created_by=user)
    elif user.is_agent:
        tickets = tickets.filter(assigned_to=user)
    # Admin sees all tickets.

    now = timezone.now()
    total = tickets.count()
    open_count = tickets.filter(status=Ticket.Status.NEW).count()
    pending_count = tickets.filter(status__in=[Ticket.Status.ASSIGNED, Ticket.Status.IN_PROGRESS, Ticket.Status.REOPENED]).count()
    resolved_count = tickets.filter(status=Ticket.Status.RESOLVED).count()
    closed_count = tickets.filter(status=Ticket.Status.CLOSED).count()
    high_priority_count = tickets.filter(priority__in=[Ticket.Priority.CRITICAL, Ticket.Priority.HIGH]).exclude(
        status__in=[Ticket.Status.CLOSED, Ticket.Status.RESOLVED]
    ).count()
    overdue_count = sum(1 for t in tickets.exclude(status__in=[Ticket.Status.CLOSED, Ticket.Status.RESOLVED]) if t.is_overdue)

    resolved_qs = tickets.filter(resolved_at__isnull=False).annotate(
        resolution_duration=ExpressionWrapper(F('resolved_at') - F('created_at'), output_field=DurationField())
    )
    avg_resolution = resolved_qs.aggregate(avg=Avg('resolution_duration'))['avg']
    avg_resolution_hours = round(avg_resolution.total_seconds() / 3600, 1) if avg_resolution else None

    tickets_by_category = list(
        tickets.values('category__name').annotate(count=Count('id')).order_by('-count')
    )
    tickets_by_status = list(
        tickets.values('status').annotate(count=Count('id')).order_by('-count')
    )

    context = {
        'total': total,
        'open_count': open_count,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'closed_count': closed_count,
        'high_priority_count': high_priority_count,
        'overdue_count': overdue_count,
        'avg_resolution_hours': avg_resolution_hours,
        'tickets_by_category': tickets_by_category,
        'tickets_by_status': tickets_by_status,
        'recent_tickets': tickets.select_related('category', 'assigned_to')[:8],
    }

    if user.is_admin_role:
        agent_performance = (
            Ticket.objects.filter(assigned_to__isnull=False)
            .values('assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name')
            .annotate(
                assigned_count=Count('id'),
                resolved_count=Count('id', filter=Q(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])),
            )
            .order_by('-assigned_count')
        )
        tickets_by_department = list(
            Ticket.objects.values('created_by__department').annotate(count=Count('id')).order_by('-count')
        )
        context.update({
            'agent_performance': agent_performance,
            'tickets_by_department': tickets_by_department,
            'total_agents': User.objects.filter(role=User.Role.AGENT).count(),
            'total_employees': User.objects.filter(role=User.Role.EMPLOYEE).count(),
            'unassigned_count': Ticket.objects.filter(assigned_to__isnull=True).exclude(
                status__in=[Ticket.Status.CLOSED, Ticket.Status.RESOLVED]
            ).count(),
        })

    return render(request, 'dashboard/home.html', context)
