from collections.abc import Iterator
from contextlib import contextmanager
from sqlite3 import Connection, connect

from gimme.injectors import Injector


class DatabaseUrl(str):
    pass


@contextmanager
def get_connection(database_url: DatabaseUrl) -> Iterator[Connection]:
    with connect(database_url) as connection:
        yield connection


class HelloWorldRepository:
    _connection: Connection

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def fetch_hello_world(self) -> str:
        return self._connection.execute("SELECT 'Hello World!';").fetchone()[0]


def hello_world(repository: HelloWorldRepository) -> None:
    print(repository.fetch_hello_world())


if __name__ == "__main__":
    providers = {}
    providers[DatabaseUrl] = ":memory:"
    providers[Connection] = get_connection
    providers[HelloWorldRepository] = HelloWorldRepository

    injector = Injector(providers)

    injector.run(hello_world)
