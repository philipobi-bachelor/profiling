import re
import sys
import subprocess
from functools import reduce

isSpecial = lambda defStr: "graph " in defStr or "node " in defStr or "edge " in defStr
isEdge = lambda defStr: " -> " in defStr
isNode = lambda defStr: not (isSpecial(defStr) or isEdge(defStr))


def extractDefs(dotCode: str) -> tuple[str]:
    return tuple(
        filter(
            lambda s: s.strip(),
            re.match(
                r"digraph \{(?P<graph>.*?)\}",
                dotCode,
                re.DOTALL,
            )
            .group("graph")
            .split(";"),
        )
    )


def fmtDotCode(dotCode: str) -> str:
    return subprocess.run(
        ("nop",),
        input=dotCode.encode(),
        stdout=subprocess.PIPE,
    ).stdout.decode()



def strip(dotCode: str) -> tuple[str]:
    dotCode = re.sub(
        r"\b(?:nodesep|tooltip|ranksep|width|height|fontsize|labeldistance)=[^\n\]]*",
        "",
        fmtDotCode(dotCode),
    )
    defs = extractDefs(dotCode)

    def stripNodeLabel(match: re.Match) -> str:
        label = match.group(0)
        [
            fileName,
            funcSpec,
            totalPercentage,
            selfPercentage,
            callCount,
        ] = label.split("\\n")
        if " " in funcSpec:
            [_, funcSpec] = funcSpec.split(" ")

        scopeDefs = funcSpec.split("::")
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

    stripNode = lambda defStr: re.sub(
        r"(?<=label=\").*?(?=\")",
        stripNodeLabel,
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
    dotCode = fmtDotCode(wrap(dotCode))
    dotCode = ";".join(orderDefs(extractDefs(dotCode)))
    return wrap(dotCode)

if __name__ == "__main__":
    sys.stdout.write(main(sys.stdin.read()))
