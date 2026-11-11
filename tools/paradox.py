"""Small read-only Clausewitz data reader, not an engine or scope validator.

Keeps repeated keys and anonymous list items. No inline expansion or script execution.
"""
import re
from pathlib import Path

TOKEN = re.compile(r'\s+|\#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[=<>!]+|[^\s{}=<>!#"]+')


def parse(text):
    text = text.lstrip('\ufeff')
    tokens = []
    end = 0
    for match in TOKEN.finditer(text):
        if match.start() != end:
            raise ValueError('Invalid token or unterminated string')
        end = match.end()
        token = match.group()
        if not token.isspace() and not token.startswith('#'):
            tokens.append(token)
    if end != len(text):
        raise ValueError('Invalid trailing token')
    pos = 0

    def atom(t):
        return t[1:-1] if t.startswith('"') else t

    def block(nested=False):
        nonlocal pos
        result = []
        while pos < len(tokens):
            key = tokens[pos]; pos += 1
            if key == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                return result
            if key == '{':
                result.append((None, '=', block(True)))
            elif pos < len(tokens) and tokens[pos] in ('=', '>', '<', '>=', '<=', '!=', '=='):
                op = tokens[pos]; pos += 1
                if pos >= len(tokens):
                    raise ValueError('Missing value for ' + key)
                value = tokens[pos]; pos += 1
                result.append((atom(key), op, block(True) if value == '{' else atom(value)))
            else:
                result.append((None, '=', atom(key)))
        if nested:
            raise ValueError('Unclosed block')
        return result
    return block()


def read(path):
    return parse(Path(path).read_text(encoding='utf-8-sig'))


def values(nodes, key):
    return [v for k, op, v in nodes if k == key and op == '=']


def one(nodes, key, default=None):
    found = values(nodes, key)
    if len(found) > 1:
        raise ValueError('Repeated scalar: ' + key)
    return found[0] if found else default


def walk(nodes):
    for k, op, v in nodes:
        yield k, op, v
        if isinstance(v, list):
            yield from walk(v)
