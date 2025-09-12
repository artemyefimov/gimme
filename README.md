# gimme

Simple, type-driven dependency injection for Python.

## Installation

Install directly from the Git repository:

```bash
pip install git+https://github.com/artemyefimov/gimme.git
```

## Usage

### Basics

**First**, define providers for the types you want to inject (we’ll cover the different kinds of providers shortly):

```python
providers = {}
providers[A] = ...
providers[B] = ...
```

You don’t need a provider for every type. For example, if providers for `A` and `B` are available, the injector can automatically construct an instance of `C`:

```python
class C:
    def __init__(self, a: A, b: B) -> None:
        ...
```

**Second**, create an `Injector` with providers:

```python
from gimme.injectors import Injector

injector = Injector(providers)
```

**Finally**, use injector to call a function. Dependencies are resolved and passed automatically:

```python
def function(a: A, b: B, c: C) -> D:
    ...

injector.run(function)
```

**Note:** During a single run, each dependency is created only once and then cached.
If multiple parameters require the same type, the same instance is reused within that call.

### get function

For the sake of simplicity, we'll use a special `get` function to demonstrate how injector works. This function returns a callable that requires an instance of a given type.

For example:

```python
from gimme.utils import get

get(int)           # creates a function that requires an `int` parameter
get(list[bytes]])  # creates a function that requires a `list[bytes]` parameter
```

### Instance provider

This is the simplest kind of provider, the injector will return the value as-is:

```python
providers[str] = "hello"
...
assert injector.run(get(str)) == "hello"
```

This also works with generic type aliases.

```python
providers[str, int] = ("first", 1)
...
assert injector.run(get(tuple[str, int])) == ("first", 1)
```

### Callable provider

For a callable provider, injector always calls it and returns the result:

```python
providers[int] = lambda: 1
...
assert injector.run(get(int)) == 1
```

Any parameters of a callable are automatically resolved and injected:

```python
def parse_int(s: str) -> int:
    return int(s)

providers[str] = "123"
providers[int] = parse_int
...

assert injector.run(get(int)) == 123
```

### Context manager provider

Some dependencies are meant to exist only within a single run and may require additional cleanup after being used. For this purpose, use context manager providers:

```python
@contextmanager
def get_session() -> Iterator[str]:
    try:
        print("Creating a new session...")
        yield "session"
    finally:
        print("Doing a cleanup...")

def needs_session(session: str) -> None:
    print("Using session...")

providers[str] = get_session
...

injector.run(needs_session)

# Output:
# Creating a new session...
# Using a session...
# Doing a cleanup...
```

You can also obtain a context manager directly. However, remember that all intermediate context manager dependencies are closed when `run` completes. If context manager depends on any, it may lead to problems. Consider this example:

```python
@contextmanager
def get_numbers() -> Iterator[list[int]]:
    numbers = [1, 2, 3]
    try:
        yield numbers
    finally:
        # Pay attention! Numbers are cleared when context manager exits
        numbers.clear()

@contextmanager
def get_first_number(numbers: list[int]) -> Iterator[int]:
    yield numbers[0]

...

providers[list[int]] = get_numbers
providers[int] = get_first_number
providers[AbstractContextManager[int]] = get_first_number

...

# This works fine:
assert injector.run(get(int)) == 1

# IndexError is raised, because the list is already empty at that point:
with injector.run(get(AbstractContextManager[int])) as number:
    ...
```

**Warning:** The `Injector` is primarily designed to run functions with injection, rather than retrieve dependencies directly. Using context managers directly may cause lifecycle issues, so use this carefully.

### Iterator provider

If a provider is an `Iterator`, then `Injector` will automatically consume its next element each time it is requested:

```python
from itertools import count

...
providers[int] = count(start=1)

...
# Every time we get the next iterator's element:
assert injector.run(get(int)) == 1
assert injector.run(get(int)) == 2
```

As with context managers, you can inject an `Iterator` itself:

```python
...
providers[Iterator[int]] = count(start=1)

...
iterator = injector.run(get(Iterator[int]))
assert next(iterator) == 1
assert next(iterator) == 2
```

### Singleton scope

The `singleton` wrapper caches the result of a provider function, ensuring the same instance is returned every time:

```python
from itertools import count
from gimme.providers import singleton

iterator = count(start=1)

def get_next_number() -> int:
    return next(iterator)

...
providers[int] = singleton(get_next_number)

...
assert injector.run(get(int)) == 1
assert injector.run(get(int)) == 1
```

### Injector local scope

The `injector_local` wrapper caches the result of a provider function separately for each `Injector` instance. This is useful when multiple injectors share the same provider, but should not share the same cached value:

```python
from itertools import count
from gimme.providers import injector_local

...
providers[int] = lambda: count(start=1)

...
injector = Injector(providers)
assert injector.run(get(int)) == 1
assert injector.run(get(int)) == 2

another_injector = Injector(providers)
assert another_injector.run(get(int)) == 1
assert another_injector.run(get(int)) == 2
```
