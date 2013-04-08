import json
import unittest
import pytest
from webob import Request

from iomanager import ListOf
from pyramid_apitree.api_documentation import prepare_item

def prep_json(s, n=0, **kwargs):
    kwargs.setdefault('indent', 4)
    json_s = json.dumps(s, **kwargs).replace("'", '').replace('"', '')
    return '\n'.join("    " * n + line for line in  json_s.splitlines())

@pytest.mark.a
class TestPrepareItem(unittest.TestCase):
    """ Test the function which prepares the API documentation result by
        converting class objects to name-strings. """
    @pytest.mark.b
    def test_custom_class(self):
        class CustomClass(object):
            pass
        
        assert prepare_item(CustomClass) == 'CustomClass'
    
    def test_dict_obj(self):
        expected = prep_json({'a': 'object'})
        result = prepare_item({'a': object})
        assert result == expected
    
    def test_list_obj(self):
        expected = prep_json(['object'])
        result = prepare_item([object])
        assert result == expected
    
    def test_dict_list(self):
        expected = prep_json({'a': ['object']})
        result = prepare_item({'a': [object]})
        assert result == expected
    
    def test_list_dict(self):
        expected = prep_json([{'a': 'object'}])
        result = prepare_item([{'a': object}])
        assert result == expected
    
    def test_listof_object(self):
        assert prepare_item(ListOf(object)) == 'ListOf(object)'
    
    def test_listof_list(self):
        expected = (
            'ListOf(\n' +
            prep_json(['object'], 1) + '\n'
            +')'
            )
        result = prepare_item(ListOf([object]))
        assert result == expected
    
    def test_listof_dict(self):
        expected = (
            "ListOf(\n"
            + prep_json({'a': 'object'}, 1) + '\n'
            + ')'
            )
        result = prepare_item(ListOf({'a': object}))
        assert result == expected







