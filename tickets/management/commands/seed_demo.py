from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from tickets.models import Category, SLAPolicy, Ticket, TicketComment
from knowledgebase.models import Article


class Command(BaseCommand):
    help = 'Seed the database with demo data for HelpDeskX.'

    def handle(self, *args, **options):
        # SLA Policies
        sla_defaults = [
            (SLAPolicy.Priority.CRITICAL, 30, 120),
            (SLAPolicy.Priority.HIGH, 120, 480),
            (SLAPolicy.Priority.MEDIUM, 480, 1440),
            (SLAPolicy.Priority.LOW, 1440, 4320),
        ]
        for priority, resp, res in sla_defaults:
            SLAPolicy.objects.update_or_create(
                priority=priority, defaults={'response_time_minutes': resp, 'resolution_time_minutes': res}
            )

        # Categories
        cat_names = ['Network & Wi-Fi', 'Hardware', 'Software', 'Account & Access', 'Email', 'VPN']
        categories = {}
        for name in cat_names:
            categories[name], _ = Category.objects.get_or_create(name=name)

        # Users
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@helpdeskx.local', 'admin12345', role=User.Role.ADMIN, first_name='Ava', last_name='Admin')
        agent1, _ = User.objects.get_or_create(username='agent.rios', defaults={
            'email': 'rios@helpdeskx.local', 'first_name': 'Marco', 'last_name': 'Rios',
            'role': User.Role.AGENT, 'department': 'IT Support',
        })
        agent1.set_password('agent12345')
        agent1.save()
        agent2, _ = User.objects.get_or_create(username='agent.chen', defaults={
            'email': 'chen@helpdeskx.local', 'first_name': 'Lena', 'last_name': 'Chen',
            'role': User.Role.AGENT, 'department': 'IT Support',
        })
        agent2.set_password('agent12345')
        agent2.save()
        emp1, _ = User.objects.get_or_create(username='j.doe', defaults={
            'email': 'jdoe@helpdeskx.local', 'first_name': 'Jamie', 'last_name': 'Doe',
            'role': User.Role.EMPLOYEE, 'department': 'Sales',
        })
        emp1.set_password('employee12345')
        emp1.save()
        emp2, _ = User.objects.get_or_create(username='s.patel', defaults={
            'email': 'spatel@helpdeskx.local', 'first_name': 'Sana', 'last_name': 'Patel',
            'role': User.Role.EMPLOYEE, 'department': 'Finance',
        })
        emp2.set_password('employee12345')
        emp2.save()

        # Tickets
        sample_tickets = [
            ('Wi-Fi keeps disconnecting in East wing', 'My laptop drops the office Wi-Fi every 10-15 minutes today.', categories['Network & Wi-Fi'], Ticket.Priority.HIGH, Ticket.Status.IN_PROGRESS, emp1, agent1),
            ('Cannot reset my password', 'The self-service password reset link is not sending an email.', categories['Account & Access'], Ticket.Priority.MEDIUM, Ticket.Status.RESOLVED, emp2, agent2),
            ('Laptop screen flickering', 'Screen flickers when running on battery power.', categories['Hardware'], Ticket.Priority.LOW, Ticket.Status.NEW, emp1, None),
            ('VPN connection error 619', 'Getting error 619 when connecting to the corporate VPN from home.', categories['VPN'], Ticket.Priority.CRITICAL, Ticket.Status.ASSIGNED, emp2, agent1),
            ('Outlook not syncing new emails', 'Outlook stopped receiving new emails since this morning.', categories['Email'], Ticket.Priority.HIGH, Ticket.Status.CLOSED, emp1, agent2),
        ]
        for subject, desc, cat, pri, status, creator, assignee in sample_tickets:
            if Ticket.objects.filter(subject=subject).exists():
                continue
            t = Ticket.objects.create(
                subject=subject, description=desc, category=cat, priority=pri,
                status=status, created_by=creator, assigned_to=assignee,
            )
            if status in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED):
                t.resolved_at = t.created_at + timedelta(hours=3)
                t.first_response_at = t.created_at + timedelta(minutes=20)
                if status == Ticket.Status.CLOSED:
                    t.closed_at = t.created_at + timedelta(hours=5)
                t.save()
            if assignee:
                TicketComment.objects.create(ticket=t, author=assignee, body='Looking into this now, will update shortly.')

        # Knowledge base
        articles = [
            ('Wi-Fi not connecting', 'wifi-not-connecting', categories['Network & Wi-Fi'],
             'Quick fixes for dropped or unavailable office Wi-Fi.',
             '1. Toggle Wi-Fi off and on.\n2. Forget the network and reconnect.\n3. Restart your laptop.\n4. If issue persists, connect to the guest network and contact IT.'),
            ('How to reset your password', 'password-reset', categories['Account & Access'],
             'Step-by-step self-service password reset instructions.',
             '1. Go to the company login portal.\n2. Click "Forgot password".\n3. Check your recovery email for the reset link (valid for 15 minutes).\n4. Choose a new password meeting the complexity policy.'),
            ('Fixing VPN connection errors', 'vpn-connection-error', categories['VPN'],
             'Common VPN error codes and how to resolve them.',
             'Error 619: usually caused by a firewall blocking the VPN port — disable third-party firewalls and retry.\nError 809: often a network configuration issue — switch from Wi-Fi to a wired connection.\nStill stuck? Open a ticket with the exact error code.'),
        ]
        for title, slug, cat, summary, body in articles:
            Article.objects.get_or_create(slug=slug, defaults={
                'title': title, 'category': cat, 'summary': summary, 'body': body, 'author': agent1,
            })

        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))
        self.stdout.write('Login as: admin/admin12345, agent.rios/agent12345, j.doe/employee12345')
