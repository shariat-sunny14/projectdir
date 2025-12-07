import logging
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.contrib.sessions.models import Session

logger = logging.getLogger(__name__)

class SessionManagementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            try:
                # 1️⃣ Check if session object exists
                session = Session.objects.get(session_key=request.session.session_key)
                if session.expire_date < timezone.now():
                    # Session expired, mark user logged out
                    request.user.is_login_status = False
                    request.user.save(update_fields=['is_login_status'])
                    logger.info(f"Session expired for user: {request.user}")
                    logout(request)
            except Session.DoesNotExist:
                # No session found, force logout
                request.user.is_login_status = False
                request.user.save(update_fields=['is_login_status'])
                logger.info(f"No session found for user: {request.user}")
                logout(request)

            # 2️⃣ Optional: idle timeout (SESSION_COOKIE_AGE)
            last_access_str = request.session.get('last_access_time')
            now = timezone.now()
            if last_access_str:
                last_access = timezone.datetime.fromisoformat(last_access_str)
                elapsed = (now - last_access).total_seconds()
                if elapsed > settings.SESSION_COOKIE_AGE:
                    request.user.is_login_status = False
                    request.user.save(update_fields=['is_login_status'])
                    logger.info(f"Idle timeout for user: {request.user}")
                    logout(request)

            # 3️⃣ Update last access time
            request.session['last_access_time'] = now.isoformat()

        return response


"""
for auto logout use this code
#settings.py
SESSION_COOKIE_AGE = 1800  # 1800 seconds (30 minutes)
MIDDLEWARE = [
    'user_auth.middleware.SessionManagementMiddleware',  # Make sure this path is correct
]

#middleware.py
#decorators.py

use this python file or function
"""