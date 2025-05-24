from .models import Notification

def create_notification(user, type_, message, data=None):
    Notification.objects.create(
        user=user,
        type=type_,
        message=message,
        data=data or {}
    )
