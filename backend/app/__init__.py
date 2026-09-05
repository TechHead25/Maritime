# App package

# Startup sanity check to prevent benchmark fixture imports in production
import importlib
import sys

def _check_forbidden_imports():
    forbidden_prefixes = ["benchmark", "tests"]
    for name, module in list(sys.modules.items()):
        if any(name.startswith(p) for p in forbidden_prefixes):
            raise RuntimeError(f"Forbidden benchmark module imported in production: {name}")

# Run the check when the package is imported
_check_forbidden_imports()

