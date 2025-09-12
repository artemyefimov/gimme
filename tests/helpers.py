from __future__ import annotations


class ClassThatNeedsInt:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def from_string(cls, s: str) -> ClassThatNeedsInt:
        return ClassThatNeedsInt(int(s))


class AnotherClassThatNeedsInt:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value
