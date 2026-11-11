"""Dependency-free validation of the JSON Schema vocabulary used by our schema.

Not a general JSON Schema library. External consumers may use a draft 2020-12 validator.
"""
import json
import re


def validate_shape(value, spec, path='$'):
    def fail(message):raise ValueError(path+': '+message)
    if 'anyOf' in spec:
        for choice in spec['anyOf']:
            try:validate_shape(value,choice,path);break
            except ValueError:pass
        else:fail('no allowed shape matches')
    checks={'object':lambda x:type(x) is dict,'array':lambda x:type(x) is list,
            'string':lambda x:type(x) is str,'integer':lambda x:type(x) is int,
            'boolean':lambda x:type(x) is bool}
    if 'type' in spec and not checks[spec['type']](value):fail('expected '+spec['type'])
    if 'const' in spec and value != spec['const']:fail('unexpected constant')
    if 'enum' in spec and value not in spec['enum']:fail('unexpected enum value')
    if type(value) is dict:
        for key in spec.get('required',[]):
            if key not in value:fail('missing '+key)
        if len(value)<spec.get('minProperties',0):fail('too few properties')
        for key,child in value.items():
            if key in spec.get('properties',{}):
                validate_shape(child,spec['properties'][key],path+'.'+key)
            else:
                matching=[rule for pattern,rule in spec.get('patternProperties',{}).items() if re.search(pattern,key)]
                if not matching and spec.get('additionalProperties') is False:fail('unknown property '+key)
                for rule in matching:validate_shape(child,rule,path+'.'+key)
    if type(value) is list:
        if len(value)<spec.get('minItems',0) or len(value)>spec.get('maxItems',float('inf')):fail('invalid array length')
        if spec.get('uniqueItems') and len({json.dumps(x,sort_keys=True) for x in value})!=len(value):fail('duplicate array item')
        for i,child in enumerate(value):validate_shape(child,spec.get('items',{}),f'{path}[{i}]')
    if type(value) is str:
        if len(value)<spec.get('minLength',0):fail('string too short')
        if 'pattern' in spec and not re.search(spec['pattern'],value):fail('invalid identifier/format')
    if type(value) is int:
        if value<spec.get('minimum',-float('inf')) or value>spec.get('maximum',float('inf')):fail('numeric bound violated')
