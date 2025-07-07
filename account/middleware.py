from django.shortcuts import redirect
from django.conf import settings

class Handle404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            # Redirect to homepage or custom 404 page
            return redirect('login_view')  # or 'dashboard' or render a custom 404.html
        return response
