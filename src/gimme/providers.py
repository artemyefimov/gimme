from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Concatenate
from weakref import WeakKeyDictionary

from gimme.injectors import Injector


@dataclass(slots=True)
class _Cached[T]:
    value: T


def singleton[**P, R](
    function: Callable[P, R],
    /,
) -> Callable[P, R]:
    cached: _Cached[R] | None = None

    def provider(*args: P.args, **kwargs: P.kwargs) -> R:
        nonlocal cached
        if cached is not None:
            return cached.value

        result = function(*args, **kwargs)
        cached = _Cached(result)
        return result

    provider.__annotations__ = function.__annotations__.copy()
    provider.__signature__ = signature(function)  # type: ignore

    return provider


def injector_local[**P, R](
    function: Callable[P, R],
    /,
) -> Callable[Concatenate[Injector, P], R]:
    cache = WeakKeyDictionary[Injector, R]()

    def provider(injector: Injector, *args: P.args, **kwargs: P.kwargs) -> R:
        if injector in cache:
            return cache[injector]

        result = function(*args, **kwargs)
        cache[injector] = result
        return result

    original_signature = signature(function)
    updated_signature = original_signature.replace(
        parameters=[
            Parameter("injector", Parameter.POSITIONAL_ONLY, annotation=Injector),
            *original_signature.parameters.values(),
        ],
    )

    provider.__annotations__ = function.__annotations__.copy()
    provider.__annotations__["injector"] = Injector
    provider.__signature__ = updated_signature  # type: ignore

    return provider
