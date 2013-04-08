""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """
import iomanager
from iomanager import (
    IOManager,
    VerificationFailureError,
    )

class BaseViewCallable(object):
    def __init__(self, *pargs, **kwargs):
        if pargs:
            # Decorator without keyword arguments.
            self.set_wrapped(pargs[0])
            self.setup(kwargs)
        else:
            # Decorator with keyword arguments.
            self._setup_kwargs = kwargs
    
    def __call__(self, obj):
        if not hasattr(self, 'wrapped'):
            # Decorator with keyword arguments - after '__init__'.
            self.set_wrapped(obj)
            self.setup(self.__dict__.pop('_setup_kwargs'))
            return self
        
        return self.view_call(obj)
    
    def setup(self, kwargs_dict):
        self.view_kwargs = kwargs_dict
    
    def set_wrapped(self, wrapped):
        if not callable(wrapped):
            raise TypeError('Wrapped object must be callable.')
        self.wrapped = wrapped

class SimpleViewCallable(BaseViewCallable):
    def view_call(self, request):
        return self.wrapped(request)

class FunctionViewCallable(BaseViewCallable):
    def view_call(self, request):
        self.request = request
        
        kwargs_url = dict(request.matchdict)
        kwargs_get = dict(request.GET)
        
        content_type = request.headers.get('content-type', '').lower()
        
        if content_type == 'application/json':
            kwargs_body = request.json_body
        else:
            kwargs_body = request.POST
        
        kwargs_dict = {}
        special_kwargs = self.special_kwargs(request)
        
        # Listed in reverse-priority order (last has highest priority).
        kwargs_sources = [kwargs_body, kwargs_get, kwargs_url, special_kwargs]
        
        for item in kwargs_sources:
            kwargs_dict.update(item)
        
        return self.wrapped_call(**kwargs_dict)
    
    def special_kwargs(self, request):
        return {}
    
    def wrapped_call(self, **kwargs):
        return self._call(**kwargs)
    
    def _reject_pargs(self, pargs):
        if pargs:
            raise TypeError(
                "When using the '_call' method, you must provide all arguments "
                "as keyword arguments."
            )
    
    def _call(self, *pargs, **kwargs):
        self._reject_pargs(pargs)
        
        return self.wrapped(**kwargs)

class APIViewCallable(FunctionViewCallable):
    iomanager_class = IOManager
    
    def get_items_from_dict(self, dict_obj, keys, result_keys=None):
        if result_keys is None:
            result_keys = list(keys)
        result = {}
        for ikey, result_key in zip(keys, result_keys):
            try:
                result[result_key] = dict_obj[ikey]
            except KeyError:
                continue
        return result
    
    def setup(self, kwargs_dict):
        """ Set up view callable.
            
            Access special decorator keyword arguments using
            'get_items_from_dict' method. """
        # Highest priority.
        decorator_input_kwargs = self.get_items_from_dict(
            kwargs_dict,
            ['required', 'optional', 'unlimited']
            )
        
        # Lower priority.
        callable_input_kwargs = iomanager.iospecs_from_callable(self.wrapped)
        
        input_kwargs = iomanager.combine_iospecs(
            decorator_input_kwargs,
            callable_input_kwargs,
            )
        
        output_kwargs = self.get_items_from_dict(
            kwargs_dict,
            ['returns'],
            ['required']
            )
        
        self.manager = self.iomanager_class(
            input_kwargs=input_kwargs,
            output_kwargs=output_kwargs
            )
        
        remaining_kwargs = {
            ikey: ivalue for ikey, ivalue in kwargs_dict.iteritems()
            if ikey not in ['required', 'optional', 'unlimited', 'returns']
            }
        
        super(APIViewCallable, self).setup(remaining_kwargs)
    
    def wrapped_call(self, **kwargs):
        coerced_kwargs = self.manager.coerce_input(kwargs)
        
        result =  self._call(**coerced_kwargs)
        
        return self.manager.coerce_output(result)
    
    def _call(self, *pargs, **kwargs):
        self._reject_pargs(pargs)
        
        self.manager.verify_input(iovalue=kwargs)
        
        result = self.wrapped(*pargs, **kwargs)
        
        self.manager.verify_output(iovalue=result)
        
        return result







