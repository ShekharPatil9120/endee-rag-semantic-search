from django.core.mail import send_mail
from django.conf import settings

def send_action_notification(user, subject, message):
	try:
		recipient = None
		if hasattr(user, 'email') and user.email:
			recipient = user.email
		if not recipient:
			return False
		send_mail(
			subject,
			message,
			settings.EMAIL_HOST_USER,
			[recipient],
			fail_silently=True,
		)
		return True
	except Exception:
		return False
