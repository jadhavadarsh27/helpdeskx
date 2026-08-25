from .models import Notification


def notify(recipient, message, link=''):
    """Create an in-app notification for a user. Called from ticket lifecycle events."""
    if recipient is None:
        return None
    return Notification.objects.create(recipient=recipient, message=message, link=link)


def notify_many(recipients, message, link=''):
    for recipient in recipients:
        notify(recipient, message, link)
