""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from pyramid_apitree.exc import BadAPITreeError

ALL_REQUEST_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')

def get_endpoints(api_tree, root_path=''):
    """ Returns a dictionary, like this:
        {
            'complete/route': [
                {
                    'view': view_callable,
                    <More view_kwargs> ...
                    },
                <One 'view callable' dictionary for each request method.> ...
                ]
            }
        
        """
    
    endpoints = {}
    
    for ikey, ivalue in api_tree.iteritems():
        view_dict = {}
        
        if isinstance(ikey, tuple) or ikey in ALL_REQUEST_METHODS:
            route_request_method = ikey
            branch_path = ''
        else:
            route_request_method = None
            branch_path = ikey
        
        try:
            complete_route = root_path + branch_path
        except TypeError:
            raise BadAPITreeError(
                "Invalid branch route object. Must be either a string route, a "
                "string request method ('GET', 'POST', etc.), or a tuple of "
                "string request methods. Got: {}"
                .format(type(branch_path).__name__)
                )
        
        if isinstance(ivalue, dict):
            if route_request_method is not None:
                invalid_path = complete_route + '/' + str(route_request_method)
                raise BadAPITreeError(
                    "'Request method' branch routes ('GET', 'POST', etc.) "
                    "cannot have a dictionary of sub-routes. Invalid path: {}"
                    .format(invalid_path)
                    )
            
            endpoints.update(get_endpoints(ivalue, complete_route))
            continue
        
        view_callable = ivalue
        view_dict['view'] = view_callable
        
        view_kwargs = getattr(view_callable, 'view_kwargs', dict())
        view_dict.update(view_kwargs)
        
        # Request method from API tree overrides request method provided by
        # view callable 'view_kwargs'.
        if route_request_method is not None:
            view_dict['request_method'] = route_request_method
        
        view_dicts_list = endpoints.setdefault(complete_route, list())
        view_dicts_list.append(view_dict)
    
    return endpoints

def scan_api_tree(configurator, api_tree, root_path=''):
    endpoints = get_endpoints(api_tree, root_path=root_path)
    
    for complete_route, view_dicts_list in endpoints.iteritems():
        for view_dict in view_dicts_list:
            configurator.add_route(name=complete_route, pattern=complete_route)
            
            configurator.add_view(
                route_name=complete_route,
                **view_dict
                )






