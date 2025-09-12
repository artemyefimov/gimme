from __future__ import annotations

from collections.abc import Callable
from inspect import Signature, get_annotations, isclass, isfunction, ismethod, signature
from typing import Any, get_origin


def injectable_signature(instance: Any) -> Signature:
    target: Callable[..., Any]
    drop_self: bool

    if isclass(instance):
        target = instance.__init__
        drop_self = True
    elif isfunction(instance) or ismethod(instance):
        target = instance
        drop_self = ismethod(instance)
    elif callable(instance):
        target = instance.__call__
        drop_self = True
    else:
        message = f"Object is not callable: {instance!r}"
        raise TypeError(message)

    original_signature = signature(target)
    parameters = list(original_signature.parameters.values())
    type_hints = get_annotations(target, eval_str=True)

    if drop_self and parameters[0].name in ("self", "cls"):
        parameters.pop(0)

    parameters = [
        parameter.replace(annotation=type_hints[parameter.name])
        for parameter in parameters
    ]

    return original_signature.replace(parameters=parameters, return_annotation=None)


def is_instance_of_type_hint(instance: Any, type_hint: Any) -> bool:
    origin = get_origin(type_hint) or type_hint
    return isinstance(instance, origin)


def get(type_: Any) -> Callable[[Any], Any]:
    def wrapper(instance: Any) -> Any:
        return instance

    wrapper.__annotations__["instance"] = type_

    return wrapper
