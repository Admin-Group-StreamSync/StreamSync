from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


# --- decorador usuari SPM---

def cap_manager_permes(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            plataforma = request.user.profile.manager_de
            if plataforma:
                # Es un SPM. Lo mandamos a su panel.
                messages.info(request, "Ets un Manager. Aquesta és la teva àrea de treball.")
                return redirect('dashboard_manager', plataforma_nom=plataforma)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
