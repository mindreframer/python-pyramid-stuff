""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pytest
import iomanager

from pyramid_apitree import (
    simple_view,
    function_view,
    api_view,
    )
from pyramid_apitree.view_callable import (
    BaseViewCallable,
    SimpleViewCallable,
    FunctionViewCallable,
    APIViewCallable,
    )

class Error(Exception):
    """ Base class for errors. """

class WrappedCallableSuccessError(Error):
    """ Raised to confirm that the wrapped function was actually called by a
        view callable instance.
        
        Without testing for this error, many tests could pass without the
        wrapped callable being called at all. """

class TestBaseViewCallable(unittest.TestCase):
    """ A 'BaseViewCallable' view should have a 'view_kwargs' attribute, which
        is a dictionary of any keyword arguments provided to the decorator. """
    
    def view_kwargs_test(self, view_callable, expected_view_kwargs):
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == expected_view_kwargs
    
    def test_no_kwargs(self):
        @BaseViewCallable
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {})
    
    def test_empty_kwargs(self):
        @BaseViewCallable()
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {})
    
    def test_yes_kwargs(self):
        PREDICATE_VALUE = object()
        @BaseViewCallable(predicate=PREDICATE_VALUE)
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {'predicate': PREDICATE_VALUE})
    
    def test_wrapped_not_callable_raises(self):
        """ If wrapped function is not callable, an error is raised. """
        not_callable = object()
        with pytest.raises(TypeError):
            BaseViewCallable(not_callable)

class BasicBehaviorTest(object):
    """ For all view callable classes, confirm some common behaviors. """
    
    def test_decorator_accepts_keyword_arguments(self):
        expected_view_kwargs = {'predicate': 'xxx'}
        view_kwargs = expected_view_kwargs.copy()
        
        @self.view_decorator(predicate='xxx')
        def view_callable(**kwargs):
            pass
        
        assert view_callable.view_kwargs == expected_view_kwargs
    
    def test_return_value_unchanged(self):
        """ Return value should be returned unchanged. """
        expected = object()
        @self.view_decorator
        def view_callable(*pargs, **kwargs):
            return expected
        
        result = view_callable(MockPyramidRequest())
        
        assert result is expected

class TestSimpleViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = simple_view

class TestSimpleViewCallable(unittest.TestCase):
    """ A 'simple_view' view callable should have a 'view_kwargs' attribute,
        which is a dictionary of any keyword arguments provided to the
        decorator. """
    REQUEST_OBJ = object()
    
    def test_subclass_of_BaseViewCallable(self):
        """ Confirm that 'simple_view' is a subclass of BaseViewCallable. """
        assert issubclass(simple_view, BaseViewCallable)
    
    def test_instance_of_BaseViewCallable(self):
        """ Confirm that 'simple_view' returns an instance of
            BaseViewCallable. """
        @simple_view
        def view_callable(request):
            pass
        
        assert isinstance(view_callable, BaseViewCallable)
    
    def test_no_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        @simple_view
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        view_callable(self.REQUEST_OBJ)
    
    def test_yes_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        @simple_view(predicate=object())
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        view_callable(self.REQUEST_OBJ)

class MockPyramidRequest(object):
    """ A mock 'pyramid.request.Request' object. """
    def __init__(
        self,
        headers={},
        GET={},
        POST={},
        matchdict={},
        json_body={}
        ):
        self.headers = headers.copy()
        self.headers.setdefault('content-type', 'xxx')
        
        self.GET = GET.copy()
        self.POST = POST.copy()
        self.matchdict = matchdict.copy()
        
        if isinstance(json_body, dict):
            self.json_body = json_body.copy()
        else:
            self.json_body = json_body

class TestFunctionViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = function_view

class TestFunctionViewCallable(unittest.TestCase):
    """ A 'function_view' view callable gets function keyword arguments from the
        'request' object. """
    
    def test_subclass_of_BaseViewCallable(self):
        assert issubclass(function_view, BaseViewCallable)
    
    def test_instance_of_BaseViewCallable(self):
        @function_view
        def view_callable(**kwargs):
            pass
        
        assert isinstance(view_callable, BaseViewCallable)

