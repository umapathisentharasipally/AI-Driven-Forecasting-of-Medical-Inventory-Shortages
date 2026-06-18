import sys, importlib, traceback
from pathlib import Path
print('cwd=', Path.cwd())
print('sys.path[0]=', sys.path[0])
try:
    pkg = importlib.import_module('app.api.v1.routes')
    print('imported package app.api.v1.routes ->', pkg, 'file=', getattr(pkg, '__file__', None))
    print('package attrs:', [a for a in dir(pkg) if not a.startswith('_')])
except Exception:
    print('failed importing package:')
    traceback.print_exc()

try:
    mod = importlib.import_module('app.api.v1.routes.auth_routes')
    print('imported module auth_routes ->', mod, 'file=', getattr(mod, '__file__', None))
    print('has router?', hasattr(mod, 'router'))
    print('router=', getattr(mod, 'router', None))
except Exception:
    print('failed importing module:')
    traceback.print_exc()

try:
    from app.api.v1.routes import auth_routes
    print('from app.api.v1.routes import auth_routes ->', auth_routes, 'type=', type(auth_routes))
    print('has router?', hasattr(auth_routes, 'router'))
    print('router=', getattr(auth_routes, 'router', None))
except Exception:
    print('failed "from package import auth_routes":')
    traceback.print_exc()

print('\nDone')
