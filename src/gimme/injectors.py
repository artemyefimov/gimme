from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, MutableMapping
from contextlib import AbstractContextManager, ExitStack
from inspect import Parameter
from types import TracebackType
from typing import Any, Self

from gimme.utils import injectable_signature, is_instance_of_type_hint


class Injector:
    _providers: Mapping[Any, Any]

    def __init__(self, providers: Mapping[Any, Any]) -> None:
        self._providers = {**providers, Injector: self}

    def run[R](self, function: Callable[..., R]) -> R:
        with _InjectorContext(self._providers) as in_context:
            return in_context.call_with_injection(function)


class _InjectorContext(AbstractContextManager["_InjectorContext"]):
    _exit_stack: ExitStack
    _cached_dependencies: MutableMapping[Any, Any]

    def __init__(self, providers: Mapping[Any, Any]) -> None:
        self._providers = providers
        self._exit_stack = ExitStack()
        self._cached_dependencies = {}

    def call_with_injection[R](self, function: Callable[..., R]) -> R:
        args = []
        kwargs = {}
        signature = injectable_signature(function)

        for parameter in signature.parameters.values():
            value = self.provide(parameter.annotation)

            match parameter.kind:
                case Parameter.POSITIONAL_OR_KEYWORD | Parameter.POSITIONAL_ONLY:
                    args.append(value)
                case Parameter.KEYWORD_ONLY:
                    kwargs[parameter.name] = value

        return function(*args, **kwargs)

    def provide(self, key: Any) -> Any:
        if key in self._cached_dependencies:
            return self._cached_dependencies[key]

        provider = self._providers.get(key, key)
        value = self.call_with_injection(provider) if callable(provider) else provider

        if not is_instance_of_type_hint(value, key):
            value = self.unwrap(value)

        self._cached_dependencies[key] = value
        return value

    def unwrap(self, value: Any) -> Any:
        match value:
            case AbstractContextManager() as context_manager:
                return self._exit_stack.enter_context(context_manager)
            case Iterator() as iterator:
                return next(iterator)
            case _:
                return value

    def __enter__(self) -> Self:
        self._exit_stack.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> bool | None:
        self._cached_dependencies.clear()
        return self._exit_stack.__exit__(exc_type, exc_value, traceback)