class TestFunctionViewCallableKwargsSources(unittest.TestCase):
    def request_method_test(
        self,
        request_method,
        expected_kwargs=None,
        **kwargs
        ):
        method_kwargs = {'a': 1}
        if expected_kwargs is None:
            expected_kwargs = method_kwargs.copy()
        
        @function_view
        def view_callable(**kwargs):
            assert kwargs == expected_kwargs
            raise WrappedCallableSuccessError
        
        request_kwargs = kwargs
        request_kwargs.update({request_method: method_kwargs})
        
        request = MockPyramidRequest(**request_kwargs)
        
        with pytest.raises(WrappedCallableSuccessError):
            view_callable(request)
    
    def test_URL_kwargs(self):
        """ Keyword arguments from the URL (not from the URL query string) are
            passed through the 'matchdict' attribute of the 'request' object.
            """
        self.request_method_test('matchdict')
    
    def test_GET_kwargs(self):
        self.request_method_test('GET')
    
    def test_POST_kwargs(self):
        self.request_method_test('POST')
    
    def test_json_kwargs(self):
        """ Keyword arguments from JSON are passed through the 'json_body'
            request attribute. 'content-type' MUST be 'application/json'. """
        self.request_method_test(
            'json_body',
            headers={'content-type': 'application/json'},
            )
    
    def test_json_kwargs_wrong_content_type(self):
        """ When a request is made with an incorrect content-type (not
            'application/json'), the JSON-encoded request body will be ignored.
            """
        self.request_method_test(
            'json_body',
            headers={'content-type': 'xxx'},
            expected_kwargs={}
            )
    
    def test_special_kwargs(self):
        """ The 'special_kwargs' method injects keyword arguments before calling
            the wrapped callable. """
        expected_kwargs = {'a': object()}
        method_kwargs = expected_kwargs.copy()
        
        class SpecialKwargsFunctionViewCallable(FunctionViewCallable):
            def special_kwargs(self, request):
                return method_kwargs
        
        @SpecialKwargsFunctionViewCallable
        def view_callable(**kwargs):
            assert kwargs == expected_kwargs
            raise WrappedCallableSuccessError
        
        request = MockPyramidRequest()
        with pytest.raises(WrappedCallableSuccessError):
            view_callable(request)

class TestFunctionViewCallableKwargsSourcesPrecedence(unittest.TestCase):
    def make_request(self, *request_methods):
        request_kwargs = {item: {'a': object()} for item in request_methods}
        
        if 'json_body' in request_kwargs:
            request_kwargs['headers'] = {'content_type': 'application/json'}
        
        return MockPyramidRequest(**request_kwargs)
    
    def override_test(self, *request_methods):
        request = self.make_request(*request_methods)
        
        # First-listed request method is expected to override the others.
        expected_value = getattr(request, request_methods[0])['a']
        
        @function_view
        def view_callable(a):
            assert a == expected_value
            raise WrappedCallableSuccessError
        
        with pytest.raises(WrappedCallableSuccessError):
            view_callable(request)
    
    def test_URL_overrides_GET(self):
        self.override_test('matchdict', 'GET')
    
    def test_URL_overrides_POST(self):
        self.override_test('matchdict', 'POST')
    
    def test_URL_overrides_JSON(self):
        self.override_test('matchdict', 'json_body')
    
    def test_GET_overrides_POST(self):
        self.override_test('GET', 'POST')
    
    def test_GET_overrides_JSON(self):
        self.override_test('GET', 'json_body')
    
    def test_URL_overrides_GET_and_POST(self):
        self.override_test('matchdict', 'GET', 'POST')
    
    def test_URL_overrides_GET_and_JSON(self):
        self.override_test('matchdict', 'GET', 'json_body')
    
    def special_kwargs_overrides_all_others_test(self, request_body_source):
        """ Keyword arguments from the 'special_kwargs' method override all
            other kwarg sources. """
        expected_value = object()
        
        class SpecialKwargsFunctionViewCallable(FunctionViewCallable):
            def special_kwargs(self, request):
                return {'a': expected_value}
        
        request = self.make_request('matchdict', 'GET', request_body_source)
        
        @SpecialKwargsFunctionViewCallable
        def view_callable(a):
            assert a == expected_value
            raise WrappedCallableSuccessError
        
        with pytest.raises(WrappedCallableSuccessError):
            view_callable(request)
    
    def test_special_kwargs_overrides_all_with_json_body(self):
        self.special_kwargs_overrides_all_others_test('json_body')
    
    def test_special_kwargs_overrides_all_with_POST(self):
        self.special_kwargs_overrides_all_others_test('POST')

