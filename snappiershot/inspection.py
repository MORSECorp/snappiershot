""" Inspection into caller functions. """
import inspect
from pathlib import Path
from typing import Any, Dict, NamedTuple


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

        Unfortunately, there currently is no known (stable) way to get the fully
          qualified function name of a static method. If the calling function is a
          static method, the unqualified function name is returned.

        Args:
            frame_index: The index of the frame of the caller function.
              This defaults to 2 as, in the case for this package, it's expected
              that the caller function calls a method on the Snapshot object, which
              in turn calls this function.

        Returns:
            CallerInfo
        """
        frame, file, _, function, *_ = inspect.stack()[frame_index]
        try:
            arg_info = inspect.getargvalues(frame)
        finally:
            # Explicit cleanup as a safety precaution. Suggested by the inspect module docs:
            # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
            del frame

        caller_locals = arg_info.locals
        args = {name: caller_locals[name] for name in arg_info.args}

        # Remove any self or cls variables, but use them to set the fully qualified function name.
        if "self" in args:
            function = f"{args.pop('self').__class__.__qualname__}.{function}"
        elif "cls" in args:
            function = f"{args.pop('cls').__qualname__}.{function}"

        return CallerInfo(Path(file), function, args)
