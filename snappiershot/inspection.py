""" Inspection into caller functions. """
import inspect
from pathlib import Path
from types import FunctionType
from typing import Any, Dict, Iterator, NamedTuple


class CallerInfo(NamedTuple):
    # noinspection PyUnresolvedReferences
    """ Information about the caller function.

    Args:
        file: The path to the file containing the caller function.
        function: The fully qualified name of the caller function.
        args: A dictionary mapping name to value for the arguments of the caller function.
    """

    file: Path
    function: str
    args: Dict[str, Any]

    @classmethod
    def from_call_stack(cls, frame_index: int = 2) -> "CallerInfo":
        """ Collect the CallerInfo from the call stack.

        Args:
            frame_index: The index of the frame of the caller function.
              This defaults to 2 as, in the case for this package, it's expected
              that the caller function calls a method on the Snapshot object, which
              in turn calls this function.

        Raises:
            FileNotFoundError: If the caller function was defined within the Python REPL.
            NameError: If the call came from a python module/file and not a function.

        Returns:
            CallerInfo
        """
        frame, file, _, function, *_ = inspect.stack()[frame_index]
        try:
            caller_arg_info = inspect.getargvalues(frame)
            caller_globals = frame.f_globals
            caller_code = frame.f_code
        finally:
            # Explicit cleanup as a safety precaution. Suggested by the inspect module docs:
            # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
            del frame

        # Filter edge cases.
        if file == "<input>":  # pragma: no cover
            # If the caller function was defined within the REPL.
            raise FileNotFoundError(
                "The caller function was detected to exist in the Python REPL. "
                "These types of functions are not supported. "
            )
        if function == "<module>":  # pragma: no cover
            # If the call is from a python file/module, not a function.
            raise NameError(
                "The caller was detected to be a module, not a function. "
                "These types of calls are not supported. "
            )

        caller_locals = caller_arg_info.locals
        args = {name: caller_locals[name] for name in caller_arg_info.args}

        # Remove any self or cls variables, but use them to set the fully qualified function name.
        if "self" in args:
            function = f"{args.pop('self').__class__.__qualname__}.{function}"
        elif "cls" in args:
            function = f"{args.pop('cls').__qualname__}.{function}"
        else:
            if function not in caller_globals:
                module = inspect.getmodulename(file)
                for func in recursive_find_staticmethod(caller_globals, function, module):
                    print(func.__qualname__)
                    if func.__code__ == caller_code:
                        function = func.__qualname__

        return CallerInfo(Path(file), function, args)


def recursive_find_staticmethod(
    haystack: Dict[str, object], function: str, module_name: str
) -> Iterator[FunctionType]:
    """ Recursively attempt to sort through the haystack looking classes with
    staticmethods with the specified function name, and yields these functions.

    Args:
        haystack: The output of a ``vars`` call on a class or module.
        function: The name of the function to be yielded.
        module_name: The name of the module containing the staticmethod.

    Yields:
        Staticmethods with the specified function name.
    """

    def is_class_within_module(obj: object) -> bool:
        """ Predicate that filters for classes contained within ``module_name``. """
        return inspect.isclass(obj) and obj.__module__.endswith(module_name)

    for cls in filter(is_class_within_module, haystack.values()):
        if is_staticmethod(cls, function):
            yield getattr(cls, function)
        yield from recursive_find_staticmethod(vars(cls), function, module_name)


def is_staticmethod(cls: object, method: str) -> bool:
    """ Determines if the method of the class is a staticmethod.

    Args:
        cls: The class to test for the staticmethod.
        method: The name of the method to be checked. This method does not need
          to exist; if it does not exist, this function returns False.
    """
    bound_method = vars(cls).get(method, False)
    return bound_method and isinstance(bound_method, staticmethod)
