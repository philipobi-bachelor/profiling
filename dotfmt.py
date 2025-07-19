import re
import sys
import subprocess
from functools import reduce

isSpecial = lambda defStr: "graph " in defStr or "node " in defStr or "edge " in defStr
isEdge = lambda defStr: " -> " in defStr
isNode = lambda defStr: not (isSpecial(defStr) or isEdge(defStr))


def extractDefs(dotCode: str) -> tuple[str]:
    return tuple(
        item
        for defStr in (
            re.match(
                r"digraph \{(?P<graph>.*)\}",
                dotCode,
                re.DOTALL,
            )
            .group("graph")
            .split(";")
        )
        if (item := defStr.strip())
    )


def fmtDotCode(dotCode: str) -> str:
    print("Formatting code", file=sys.stderr)
    return subprocess.run(
        ("nop",),
        input=dotCode.encode(),
        stdout=subprocess.PIPE,
    ).stdout.decode()


def formatNodeLabel(match: re.Match, nodeName: str) -> str:
    label = match.group(0)
    [
        fileName,
        funcSpec,
        totalPercentage,
        selfPercentage,
        callCount,
    ] = label.split("\\n")

    funcSpec1 = None
    for segment in nodeName.split(" "):
        if "(" in segment:
            [funcSpec1, *_] = segment.split("(")
            break

    scopeDefs = (funcSpec,)
    if funcSpec1 is not None:
        scopeDefs = funcSpec1.split("::")
        scopeDefs = (
            *map(lambda s: s + "::", scopeDefs[:-1]),
            scopeDefs[-1],
        )

    return reduce(
        lambda s1, s2: s1 + s2,
        map(
            lambda s: s + "\l",
            (
                *scopeDefs,
                f"{totalPercentage} {selfPercentage}",
            ),
        ),
        "",
    )


def strip(dotCode: str) -> tuple[str]:
    print("Stripping code", file=sys.stderr)
    dotCode = re.sub(
        r"\b(?:nodesep|tooltip|ranksep|width|height|fontsize|labeldistance)=[^\n\]]*",
        "",
        fmtDotCode(dotCode),
    )
    defs = extractDefs(dotCode)

    getNodeName = lambda defStr: re.match(
        r"\s*\"(?P<name>.*?)\"", defStr, re.DOTALL
    ).group("name")

    stripNode = lambda defStr: re.sub(
        r"(?<=label=\").*?(?=\")",
        lambda match: print(defStr, file=sys.stderr) or formatNodeLabel(match, getNodeName(defStr)),
        defStr,
        flags=re.DOTALL,
    )

    return tuple((stripNode(defStr) if isNode(defStr) else defStr) for defStr in defs)


def orderDefs(defs: tuple[str]) -> tuple[str]:
    return (
        *filter(isSpecial, defs),
        *filter(isNode, defs),
        *filter(isEdge, defs),
    )


def main(dotCode: str) -> str:
    wrap = lambda dotCode: "digraph {\n" + dotCode + "\n}\n"
    dotCode = ";".join(strip(dotCode))
    return fmtDotCode(wrap(dotCode))
    dotCode = ";".join(orderDefs(extractDefs(dotCode)))
    return wrap(dotCode)


if __name__ == "__main__":
    sys.stdout.write(main(sys.stdin.read()))
