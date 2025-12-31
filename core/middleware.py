import threading

_thread_locals = threading.local()

def get_current_user():
    """Retorna el usuario de la request actual (si existe)."""
    return getattr(_thread_locals, 'user', None)

class RequestUserMiddleware:
    """
    Middleware que intercepta la request y guarda el usuario en thread-local
    para que esté disponible globalmente (ej. en señales o métodos save).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response
