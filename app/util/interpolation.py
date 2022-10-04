from collections import namedtuple
import re
from typing import List, Optional

_replacement_regex = r"<([^:>]*):?([^>]*)>"

Interpolation = namedtuple('Interpolation', ['field', 'value', 'default_value'])


def parse_interpolations(*cmds) -> List[Interpolation]:
    interpolations = []
    field_names = set()
    for cmd in cmds:
        matches = re.findall(_replacement_regex, cmd)
        for m in matches:
            value = ''
            if m:
                field = m[0].strip()
                if len(m) == 2:
                    value = m[1].strip()
                interpolations.append(Interpolation(field=field, value=value, default_value=value))
                assert field not in field_names, f'A duplicate replacement ' \
                                                 f'field detected during interpolation - field: "{field}" \n' \
                                                 f'All replacement fields must have unique names per process definition'
                field_names.add(field)
    return interpolations


def interpolate(text: str, interpolations: Optional[List[Interpolation]] = None) -> str:
    if not interpolations:
        return text
    for interp in interpolations:
        replace_regex = rf'<\s*{interp.field}\s*:?\s*{interp.default_value}\s*>'
        text = re.sub(replace_regex, interp.value, text)

    return text
