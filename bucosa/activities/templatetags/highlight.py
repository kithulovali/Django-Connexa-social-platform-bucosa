from django import template
import re
register = template.Library()

@register.filter
def highlight(text, search):
    if not search:
        return text
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark>{m.group(0)}</mark>', str(text))
