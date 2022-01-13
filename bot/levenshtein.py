import functools
import sys


IGNORE = (
    "bash",
    "blacklist",
    "cancel",
    "eval",
    "exec",
    "log",
    "raise",
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


string = sys.argv[1]
words = sys.argv[2:]
val = 9999

for word in words:
    if word in IGNORE:
        continue

    measure = lev(string, word)
    if measure < val:
        ret = word
        val = measure

print(ret)