class TestFunctionViewCallableDirectCall(unittest.TestCase):
    """ FunctionViewCallable provides a '_call' method to call the wrapped
        callable directly. This is mostly used for testing. """
    
    def make_view_callable(self):
        @function_view
        def view_callable(a=1):
            raise WrappedCallableSuccessError
        return view_callable
    
    def test_call_unknown_kwargs_raises(self):
        """ Calling a FunctionViewCallable with a keyword argument other than
            'request' fails. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable(a=1)
    
    def test_call_direct_passes(self):
        """ Calling the '_call' method with a known keyword argument passes. """
        view_callable = self.make_view_callable()
        with pytest.raises(WrappedCallableSuccessError):
            view_callable._call(a=1)
    
    def test_call_direct_unknown_kwarg_raises(self):
        """ Calling the '_call' method with an unknown keyword argument
            fails. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable._call(b=2)
    
    def test_call_direct_positional_args_raises(self):
        """ Calling the '_call' method with positional arguments raises an
            error. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable._call(1)

class TestAPIViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = api_view
    
    def test_iomanager_kwargs_collected(self):
        """ Confirm that the special keyword arguments for verification and
            coercion (using 'iomanager') are not included in the 'view_kwargs'
            dictionary. """
        iomanager_kwargs = dict(
            required=object(),
            optional=object(),
            unlimited=object(),
            returns=object(),
            )
        view_kwargs = dict(
            predicate=object()
            )
        decorator_kwargs = iomanager_kwargs.copy()
        decorator_kwargs.update(view_kwargs)
        
        @api_view(**decorator_kwargs)
        def view_callable():
            pass
        
        assert view_callable.view_kwargs == view_kwargs



# ----------------- APIViewCallable verification tests -----------------

class ViewCallableCallTest(object):
    def view_callable_call(self, view_callable, **kwargs):
        method = getattr(view_callable, self.method_name)
        method(**kwargs)

class APIViewCallableVerifyStructureInputTest(ViewCallableCallTest):
    """ Confirm that input structure is checked with 'IOManager.verify'.
        
        Confirm that keyword arguments for 'IOManager.verify' can be passed
        through the decorator.
        
        Extra parameters in the function definition are included in 'verify'
        combined iospec.
        
        Confirm that the 'unlimited' decorator argument behaves in the expected
        way. """
    
    def call_passes_test(self, view_callable, **kwargs):
        with pytest.raises(WrappedCallableSuccessError):
            self.view_callable_call(view_callable, **kwargs)
    
    def call_raises_error_test(self, view_callable, error_class, **kwargs):
        with pytest.raises(error_class):
            self.view_callable_call(view_callable, **kwargs)
    
    def call_raises_test(self, view_callable, **kwargs):
        """ An error is raised by 'IOManager.verify()'. """
        self.call_raises_error_test(
            view_callable,
            iomanager.VerificationFailureError,
            **kwargs
            )
    
    def mismatch_raises_test(self, **kwargs):
        """ A TypeError is raised when the wrapped callable is called. This
            happens when the 'verify' arguments (iospecs) allow arguments
            through which are not allowed by the wrapped callable's parameter
            definition. """
        @api_view(**kwargs)
        def view_callable():
            pass
        
        self.call_raises_error_test(
            view_callable,
            TypeError,
            a=None
            )
    
    def test_no_kwargs_passes(self):
        @api_view
        def view_callable():
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_unknown_kwarg_raises(self):
        @api_view
        def view_callable():
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_definition_required_present_passes(self):
        @api_view
        def view_callable(a):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_definition_required_missing_raises(self):
        @api_view
        def view_callable(a):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_definition_optional_present_passes(self):
        @api_view
        def view_callable(a=None):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_definition_optional_missing_passes(self):
        @api_view
        def view_callable(a=None):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_definition_kwargs_not_unlimited(self):
        """ When the view callable definition specifies a '**kwargs' parameter
            and the 'unlimited' directive is not used, unknown keyword arguments
            fail. """
        @api_view
        def view_callable(**kwargs):
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_decorator_mismatch_required_raises(self):
        self.mismatch_raises_test(required={'a': object})
    
    def test_decorator_mismatch_optional_raises(self):
        self.mismatch_raises_test(optional={'a': object})
    
    def test_decorator_mismatch_unlimited_raises(self):
        self.mismatch_raises_test(unlimited=True)
    
    def test_decorator_required_present_passes(self):
        @api_view(required={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_required_missing_raises(self):
        @api_view(required={'a': object})
        def view_callable(**kwargs):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_decorator_optional_present_passes(self):
        @api_view(optional={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_optional_missing_passes(self):
        @api_view(optional={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_decorator_required_overrides_definition_optional(self):
        @api_view(required={'a': object})
        def view_callable(a=None):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_decorator_required_compliments_definition_required(self):
        @api_view(required={'b': object})
        def view_callable(a, **kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None, b=None)
    
    def test_decorator_optional_compliments_definition_optional(self):
        @api_view(optional={'b': object})
        def view_callable(a=None, **kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None, b=None)
    
    def test_decorator_unlimited_passes_with_definition_kwargs(self):
        """ When 'unlimited=True' AND the view callable definition specifies a
            '**kwargs' parameter, unknown keyword arguments pass. """
        @api_view(unlimited=True)
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_mismatch_unlimited_raises_without_definition_kwargs(
        self
        ):
        """ When 'unlimited=True' but the view callable definition does not
            specify a '**kwargs' parameter, unknown keyword argumets fail. """
        @api_view(unlimited=True)
        def view_callable():
            pass
        
        self.call_raises_error_test(view_callable, TypeError, a=None)
    
    def test_decorator_optional_definition_required_no_type_checking(self):
        """ When a parameter is 'required' in the callable definition, but
            'optional' in the decorator arguments, the callable definition
            takes priority. Be careful! This means that type checking and
            coercion will not apply to arguments that have been mismatched.
            
            You should probably add additional tests to confirm all of the
            mismatch behaviors. """
        @api_view(optional={'a': CustomType})
        def view_callable(a):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=object())

class TestAPIViewCallableVerifyStructureInput_call(
    APIViewCallableVerifyStructureInputTest,
    unittest.TestCase,
    ):
    method_name = '_call'

class TestAPIViewCallableVerifyStructureInput_wrapped_call(
    APIViewCallableVerifyStructureInputTest,
    unittest.TestCase,
    ):
    method_name = 'wrapped_call'

class APIViewCallableVerifyStructureOutputTest(ViewCallableCallTest):
    """ Confirm that output structure is checked with 'IOManager.verify'.
        
        All 'output' values are considered to be 'required': output checking is
        strict. """
    
    def return_test(self, expected_return, return_value):
        """ The wrapped view callable returns a non-container value. """
        @api_view(returns=expected_return)
        def view_callable():
            return return_value
        
        self.view_callable_call(view_callable)
    
    def test_no_returns_argument_passes(self):
        """ Don't use 'return_test' for this test. It is necessary to
            test the situation when no 'returns' argument is given. """
        @api_view
        def view_callable():
            return object()
        
        self.view_callable_call(view_callable)
    
    def test_returns_object_passes(self):
        self.return_test(object, object())
    
    def container_test(self, return_value):
        """ Test behavior when expected return value is a container-type. For
            this test, a 'dict' value is used as a representative container-type
            expected return. This test relies upon 'iomanager' to treat all
            container types the same way. """
        self.return_test({'a': object}, return_value)
    
    def container_raises_test(self, return_value):
        with pytest.raises(iomanager.VerificationFailureError):
            self.container_test(return_value)
    
    def test_dict_expected_passes(self):
        self.container_test({'a': object()})
    
    def test_dict_missing_raises(self):
        self.container_raises_test({})
    
    def test_dict_extra_raises(self):
        self.container_raises_test({'a': object(), 'b': object()})

class TestAPIViewCallableVerifyStructureOutput_call(
    APIViewCallableVerifyStructureOutputTest,
    unittest.TestCase,
    ):
    method_name = '_call'

class TestAPIViewCallableVerifyStructureOutput_wrapped_call(
    APIViewCallableVerifyStructureOutputTest,
    unittest.TestCase,
    ):
    method_name = 'wrapped_call'

class CustomType(object):
    """ A custom type used to confirm type-checking. """

class APIViewCallableVerifyTypecheckInputTest(ViewCallableCallTest):
    def typecheck_test(self, parameter_name, input_value):
        @api_view(**{parameter_name: {'a': CustomType}})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.view_callable_call(view_callable, a=input_value)
    
    def typecheck_passes_test(self, parameter_name):
        with pytest.raises(WrappedCallableSuccessError):
            self.typecheck_test(parameter_name, CustomType())
    
    def typecheck_raises_test(self, parameter_name):
        with pytest.raises(iomanager.VerificationFailureError):
            self.typecheck_test(parameter_name, object())
    
    def test_typecheck_passes_required(self):
        self.typecheck_passes_test('required')
    
    def test_typecheck_passes_optional(self):
        self.typecheck_passes_test('optional')
    
    def test_typecheck_raises_required(self):
        self.typecheck_raises_test('required')
    
    def test_typecheck_raises_optional(self):
        self.typecheck_raises_test('optional')

class TestAPIViewCallableVerifyTypecheckInput_call(
    APIViewCallableVerifyTypecheckInputTest,
    unittest.TestCase,
    ):
    method_name = '_call'

class TestAPIViewCallableVerifyTypecheckInput_wrapped_call(
    APIViewCallableVerifyTypecheckInputTest,
    unittest.TestCase,
    ):
    method_name = 'wrapped_call'

class APIViewCallableVerifyTypecheckOutputTest(ViewCallableCallTest):
    def typecheck_test(self, output_value):
        @api_view(returns=CustomType)
        def view_callable():
            return output_value
        
        view_callable._call()
    
    def test_typecheck_passes(self):
        self.typecheck_test(CustomType())
    
    def test_typecheck_raises(self):
        with pytest.raises(iomanager.VerificationFailureError):
            self.typecheck_test(object())

class TestAPIViewCallableVerifyTypecheckOutput_call(
    APIViewCallableVerifyTypecheckOutputTest,
    unittest.TestCase,
    ):
    method_name = '_call'

class TestAPIViewCallableVerifyTypecheckOutput_wrapped_call(
    APIViewCallableVerifyTypecheckOutputTest,
    unittest.TestCase,
    ):
    method_name = 'wrapped_call'



# --------------- APIViewCallable custom IOManager tests ---------------

class CustomTypecheckType(object):
    pass

class TypeCheckConfirmationError(Error):
    """ A custom error to confirm that the custom IOManager is being used. """

class CustomVerificationIOManager(iomanager.IOManager):
    def typecheck_custom(value, expected_type):
        raise TypeCheckConfirmationError
    
    input_kwargs = {
        'typecheck_functions': {CustomTypecheckType: typecheck_custom}
        }

class TestAPIViewCallableCustomIOManager(unittest.TestCase):
    """ The 'iomanager_class' class attribute can be used to assign a custom
        IOManager subclass to a view callable class. """
    
    class CustomAPIViewCallable(APIViewCallable):
        iomanager_class = CustomVerificationIOManager
    
    def test_custom_iomanager_class(self):
        @self.CustomAPIViewCallable(
            required={'a': CustomTypecheckType}
            )
        def view_callable(**kwargs):
            pass
        
        with pytest.raises(TypeCheckConfirmationError):
            view_callable._call(a=object())



# ------------------- APIViewCallable coercion tests -------------------

class CustomInputType(object):
    """ A custom type for testing coercion. """

class CustomCoercedType(object):
    """ A custom type for testingcoercion. """

class CustomOutputType(object):
    """ A custom type for testing output coercion. """

def coerce_custom_input(value, expected_type):
    if isinstance(value, CustomInputType):
        return CustomCoercedType()
    return value

def coerce_custom_output(value, expected_type):
    if isinstance(value, CustomCoercedType):
        return CustomOutputType()
    return value

class CustomCoercionIOManager(iomanager.IOManager):
    input_kwargs = {
        'coercion_functions': {CustomCoercedType: coerce_custom_input}
        }
    output_kwargs = {
        'coercion_functions': {CustomCoercedType: coerce_custom_output}
        }

class TestAPIViewCallableCoercion(unittest.TestCase):
    """ Input and output values go through coercion. """
        
    class CustomAPIViewCallable(APIViewCallable):
        """ A view callable that coerces input and output value types. """
        iomanager_class = CustomCoercionIOManager
    
    def test_input_coercion(self):
        """ 'wrapped_call' coerces input. """
        @self.CustomAPIViewCallable(
            required={'a': CustomCoercedType}
            )
        def view_callable(a):
            assert isinstance(a, CustomCoercedType)
            raise WrappedCallableSuccessError
        
        with pytest.raises(WrappedCallableSuccessError):
            view_callable.wrapped_call(a=CustomInputType())
    
    def test_output_coercion(self):
        """ 'wrapped_call' coerces output. """
        @self.CustomAPIViewCallable(
            returns=CustomCoercedType
            )
        def view_callable():
            return CustomCoercedType()
        
        result = view_callable.wrapped_call()
        assert isinstance(result, CustomOutputType)







