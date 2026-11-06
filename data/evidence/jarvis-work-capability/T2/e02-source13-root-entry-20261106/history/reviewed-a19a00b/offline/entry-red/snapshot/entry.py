import time
ENTRY_NS=time.monotonic_ns()

def execute(context,origin,backend_factory):
    raise ValueError('Unconfigured enclosing root')

def clean_environment(values):
    raise ValueError('Unconfigured child environment')

def bootstrap(context,callback):
    raise ValueError('Unconfigured clean child bootstrap')
