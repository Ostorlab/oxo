"""Runtime registry that references all supported runtimes."""

from ostorlab import exceptions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.lite_local import runtime as lite_local_runtime
from ostorlab.runtimes.cloud import runtime as cloud_runtime


class RuntimeNotFoundError(exceptions.OstorlabError):
    """Specified runtime is not found."""


def select_runtime(runtime_type: str, *args, **kwargs) -> runtime.Runtime:
    """Selects and instantiate runtime by type.

    Args:
        runtime_type: The type of runtime to create.
        *args: Runtime args.
        **kwargs: Runtime kwargs.

    Returns:
        Runtime instance.
    """
    if runtime_type == "local":
        return local_runtime.LocalRuntime(*args, **kwargs)
    elif runtime_type == "litelocal":
        return lite_local_runtime.LiteLocalRuntime(*args, **kwargs)
    elif runtime_type == "cloud":
        return cloud_runtime.CloudRuntime(*args, **kwargs)
    else:
        raise RuntimeNotFoundError(f"runtime type {runtime_type} not found")
