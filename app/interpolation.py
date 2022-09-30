from collections import namedtuple
import re
from typing import List

_replacement_regex = r"<([^:>]*):?([^>]*)>"

Interpolation = namedtuple('Interpolation', ['field', 'value'])


def parse_interpolations(*cmds) -> List[Interpolation]:
    interpolations = []
    for cmd in cmds:
        matches = re.findall(_replacement_regex, cmd)
        for m in matches:
            value = ''
            if m:
                field = m[0].strip()
                if len(m) == 2:
                    value = m[1].strip()
                interpolations.append(Interpolation(field=field, value=value))
    return interpolations
