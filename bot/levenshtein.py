import functools
import sys
from typing import List, Tuple


IGNORE: Tuple[str, ...] = (
    "bash",
    "blacklist",
    "cancel",
    "eval",
    "exec",
    "log",
    "sql",
    "sh",
    "ssh",
    "state",
    "status",
    "task",
    "tasks",
    "thread",
    "threads",
    "trace",
)


@functools.cache
def lev(i: str, j: str) -> int:
    if not i:
        return len(j)

    if not j:
        return len(i)

    if i[0] == j[0]:
        return lev(i[1:], j[1:])

    return 1 + min(
        lev(i, j[1:]),
        lev(i[1:], j),
        lev(i[1:], j[1:]),
    )


string: str = sys.argv[1]
words: List[str] = sys.argv[2:]
val: int = 9999

# Typing
measure: int
ret: str

for word in words:
    if word in IGNORE:
        continue

    measure = lev(string, word)
    if measure < val:
        ret = word
        val = measure

print(ret)
