import functools
import sys


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


if __name__ == "__main__":
    string = sys.argv[1]
    words = sys.argv[2:]
    val = 9999

    for word in words:
        measure = lev(string, word)
        if measure < val:
            ret = word
            val = measure

    print(ret)
