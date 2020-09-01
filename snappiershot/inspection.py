""" Inspection into caller functions. """
import inspect
from pathlib import Path
from types import CodeType, FunctionType
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
            RuntimeError: If the caller function could not be determined.

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
            ) from NotImplementedError
        if function == "<module>":  # pragma: no cover
            # If the call is from a python file/module, not a function.
            raise NameError(
                "The caller was detected to be a module, not a function. "
                "These types of calls are not supported. "
            ) from NotImplementedError

        caller_locals = caller_arg_info.locals
        args = {name: caller_locals[name] for name in caller_arg_info.args}

        # Get the first argument to the function, if it exists.
        first_arg = None
        if caller_arg_info.args:
            first_arg = args[caller_arg_info.args[0]]

        # Filter any "self" or "cls" variables, which might be named something else.
        is_cls_or_self = has_caller_method(first_arg, function, caller_code)
        if inspect.isclass(first_arg) and is_cls_or_self:
            # If the function is a classmethod.
            args.pop(caller_arg_info.args[0])
            function = f"{first_arg.__qualname__}.{function}"
        elif is_cls_or_self:
            # If the function is a regular method of a class.
            args.pop(caller_arg_info.args[0])
            function = f"{first_arg.__class__.__qualname__}.{function}"
        else:
            if function not in caller_globals:
                # If this function does not have a "self" or "cls" argument and is not in the
                #   globals of the module, then the function is a staticmethod and must be
                #   specially handled to get the fully-qualified function name.
                for func in recursive_yield_staticmethods(caller_globals, function, file):
                    if func.__code__ == caller_code:
                        function = func.__qualname__
                        break
                else:
                    raise RuntimeError(
                        "The caller function could not be determined. "
                        "This might be due to the caller function being an inner function "
                        "which are currently not supported. "
                    ) from NotImplementedError

        return CallerInfo(Path(file), function, args)


def recursive_yield_staticmethods(
    haystack: Dict[str, Any], function: str, file: str
) -> Iterator[FunctionType]:
    """ Recursively attempt to sort through the haystack looking classes with
    staticmethods with the specified function name, and yields these functions.

    Args:
        haystack: The output of a ``vars`` call on a class or module.
        function: The name of the function to be yielded.
        file: The file containing the staticmethod.

    Yields:
        Staticmethods with the specified function name.
    """
    reduced_haystack = (
        obj
        for obj in haystack.values()
        if inspect.isclass(obj)
        # Filter builtins to guard against TypeErrors when calling inspect.getfile on builtins.
        and not inspect.isbuiltin(obj) and inspect.getfile(obj) == file
    )

    for cls in reduced_haystack:
        if is_staticmethod(cls, function):
            yield getattr(cls, function)
        yield from recursive_yield_staticmethods(vars(cls), function, file)


def has_caller_method(kls: object, function_name: str, function_code: CodeType) -> bool:
    """ Determines the function with specified function name and code is a
    method of the specified class.

    Args:
        kls: The class to test. (Can be unsubstantiated)
        function_name: The name of the function.
        function_code: The compiled code of the function.
          This is the value of the ``__code__`` attribute for a function.
    """
    if hasattr(kls, function_name):
        method = getattr(kls, function_name)
        return inspect.ismethod(method) and method.__code__ == function_code
    return False


def is_staticmethod(kls: object, method: str) -> bool:
    """ Determines if the method of the class is a staticmethod.

    Args:
        kls: The class to test for the staticmethod.
        method: The name of the method to be checked. This method does not need
          to exist; if it does not exist, this function returns False.
    """
    bound_method = vars(kls).get(method, False)
    return bound_method and isinstance(bound_method, staticmethod)
