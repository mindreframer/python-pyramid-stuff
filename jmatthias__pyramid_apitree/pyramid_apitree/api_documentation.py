""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """
import json
from iomanager import ListOf

INDENT_STR = '    '

class APIDocumentationView(object):
    pass

def indent(s):
    return '\n'.join([INDENT_STR + line for line in s.splitlines()])

def prepare_item(value):
    if isinstance(value, list):
        return prepare_list(value)
    if isinstance(value, dict):
        return prepare_dict(value)
    if isinstance(value, ListOf):
        return prepare_listof(value)
    
    return value.__name__

def prepare_list(value):
    start, end = '[]'
    prepared_lines = map(prepare_item, value)
    all_lines = [start] + map(indent, prepared_lines) + [end]
    
    return '\n'.join(all_lines)

def prepare_dict(value):
    start, end = '{}'
    prepared_lines = [
        "{}: {}".format(ikey, prepare_item(ivalue))
        for ikey, ivalue in value.iteritems()
        ]
    all_lines = [start] + map(indent, prepared_lines) + [end]
    
    return '\n'.join(all_lines)

def prepare_listof(value):
    start, end = 'ListOf(', ')'
    
    iospec_obj = value.iospec_obj
    if not isinstance(iospec_obj, (list, dict)):
        joiner = ''
        wrapped = prepare_item(iospec_obj)
    else:
        joiner = '\n'
        wrapped = indent(prepare_item(iospec_obj))
    
    return joiner.join([start, wrapped, end])







