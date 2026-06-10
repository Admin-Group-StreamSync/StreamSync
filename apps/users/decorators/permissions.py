# --- decorador usuari SPM---
from functools import wraps

from django.shortcuts import redirect


def cap_manager_permes(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Els superusuaris (admin) mai es redirigeixen
        if request.user.is_authenticated and not request.user.is_superuser:
            if hasattr(request.user, 'profile'):
                plataforma = request.user.profile.manager_de
                if plataforma:
                    # Evitar bucle infinit: si ja estem al dashboard del manager, no redirigir
                    current_plataforma = kwargs.get('plataforma_nom')
                    if current_plataforma != plataforma:
                        return redirect('dashboard_manager', plataforma_nom=plataforma)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
