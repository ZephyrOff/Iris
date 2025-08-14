import threading

_current_environment = threading.local()

def set_environment(env):
    _current_environment.value = env

def get_environment():
    return getattr(_current_environment, 'value', None)

class EnvironmentContext:
    def __init__(self, env):
        self.env = env
        self.old_env = None

    def __enter__(self):
        self.old_env = get_environment()
        set_environment(self.env)

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_environment(self.old_env)
