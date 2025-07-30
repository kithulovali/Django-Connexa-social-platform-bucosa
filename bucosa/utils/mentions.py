# filepath: bucosa/utils/mentions.py

import re

def extract_mentions(text):
    if not text:
        return []
    return re.findall(r'@(\w+)', text)