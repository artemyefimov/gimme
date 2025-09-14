from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from itertools import count

from gimme.injectors import Injector
from gimme.providers import injector_local, singleton
from gimme.utils import get
from tests.helpers import AnotherClassThatNeedsInt, ClassThatNeedsInt


def test_inject_instances_of_primitive_types() -> None:
    providers = {}
    providers[int] = 1
    providers[str] = "hello"
    providers[bool] = True

    injector = Injector(providers)

    assert injector.run(get(int)) == 1
    assert injector.run(get(str)) == "hello"
    assert injector.run(get(bool)) is True


def test_inject_instances_of_generic_tuples() -> None:
    providers = {}
    providers[tuple[int]] = (1,)
    providers[tuple[int, int]] = (1, 2)
    providers[tuple[int, int, int]] = (1, 2, 3)

    injector = Injector(providers)

    assert injector.run(get(tuple[int])) == (1,)
    assert injector.run(get(tuple[int, int])) == (1, 2)
    assert injector.run(get(tuple[int, int, int])) == (1, 2, 3)


def test_inject_instances_of_generic_lists() -> None:
    providers = {}
    providers[list[int]] = [1, 2]
    providers[list[str]] = ["1", "2"]
    providers[list[bool]] = [True, False]
    providers[list[list[int]]] = [[1], [2], [3]]

    injector = Injector(providers)

    assert injector.run(get(list[int])) == [1, 2]
    assert injector.run(get(list[str])) == ["1", "2"]
    assert injector.run(get(list[bool])) == [True, False]
    assert injector.run(get(list[list[int]])) == [[1], [2], [3]]


def test_inject_instances_of_generic_dicts() -> None:
    providers = {}
    providers[dict[str, int]] = {"key": 0}
    providers[dict[str, str]] = {"key": "value"}

    injector = Injector(providers)

    assert injector.run(get(dict[str, int])) == {"key": 0}
    assert injector.run(get(dict[str, str])) == {"key": "value"}


def test_provide_dependency_to_class_constructor() -> None:
    providers = {}
    providers[int] = 1

    injector = Injector(providers)

    result = injector.run(get(ClassThatNeedsInt))
    assert result.value == 1


def test_use_classmethod_as_provider() -> None:
    providers = {}
    providers[str] = "123"
    providers[ClassThatNeedsInt] = ClassThatNeedsInt.from_string

    injector = Injector(providers)

    result = injector.run(get(ClassThatNeedsInt))
    assert result.value == 123


def test_inject_context_scoped_dependency() -> None:
    @contextmanager
    def provide_session() -> Iterator[str]:
        yield "session"

    providers = {}
    providers[str] = provide_session

    injector = Injector(providers)

    assert injector.run(get(str)) == "session"


def test_inject_context_manager() -> None:
    @contextmanager
    def provide_session() -> Iterator[str]:
        yield "session"

    providers = {}
    providers[AbstractContextManager[str]] = provide_session
    providers[str] = provide_session

    injector = Injector(providers)

    assert injector.run(get(str)) == "session"

    with injector.run(get(AbstractContextManager[str])) as session:
        assert session == "session"


def test_inject_next_element_from_iterator() -> None:
    providers = {}
    providers[int] = count()

    injector = Injector(providers)

    assert injector.run(get(int)) == 0
    assert injector.run(get(int)) == 1
    assert injector.run(get(int)) == 2


def test_injector_iterator_itself() -> None:
    iterator = count()

    providers = {}
    providers[int] = iterator
    providers[Iterator[int]] = iterator

    injector = Injector(providers)

    assert injector.run(get(int)) == 0
    assert injector.run(get(Iterator[int])) is iterator
    assert injector.run(get(int)) == 1


def test_inject_singleton() -> None:
    iterator = count()

    def next_number() -> int:
        return next(iterator)

    providers = {}
    providers[int] = singleton(next_number)

    injector = Injector(providers)
    assert injector.run(get(int)) == 0
    assert injector.run(get(int)) == 0

    another_injector = Injector(providers)
    assert another_injector.run(get(int)) == 0
    assert another_injector.run(get(int)) == 0


def test_inject_injector_local() -> None:
    iterator = count()

    def next_number() -> int:
        return next(iterator)

    providers = {}
    providers[int] = injector_local(next_number)

    injector = Injector(providers)
    assert injector.run(get(int)) == 0
    assert injector.run(get(int)) == 0

    another_injector = Injector(providers)
    assert another_injector.run(get(int)) == 1
    assert another_injector.run(get(int)) == 1


def test_dependencies_are_cached_within_a_single_run() -> None:
    provide_int_calls_count = 0

    @contextmanager
    def provide_int() -> Iterator[int]:
        nonlocal provide_int_calls_count
        provide_int_calls_count += 1
        yield 1

    def calculate_sum(a: ClassThatNeedsInt, b: AnotherClassThatNeedsInt) -> int:
        return a.value + b.value

    providers = {}
    providers[int] = provide_int
    providers[ClassThatNeedsInt] = ClassThatNeedsInt
    providers[AnotherClassThatNeedsInt] = AnotherClassThatNeedsInt

    injector = Injector(providers)
    injector.run(calculate_sum)

    assert provide_int_calls_count == 1


def test_inject_injector_in_injector_local_scope() -> None:
    def needs_injector(injector: Injector) -> bool:  # noqa: ARG001
        return True

    providers = {}
    providers[bool] = injector_local(needs_injector)

    injector = Injector(providers)

    assert injector.run(get(bool))
