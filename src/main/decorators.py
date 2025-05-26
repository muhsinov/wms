from functools import wraps
from django.shortcuts import redirect

def employee_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('employee_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped
