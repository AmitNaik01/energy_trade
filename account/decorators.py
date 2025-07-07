from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(required_role):
    def decorator(view_func):
        @login_required(login_url='login_view')
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'role'):
                if request.user.role == required_role:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "Unauthorized access: You do not have permission.")
                    return redirect('login_view')  # or render 403 page
            else:
                messages.error(request, "Invalid user role.")
                return redirect('login_view')
        return _wrapped_view
    return decorator
