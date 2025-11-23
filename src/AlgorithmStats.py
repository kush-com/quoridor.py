import importlib
import threading
import atexit
from collections import defaultdict
from functools import wraps
import os


class AlgorithmStats:
    _counters = defaultdict(int)
    _lock = threading.Lock()
    _installed = False

    @classmethod
    def increment(cls, name: str, amount: int = 1):
        with cls._lock:
            cls._counters[name] += amount

    @classmethod
    def wrap_function(cls, module, func_name: str, display_name: str = None):
        # Try to wrap attribute on the module
        orig = getattr(module, func_name, None)
        if orig is not None:
            if getattr(orig, "__alg_wrapped__", False):
                return

            @wraps(orig)
            def wrapper(*args, **kwargs):
                cls.increment(display_name or f"{module.__name__}.{func_name}")
                return orig(*args, **kwargs)

            wrapper.__alg_wrapped__ = True
            setattr(module, func_name, wrapper)

            # Also replace references in other loaded modules that imported the function
            import sys
            for m in list(sys.modules.values()):
                try:
                    if m is None:
                        continue
                    if getattr(m, func_name, None) is orig:
                        setattr(m, func_name, wrapper)
                except Exception:
                    continue
            return

        # If not found as module attr, try to wrap as a method on classes inside the module
        for attr_name in dir(module):
            try:
                attr = getattr(module, attr_name)
            except Exception:
                continue
            # If attr is a class, check for method
            if isinstance(attr, type) and hasattr(attr, func_name):
                method = getattr(attr, func_name)
                if getattr(method, "__alg_wrapped__", False):
                    continue

                @wraps(method)
                def class_wrapper(*args, __method=method, **kwargs):
                    cls.increment(display_name or f"{module.__name__}.{attr_name}.{func_name}")
                    return __method(*args, **kwargs)

                class_wrapper.__alg_wrapped__ = True
                try:
                    setattr(attr, func_name, class_wrapper)
                except Exception:
                    # Could be built-in or otherwise not writable
                    continue

    @classmethod
    def install(cls):
        if cls._installed:
            return
        cls._installed = True
        # Attempt to wrap known algorithm entry points
        try:
            path_mod = importlib.import_module('src.Path')
            cls.wrap_function(path_mod, 'BreadthFirstSearch', 'BreadthFirstSearch')
            cls.wrap_function(path_mod, 'Dijkstra', 'Dijkstra')
            cls.wrap_function(path_mod, 'AStar', 'AStar')
        except Exception:
            pass

        try:
            runner = importlib.import_module('src.player.RunnerBot')
            cls.wrap_function(runner, 'moveAlongTheShortestPath', 'RunnerBot.moveAlongTheShortestPath')
        except Exception:
            pass

        try:
            builder = importlib.import_module('src.player.BuilderBot')
            cls.wrap_function(builder, 'computeFencePlacingImpacts', 'BuilderBot.computeFencePlacingImpacts')
            cls.wrap_function(builder, 'getFencePlacingWithTheHighestImpact', 'BuilderBot.getFencePlacingWithTheHighestImpact')
        except Exception:
            pass

        try:
            randombot = importlib.import_module('src.player.RandomBot')
            cls.wrap_function(randombot, 'placeFenceRandomly', 'RandomBot.placeFenceRandomly')
        except Exception:
            pass

        try:
            mybot = importlib.import_module('src.player.MyBot')
            cls.wrap_function(mybot, 'play', 'MyBot.play')
        except Exception:
            pass

        # Register an atexit hook to always emit a report
        atexit.register(cls.report)

    @classmethod
    def report(cls, file_path: str = None):
        # If file_path not provided, write to repository root algorithm_stats.txt
        if file_path is None:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            file_path = os.path.join(repo_root, 'algorithm_stats.txt')
        lines = []
        lines.append('Algorithm call summary:')
        with cls._lock:
            for name, count in sorted(cls._counters.items(), key=lambda x: (-x[1], x[0])):
                lines.append(f'- {name}: {count}')
        report = '\n'.join(lines)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
        except Exception:
            pass
        # Also print to stdout
        print('\n' + report + '\n')
