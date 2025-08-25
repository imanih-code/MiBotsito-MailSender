import re
from typing import Any, Dict

def render_mdx(template: str, context: Dict[str, Any]) -> str:
    repeat_pattern = re.compile(
        r'::repeat\s+(\w+)\s*\n(.*?)::endrepeat',
        re.DOTALL
    )

    def resolve_path(path: str, ctx: Dict[str, Any]):
        val = ctx
        for part in path.split('.'):
            val = val.get(part) if isinstance(val, dict) else getattr(val, part)
        return val

    def replace_repeat(match):
        list_name = match.group(1)
        block = match.group(2).strip('\n')

        items = resolve_path(list_name, context)

        if not isinstance(items, list):
            raise ValueError(f"'{list_name}' is not a list")

        return '\n'.join(block.format(**item) for item in items)

    result = repeat_pattern.sub(replace_repeat, template)
    result = result.format(**context)
    return result