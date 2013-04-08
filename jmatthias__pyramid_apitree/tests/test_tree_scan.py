""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pytest

from pyramid_apitree import (
    scan_api_tree,
    )
from pyramid_apitree.tree_scan import ALL_REQUEST_METHODS
from pyramid_apitree.exc import BadAPITreeError

""" An example API tree.
    
    api_tree = {
        'GET': root_get,
        '/resource': {
            'GET': resource_get_all,
            'POST': resource_post,
            '.{resource_id}': {
                'GET': resource_individual_get,
                'PUT': resource_individual_update,
                'DELETE': resource_individual_delete,
                '/component': {
                    'GET': resource_individual_component_get,
                    }
                }
            }
        }
    
    """

def make_request_methods_tuple(request_method):
    """ The Pyramid 'Configurator' 'add_view' and 'add_route' methods allow the
        'request_method' to either be a string value or a tuple of string
        values. This function duplicates that behavior. """
    
    if isinstance(request_method, tuple):
        return request_method
    
    if request_method is None:
        return ALL_REQUEST_METHODS
    
    return (request_method, )

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    def __init__(self):
        self.views = {}
        self.routes = set()
    
    def add_view(
        self,
        view,
        route_name,
        **kwargs
        ):
        view_dict = kwargs
        view_dict['view_callable'] = view
        
        config_view = self.views.setdefault(route_name, dict())
        
        request_methods = make_request_methods_tuple(
            kwargs.get('request_method', None)
            )
        
        for item in request_methods:
            config_view[item] = view_dict
    
    def add_route(self, name, pattern):
        assert name == pattern
        self.routes.add(pattern)

def test_empty_api_tree():
    api_tree = {}
    
    config = MockConfigurator()
    scan_api_tree(config, api_tree)
    
    assert not config.views
    assert not config.routes

class ScanTest(unittest.TestCase):
    def target(*pargs, **kwargs):
        """ A dummy 'view_callable' object. Used as a target for tests. """
    
    def dummy(*pargs, **kwargs):
        """ Another dummy 'view_callable' object. """
    
    def endpoint_test(self, path, **expected_view_dict):
        expected_view_dict['view_callable'] = self.target
        
        request_methods = make_request_methods_tuple(
            expected_view_dict.get('request_method', None)
            )
        
        config = MockConfigurator()
        scan_api_tree(
            configurator=config,
            api_tree=self.api_tree,
            root_path='')
        
        assert path in config.routes
        assert path in config.views
        
        for item in request_methods:
            assert item in config.views[path].keys()
            
            view_dict = config.views[path][item].copy()
            
            assert view_dict == expected_view_dict

class TestRequestMethods(ScanTest):
    def request_method_test(self, request_method):
        self.api_tree = {request_method: self.target}
        # Use an empty string ('') for root.
        self.endpoint_test(path='', request_method=request_method)
    
    def test_GET_method(self):
        self.request_method_test(request_method='GET')
    
    def test_POST_method(self):
        self.request_method_test(request_method='POST')
    
    def test_PUT_method(self):
        self.request_method_test(request_method='PUT')
    
    def test_DELETE_method(self):
        self.request_method_test(request_method='DELETE')
    
    def test_HEAD_method(self):
        self.request_method_test(request_method='HEAD')
    
    def test_multiple_request_methods(self):
        self.request_method_test(request_method=('GET', 'POST'))

class TestRequestMethodsMultipleEndpoints(ScanTest):
    def test_multiple_endpoints(self):
        self.api_tree = {
            'GET': self.dummy,
            'POST': self.target,
            }
        self.endpoint_test(path='', request_method='POST')

class TestBranch(ScanTest):
    def test_branch_no_request_method(self):
        self.api_tree = {'/resource': self.target}
        self.endpoint_test('/resource')
    
    def test_branch_yes_request_method(self):
        self.api_tree = {
            '/resource': {
                'GET': self.target,
                }
            }
        self.endpoint_test('/resource', request_method='GET')
    
    def test_multiple_branches(self):
        self.api_tree = {
            '/other_resource': self.dummy,
            '/resource': self.target,
            }
        self.endpoint_test('/resource')

class TestComplexBranch(ScanTest):
    def test_branch_branch(self):
        self.api_tree = {
            '/resource': {
                '/component': self.target
                }
            }
        self.endpoint_test('/resource/component')
    
    def test_branch_branch_request_method(self):
        self.api_tree = {
            '/resource': {
                '/component': {
                    'GET': self.target
                    }
                }
            }
        self.endpoint_test('/resource/component', request_method='GET')
    
    def test_branch_multiple_branches(self):
        self.api_tree = {
            '/resource': {
                '/other_component': self.dummy,
                '/component': self.target,
                }
            }
        self.endpoint_test('/resource/component')

class TestViewKwargs(ScanTest):
    def setUp(self):
        def target(*pargs, **kwargs):
            """ A view callable with a 'view_kwargs' attribute. The API tree
                scan should automatically unpack the 'view_kwargs' when calling
                'configurator.add_view()'. """
        self.target = target
    
    def test_view_kwargs(self):
        self.target.view_kwargs = {'predicate': 'predicate value'}
        self.api_tree = {
            '': self.target,
            }
        self.endpoint_test('', **self.target.view_kwargs)
    
    def test_route_request_method_overrides_view_kwargs(self):
        """ When the API tree branch route is a request method keyword AND a
            'request_method' value is included in the 'view_kwargs' dict, the
            API tree should override 'view_kwargs'. """
        self.target.view_kwargs = {'request_method': 'POST'}
        self.api_tree = {
            'GET': self.target,
            }
        self.endpoint_test('', request_method='GET')

class TestExceptions(unittest.TestCase):
    """ Confirm that appropriate errors are raised in expected situations. """
    def setUp(self):
        def dummy(*pargs, **kwargs):
            """ A dummy view callable. """
        self.dummy = dummy
    
    def exception_test(self, api_tree):
        configurator = MockConfigurator()
        with pytest.raises(BadAPITreeError):
            scan_api_tree(configurator, api_tree)
    
    def test_request_method_route_gets_dictionary(self):
        """ When a request-method-specific-route (i.e. '/GET') is assigned a
            dictionary value in the API tree, an error should be raised.
            
            This is because it is impossible to build upon a request-method-
            specific route; the request method does not form a part of the URL.
            """
        api_tree = {
            'GET': {
                '/xxx': self.dummy
                }
            }
        self.exception_test(api_tree)
    
    def test_invalid_branch_route_object(self):
        """ A 'branch route' is something besides a string, a request method
            string, or a tuple of request methods. """
        api_tree = {object(): self.dummy}
        self.exception_test(api_tree)
    
    







