import mock
from pyramid import testing
import karl.testing

try:
    import unittest2 as unittest
    unittest # stfu pyflakes
except ImportError:
    import unittest


class TestACLPathCache(unittest.TestCase):

    def _getTargetClass(self):
        from karl.security.cache import ACLPathCache
        return ACLPathCache

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeACE(self, allow=True, principal='phreddy', permission='testing'):
        from pyramid.security import Allow
        from pyramid.security import Deny
        action = allow and Allow or Deny
        return (action, principal, permission)

    def _makeModel(self, name=None, parent=None, principals=('phreddy',)):
        from pyramid.testing import DummyModel
        model = DummyModel()
        if parent is not None:
            parent[name] = model
        if principals:
            model.__acl__ = [self._makeACE(principal=x) for x in principals]
        return model

    def test_class_conforms_to_IACLPathCache(self):
        from zope.interface.verify import verifyClass
        from karl.security.cache import IACLPathCache
        verifyClass(IACLPathCache, self._getTargetClass())

    def test_instance_conforms_to_IACLPathCache(self):
        from zope.interface.verify import verifyObject
        from karl.security.cache import IACLPathCache
        verifyObject(IACLPathCache, self._makeOne())

    def test_ctor(self):
        cache = self._makeOne()
        self.assertEqual(len(cache._index), 0)

    def test_clear_default(self):
        cache = self._makeOne()
        root = self._makeModel()
        cache.index(root)
        self.assertEqual(len(cache._index), 1)
        cache.clear()
        self.assertEqual(len(cache._index), 0)

    def test_clear_nondefault(self):
        cache = self._makeOne()
        root = self._makeModel()
        cache.index(root)
        child = self._makeModel(name='child', parent=root, principals=('bob',))
        cache.index(child)
        self.assertEqual(len(cache._index), 2)
        cache.clear(child)
        self.assertEqual(len(cache._index), 1)
        self.assertEqual(cache._index.keys()[0], ())

    def test_clear_intermediate(self):
        cache = self._makeOne()
        root = self._makeModel()
        cache.index(root)
        child = self._makeModel('child', root, principals=('bob',))
        cache.index(child)
        grand = self._makeModel('grand', child, principals=('alice',))
        cache.index(grand)
        self.assertEqual(len(cache._index), 3)
        cache.clear(child)
        self.assertEqual(len(cache._index), 1)
        self.assertEqual(cache._index.keys()[0], ())

    def test_index_no_acl(self):
        cache = self._makeOne()
        root = self._makeModel()
        cache.index(root)
        child = self._makeModel('child', root, principals=())
        cache.index(child)
        self.assertEqual(len(cache._index), 1)
        self.assertEqual(cache._index.keys()[0], ())

    def test_lookup_root_uncached_no_acl_no_permission(self):
        cache = self._makeOne()
        root = self._makeModel(principals=())

        aces = cache.lookup(root)
        self.assertEqual(len(aces), 0)
        self.assertEqual(len(cache._index), 0)

    def test_lookup_root_uncached_w_acl_no_permission(self):
        from pyramid.security import Allow
        cache = self._makeOne()
        root = self._makeModel()

        aces = cache.lookup(root)
        self.assertEqual(len(aces), 1)
        self.assertEqual(aces[0], (Allow, 'phreddy', 'testing'))
        self.assertEqual(len(cache._index), 1)

    def test_lookup_root_cached_w_acl_no_permission(self):
        from pyramid.security import Allow
        cache = self._makeOne()
        root = self._makeModel()
        cache.index(root)
        root.__acl__.append(self._makeACE(principal='bob'))  # uncached

        aces = cache.lookup(root)
        self.assertEqual(len(aces), 1, aces)
        self.assertEqual(aces[0], (Allow, 'phreddy', 'testing'))
        self.assertEqual(len(cache._index), 1)

    def test_lookup_nonroot(self):
        from pyramid.security import Allow
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=('bob',))
        grand = self._makeModel('grand', child, principals=('alice',))

        aces = cache.lookup(grand)
        self.assertEqual(len(aces), 3)
        self.assertEqual(aces[0], (Allow, 'alice', 'testing'))
        self.assertEqual(aces[1], (Allow, 'bob', 'testing'))
        self.assertEqual(aces[2], (Allow, 'phreddy', 'testing'))
        self.assertEqual(len(cache._index), 3)

    def test_lookup_nonroot_w_permission(self):
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=('bob',))
        grand = self._makeModel('grand', child, principals=('alice',))

        aces = cache.lookup(grand, 'view')
        self.assertEqual(len(aces), 0)
        self.assertEqual(len(cache._index), 3)

    def test_lookup_nonroot_sparse(self):
        from pyramid.security import Allow
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=('bob',))
        grand = self._makeModel('grand', child, principals=())

        aces = cache.lookup(grand)
        self.assertEqual(len(aces), 2)
        self.assertEqual(aces[0], (Allow, 'bob', 'testing'))
        self.assertEqual(aces[1], (Allow, 'phreddy', 'testing'))
        self.assertEqual(len(cache._index), 2)

    def test_lookup_nonroot_sparse_w_permission(self):
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=('bob',))
        grand = self._makeModel('grand', child, principals=())

        aces = cache.lookup(grand, 'view')
        self.assertEqual(len(aces), 0)
        self.assertEqual(len(cache._index), 2)

    def test_lookup_nonroot_sparse_w_permission_w_all(self):
        from pyramid.security import Allow
        from karl.security.policy import ALL
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=('bob',))
        grand = self._makeModel('grand', child, principals=())
        grand.__acl__ = [self._makeACE(True, 'alice', ALL)]

        aces = cache.lookup(grand, 'view')
        self.assertEqual(len(aces), 1)
        self.assertEqual(aces[0], (Allow, 'alice', ALL))
        self.assertEqual(len(cache._index), 3)

    def test_lookup_nonroot_sparse_w_allow_everyone(self):
        from pyramid.security import Allow
        from pyramid.security import Everyone
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=())
        child.__acl__ = [self._makeACE(True, Everyone)]
        grand = self._makeModel('grand', child, principals=('alice',))

        aces = cache.lookup(grand)
        self.assertEqual(len(aces), 2)
        self.assertEqual(aces[0], (Allow, 'alice', 'testing'))
        self.assertEqual(aces[1], (Allow, Everyone, 'testing'))
        self.assertEqual(len(cache._index), 2)

    def test_lookup_nonroot_sparse_w_deny_everyone(self):
        from pyramid.security import Allow
        from pyramid.security import Deny
        from pyramid.security import Everyone
        cache = self._makeOne()
        root = self._makeModel()
        child = self._makeModel('child', root, principals=())
        child.__acl__ = [self._makeACE(True, 'bob'),
                         self._makeACE(False, Everyone)]
        grand = self._makeModel('grand', child, principals=('alice',))

        aces = cache.lookup(grand)
        self.assertEqual(len(aces), 3)
        self.assertEqual(aces[0], (Allow, 'alice', 'testing'))
        self.assertEqual(aces[1], (Allow, 'bob', 'testing'))
        self.assertEqual(aces[2], (Deny, Everyone, 'testing'))
        self.assertEqual(len(cache._index), 2)

class TestACLChecker(unittest.TestCase):
    def _getTargetClass(self):
        from karl.security.policy import ACLChecker
        return ACLChecker

    def _makeOne(self, principals, permission):
        return self._getTargetClass()(principals, permission)

    def test_it(self):
        from pyramid.security import Allow, Deny, Everyone
        from karl.security.policy import ALL
        acl_one = ((Allow, 'a', 'view'), (Allow, 'b', 'view'))
        acl_two = ((Allow, 'c', 'view'), (Allow, 'd', 'view'),)
        acl_three = ((Allow, 'd', ALL), (Allow, 'e', 'view'),
                     (Deny, Everyone, ALL),)
        from BTrees.IFBTree import IFSet
        data = []
        data.append([(0, [acl_one],), IFSet([0])])
        data.append([(1, [acl_one, acl_two]), IFSet([1,2,3])])
        data.append([(2, [acl_one, acl_two, acl_three]), IFSet([4,5,6])])
        data.append([(3, [acl_one]), IFSet()])

        checker = self._makeOne(('a', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [0, 1, 2, 3])

        checker = self._makeOne(('b', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [0, 1, 2, 3])

        checker = self._makeOne(('c', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [1, 2, 3])

        checker = self._makeOne(('d', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [1, 2, 3, 4, 5, 6])

        checker = self._makeOne(('e', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [4,5,6])

        checker = self._makeOne(('nobody', Everyone), 'view')
        result = checker(data)
        self.assertEqual(list(result), [])

class TestSecuredStateMachine(unittest.TestCase):
    def _getTargetClass(self):
        from karl.security.workflow import SecuredStateMachine
        return SecuredStateMachine

    def _makeOne(self, state_attr, states=None, initial_state=None):
        return self._getTargetClass()(state_attr, states, initial_state)

    def test_add_with_permission(self):
        machine = self._makeOne('state')
        machine.add('private', 'publish', 'public', None, permission='add')
        self.assertEqual(
            machine.states,
            {('private', 'publish'): ('public', None, {'permission': 'add'})}
            )

    def test_add_without_permission(self):
        machine = self._makeOne('state')
        machine.add('private', 'publish', 'public', None)
        self.assertEqual(
            machine.states,
            {('private', 'publish'): ('public', None, {'permission': None})}
            )

    def test_secured_transition_info_permissive(self):
        machine = self._makeOne('state')
        machine.add('private', 'publish', 'public', None)
        machine.add('private', 'reject', 'rejected', None, permission='add')
        karl.testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        context = testing.DummyModel()
        transitions = sorted(
            machine.secured_transition_info(context, request,
                                            'private'))
        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0]['permission'], None)
        self.assertEqual(transitions[1]['permission'], 'add')

    def test_secured_transition_info_not_permissive(self):
        machine = self._makeOne('state')
        machine.add('private', 'publish', 'public', None)
        machine.add('private', 'reject', 'rejected', None)
        karl.testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        context = testing.DummyModel()
        transitions = machine.secured_transition_info(context, request,
                                                      'private')
        self.assertEqual(len(transitions), 0)

    def test_secured_execute_permitted(self):
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        states = {('pending', 'publish'): ('published', dummy,
                                           {'permission':'add'}),
                  ('pending', 'reject'): ('private', dummy,
                                          {'permission':'add'}),
                  ('published', 'retract'): ('pending', dummy,
                                             {'permission':'add'}),
                  ('private', 'submit'): ('pending', dummy,
                                          {'permission':'add'}),
                  ('pending', None): ('published', dummy,
                                      {'permission':'add'}),}
        sm = self._makeOne('state', states=states, initial_state='pending')
        karl.testing.registerDummySecurityPolicy(permissive=True)
        request = testing.DummyRequest()
        ob = testing.DummyModel()
        sm.secured_execute(ob, request, 'publish')
        self.assertEqual(ob.state, 'published')
        sm.secured_execute(ob, request, 'retract')
        self.assertEqual(ob.state, 'pending')
        sm.secured_execute(ob, request, 'reject')
        self.assertEqual(ob.state, 'private')
        sm.secured_execute(ob, request, 'submit')
        self.assertEqual(ob.state, 'pending')
        # catch-all
        sm.secured_execute(ob, request, None)
        self.assertEqual(ob.state, 'published')
        self.assertEqual(len(args), 5)
        self.assertEqual(args[0], ('pending', 'published', 'publish', ob,
                                   {'permission':'add'}))
        self.assertEqual(args[1], ('published', 'pending', 'retract', ob,
                                   {'permission':'add'}))
        self.assertEqual(args[2], ('pending', 'private', 'reject', ob,
                                   {'permission':'add'}))
        self.assertEqual(args[3], ('private', 'pending', 'submit', ob,
                                   {'permission':'add'}))
        self.assertEqual(args[4], ('pending', 'published', None, ob,
                                   {'permission':'add'}))
        from repoze.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.secured_execute, ob, request,
                          'nosuch')

    def test_secured_execute_not_permitted(self):
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        states = {('pending', 'publish'): ('published', dummy,
                                           {'permission':'add'}),}

        sm = self._makeOne('state', states=states, initial_state='pending')
        karl.testing.registerDummySecurityPolicy(permissive=False)
        request = testing.DummyRequest()
        ob = testing.DummyModel()
        from repoze.workflow.statemachine import StateMachineError
        self.assertRaises(StateMachineError, sm.secured_execute,
                          ob, request, 'publish')

    def test_secured_execute_request_is_None(self):
        args = []
        def dummy(state, newstate, transition_id, context, **kw):
            args.append((state, newstate, transition_id, context, kw))
        states = {('pending', 'publish'): ('published', dummy,
                                           {'permission':'add'}),}

        sm = self._makeOne('state', states=states, initial_state='pending')
        karl.testing.registerDummySecurityPolicy(permissive=False)
        ob = testing.DummyModel()
        sm.secured_execute(ob, None, 'publish')
        self.assertEqual(ob.state, 'published')

class TestPostorder(unittest.TestCase):
    def _callFUT(self, node):
        from karl.security.workflow import postorder
        return postorder(node)

    def test_None_node(self):
        result = list(self._callFUT(None))
        self.assertEqual(result, [None])

    def test_IFolder_node_no_children(self):
        from repoze.folder.interfaces import IFolder
        from zope.interface import directlyProvides
        model = testing.DummyModel()
        directlyProvides(model, IFolder)
        result = list(self._callFUT(model))
        self.assertEqual(result, [model])

    def test_IFolder_node_nonfolder_children(self):
        from repoze.folder.interfaces import IFolder
        from zope.interface import directlyProvides
        model = testing.DummyModel()
        one = testing.DummyModel()
        two = testing.DummyModel()
        model['one'] = one
        model['two'] = two
        directlyProvides(model, IFolder)
        result = list(self._callFUT(model))
        self.assertEqual(result, [two, one, model])

    def test_IFolder_node_folder_children(self):
        from repoze.folder.interfaces import IFolder
        from zope.interface import directlyProvides
        L = [] # "deactivated" list
        model = testing.DummyModel(_p_deactivate=lambda *x: L.append('model'))
        one = testing.DummyModel(_p_deactivate=lambda *x: L.append('one'))
        two = testing.DummyModel(_p_deactivate=lambda *x: L.append('two'))
        self.assertEqual(L, [])
        directlyProvides(two, IFolder)
        model['one'] = one
        model['two'] = two
        three = testing.DummyModel(_p_deactivate=lambda *x: L.append('three'))
        four = testing.DummyModel()
        two['three'] = three
        two['four'] = four
        directlyProvides(model, IFolder)
        result = list(self._callFUT(model))
        self.assertEqual(result, [four, three, two, one, model])
        self.assertEqual(L, ['three', 'two', 'one', 'model'])

class TestResetSecurityWorkflow(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, root):
        L = []
        output = L.append
        from karl.security.workflow import reset_security_workflow
        reset_security_workflow(root, output)
        return L

    def test_donothing(self):
        root = testing.DummyModel()
        L = self._callFUT(root)
        self.assertEqual(L, ['updated 0 content objects'])

    def test_object_is_reset(self):
        from repoze.lemonade.testing import registerContentFactory
        from repoze.workflow.testing import registerDummyWorkflow
        from repoze.lemonade.interfaces import IContent
        workflow = registerDummyWorkflow('security')
        from zope.interface import directlyProvides
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        registerContentFactory(testing.DummyModel, IFoo)
        root = testing.DummyModel()
        directlyProvides(root, (IContent, IFoo))
        root.state = 'state'
        L = self._callFUT(root)
        self.assertEqual(workflow.resetted, [root])
        self.assertEqual(L, ['updated 1 content objects'])

    def test_object_with_custom_acl_matches_object_acl(self):
        from repoze.lemonade.testing import registerContentFactory
        from repoze.workflow.testing import registerDummyWorkflow
        from repoze.lemonade.interfaces import IContent
        workflow = registerDummyWorkflow('security')
        from zope.interface import directlyProvides
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        registerContentFactory(testing.DummyModel, IFoo)
        root = testing.DummyModel()
        root.state = 'state'
        acl = []
        root.__acl__ = acl
        root.__custom_acl__ = acl
        directlyProvides(root, (IContent, IFoo))
        L = self._callFUT(root)
        self.assertEqual(workflow.resetted, [])
        self.assertEqual(L, ['updated 0 content objects'])

    def test_object_with_custom_acl_different_than_object_acl(self):
        from repoze.lemonade.testing import registerContentFactory
        from repoze.workflow.testing import registerDummyWorkflow
        from repoze.lemonade.interfaces import IContent
        workflow = registerDummyWorkflow('security')
        from zope.interface import directlyProvides
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        registerContentFactory(testing.DummyModel, IFoo)
        root = testing.DummyModel()
        root.state = 'state'
        root.__acl__ = ['123']
        root.__custom_acl__ = []
        directlyProvides(root, (IContent, IFoo))
        L = self._callFUT(root)
        self.assertEqual(workflow.resetted, [root])
        self.assertEqual(L, ['updated 1 content objects'])

class Test_has_custom_acl(unittest.TestCase):
    def _callFUT(self, ob):
        from karl.security.workflow import has_custom_acl
        return has_custom_acl(ob)

    def test_it_no_custom_acl(self):
        self.assertEqual(self._callFUT(None), False)

    def test_it_old_custom_acl(self):
        class Dummy:
            pass
        ob = Dummy()
        ob.__acl__ = [123]
        ob.__custom_acl__ = [456]
        self.assertEqual(self._callFUT(ob), False)

    def test_it_current_custom_acl(self):
        class Dummy:
            pass
        ob = Dummy()
        ob.__acl__ = [123]
        ob.__custom_acl__ = [123]
        self.assertEqual(self._callFUT(ob), True)


class Test_get_security_states(unittest.TestCase):
    def _callFUT(self, workflow, context=None, request=None):
        from karl.security.workflow import get_security_states
        return get_security_states(workflow, context, request)

    def test_it_with_custom_acl(self):
        class Dummy:
            pass
        ob = Dummy()
        ob.__acl__ = [123]
        ob.__custom_acl__ = [123]
        states = [{'transitions':[1], 'current':True}]
        class DummyWorkflow:
            def state_info(self, context, request):
                return states
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), [])

    def test_it_without_custom_acl_two_states(self):
        class Dummy:
            pass
        ob = Dummy()
        states = [{'transitions':[1], 'current':False},
                  {'transitions':[2], 'current':False}]
        class DummyWorkflow:
            def state_info(self, context, request):
                return states
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), states)

    def test_it_without_custom_acl_no_transitions(self):
        class Dummy:
            pass
        ob = Dummy()
        class DummyWorkflow:
            def state_info(self, context, request):
                return [{'transitions':[], 'current':False}]
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), [])

    def test_it_single_state_only(self):
        class Dummy:
            pass
        ob = Dummy()
        class DummyWorkflow:
            def state_info(self, context, request):
                return [{'current':True}]
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), [])

    def test_it_current_state_used_without_transitions(self):
        class Dummy:
            pass
        ob = Dummy()
        states = [{'current':True},
                  {'current':False, 'transitions':['123']}]
        class DummyWorkflow:
            def state_info(self, context, request):
                return states
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), states)

class Test_available_workflow_states(unittest.TestCase):
    def _callFUT(self, workflow, context=None, request=None):
        from karl.security.workflow import available_workflow_states
        return available_workflow_states(workflow, context, request)

    def test_it_two_states(self):
        class Dummy:
            pass
        ob = Dummy()
        states = [{'transitions':[1], 'current':False},
                  {'transitions':[2], 'current':False}]
        class DummyWorkflow:
            def state_info(self, context, request):
                return states
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), states)

    def test_it_no_transitions(self):
        class Dummy:
            pass
        ob = Dummy()
        class DummyWorkflow:
            def state_info(self, context, request):
                return [{'transitions':[], 'current':False}]
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), [])

    def test_it_single_state_only(self):
        class Dummy:
            pass
        ob = Dummy()
        class DummyWorkflow:
            def state_info(self, context, request):
                return [{'current':True}]
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), [])

    def test_it_current_state_used_without_transitions(self):
        class Dummy:
            pass
        ob = Dummy()
        states = [{'current':True},
                  {'current':False, 'transitions':['123']}]
        class DummyWorkflow:
            def state_info(self, context, request):
                return states
        self.assertEqual(self._callFUT(DummyWorkflow(), ob, None), states)

class Test_acl_diff(unittest.TestCase):
    def _callFUT(self, ob, acl):
        from karl.security.workflow import acl_diff
        return acl_diff(ob, acl)

    def test_call_no_diff_has_acl(self):
        ob = DummyContent()
        ob.__acl__ = {}
        result = self._callFUT(ob, {})
        self.assertEqual(result, (None, None))

    def test_call_no_diff_has_no_acl(self):
        ob = DummyContent()
        result = self._callFUT(ob, {})
        self.assertEqual(result, (None, None))

    def test_call_diff_left(self):
        ob = DummyContent()
        ob.__acl__ = [('Allow', 'foo', ('bar',))]
        result = self._callFUT(ob, {})
        self.assertEqual(result, ('', 'Allow foo bar'))

    def test_call_diff_right(self):
        ob = DummyContent()
        ob.__acl__ = []
        result = self._callFUT(ob, [('Allow', 'foo', ('bar',))])
        self.assertEqual(result, ('Allow foo bar', ''))

    def test_call_diff_both(self):
        ob = DummyContent()
        ob.__acl__ = [('Allow', 'baz', ('buz'))]
        result = self._callFUT(ob, [('Allow', 'foo', ('bar',))])
        self.assertEqual(result, ('Allow foo bar', 'Allow baz buz'))

class Test_ace_repr(unittest.TestCase):
    def _callFUT(self, ace):
        from karl.security.workflow import ace_repr
        return ace_repr(ace)

    def test_with_permissions_iter(self):
        result = self._callFUT(('Allow', 'foo', ('buz',)))
        self.assertEqual(result, 'Allow foo buz')

    def test_with_permissions_not_iter(self):
        result = self._callFUT(('Allow', 'foo', 'buz'))
        self.assertEqual(result, 'Allow foo buz')

    def test_with_permissions_all(self):
        from karl.security.policy import ALL
        result = self._callFUT(('Allow', 'foo', ALL))
        self.assertEqual(result, 'Allow foo ALL')

    def test_multiple_permissions(self):
        result = self._callFUT(('Allow', 'foo', ('edit', 'delete', 'view')))
        self.assertEqual(result, 'Allow foo delete, edit, view')


class TestBasicAuthenticationPolicy(unittest.TestCase):

    def setUp(self):
        context = testing.DummyModel()
        context.users = DummyUsers()
        self.request = request = testing.DummyRequest(context=context)
        request.environ['wsgi.version'] = '1.0'
        self.set_credentials('login', 'password')
        self.patcher = mock.patch('karl.security.basicauth.get_sha_password',
                                  lambda x: x)
        self.patcher.start()

    def set_credentials(self, login, password):
        import base64
        self.request.environ['HTTP_AUTHORIZATION'] = (
            "Basic %s" % base64.encodestring(
                '%s:%s' % (login, password))[:-1])

    def tearDown(self):
        self.patcher.stop()

    def make_one(self):
        from karl.security.basicauth import BasicAuthenticationPolicy as CUT
        return CUT()

    def test_authenticated_userid(self):
        policy = self.make_one()
        self.assertEqual(policy.authenticated_userid(self.request), 'userid')

    def test_authenticated_userid_bad_header(self):
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Bad'
        self.assertEqual(policy.authenticated_userid(self.request), None)

    def test_authenticated_userid_bad_base64_encoding(self):
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Basic aaa'
        self.assertEqual(policy.authenticated_userid(self.request), None)

    def test_authenticated_userid_bad_encoded_data(self):
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Basic waah!'
        self.assertEqual(policy.authenticated_userid(self.request), None)

    def test_authenticated_userid_not_basic_auth(self):
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Complicated waah!'
        self.assertEqual(policy.authenticated_userid(self.request), None)

    def test_authenticated_userid_wrong_password(self):
        self.set_credentials('login', 'wrong')
        policy = self.make_one()
        self.assertEqual(policy.authenticated_userid(self.request), None)

    def test_effective_principals(self):
        from pyramid.security import Everyone
        from pyramid.security import Authenticated
        policy = self.make_one()
        self.assertEqual(policy.effective_principals(self.request),
            [Everyone, Authenticated, 'userid', 'a', 'c', 'b'])

    def test_effective_principals_wrong_password(self):
        from pyramid.security import Everyone
        policy = self.make_one()
        self.set_credentials('login', 'wrong')
        self.assertEqual(policy.effective_principals(self.request), [Everyone])

    def test_effective_principals_bad_credentials(self):
        from pyramid.security import Everyone
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Bad bad'
        self.assertEqual(policy.effective_principals(self.request), [Everyone])

    def test_unauthenticated_userid(self):
        policy = self.make_one()
        self.assertEqual(policy.unauthenticated_userid(self.request), 'login')

    def test_unauthenticated_userid_bad_credentials(self):
        policy = self.make_one()
        self.request.environ['HTTP_AUTHORIZATION'] = 'Bad bad'
        self.assertEqual(policy.unauthenticated_userid(self.request), None)

    def test_remember(self):
        policy = self.make_one()
        self.assertEqual(policy.remember('foo', self.request), [])

    def test_forget(self):
        policy = self.make_one()
        self.assertEqual(policy.forget(self.request), [
            ('WWW-Authenticate', 'Basic realm="Realm"')])


class Test_get_kerberos_userid(unittest.TestCase):
    tearDown = testing.tearDown

    def setUp(self):
        testing.setUp()

        class MockGSSError(Exception):
            pass

        patcher = mock.patch('karl.security.kerberos_auth.kerberos')
        self.kerberos = patcher.start()
        self.kerberos.GSSError = MockGSSError
        self.addCleanup(patcher.stop)

    def call_fut(self, request):
        from karl.security.kerberos_auth import get_kerberos_userid as fut
        return fut(request)

    def test_no_authorization_header(self):
        request = testing.DummyRequest(authorization=None)
        self.assertEqual(self.call_fut(request), None)

    def test_no_authorization_header_issue_challenge(self):
        from pyramid.httpexceptions import HTTPUnauthorized
        request = testing.DummyRequest(authorization=None)
        request.GET['challenge'] = '1'
        with self.assertRaises(HTTPUnauthorized) as cm:
            self.call_fut(request)
        response = cm.exception
        self.assertEqual(response.headers['WWW-Authenticate'], 'Negotiate')

    def test_authorization_header_not_negotiate(self):
        request = testing.DummyRequest(
            authorization=('Basic', 'blah blah blah'))
        self.assertEqual(self.call_fut(request), None)

    def test_unable_to_initialize_service(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'))
        self.kerberos.authGSSServerInit.return_value = 0, 'context'
        self.assertEqual(self.call_fut(request), None)
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')

    def test_bad_ticket(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'))
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 0
        self.assertEqual(self.call_fut(request), None)
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')

    def test_error_ticket(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            remote_addr='127.0.0.1')
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.side_effect = self.kerberos.GSSError
        self.assertEqual(self.call_fut(request), None)
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')

    def test_authenticated_with_login_user_finder(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            context=testing.DummyModel())
        request.context.users = DummyUsers()
        request.registry.settings = {}
        request.registry.settings['kerberos.user_finder'] = \
            'karl.security.kerberos_auth.login_user_finder'
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 1
        self.kerberos.authGSSServerUserName.return_value = \
                'joey\\exampledomain@examplerealm'
        self.assertEqual(self.call_fut(request), 'joefrommexico')
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')
        self.kerberos.authGSSServerUserName.assert_called_once_with('context')
        self.kerberos.authGSSServerClean.assert_called_once_with('context')

    def test_authenticated_with_login_user_finder_realm_and_domain_match(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            context=testing.DummyModel())
        request.context.users = DummyUsers()
        request.registry.settings = {}
        request.registry.settings['kerberos.user_finder'] = \
            'karl.security.kerberos_auth.login_user_finder'
        request.registry.settings['kerberos.allowed_realms'] = \
                'foo examplerealm'
        request.registry.settings['kerberos.allowed_domains'] = \
                'foo exampledomain'
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 1
        self.kerberos.authGSSServerUserName.return_value = \
                'joey\\exampledomain@examplerealm'
        self.assertEqual(self.call_fut(request), 'joefrommexico')
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')
        self.kerberos.authGSSServerUserName.assert_called_once_with('context')
        self.kerberos.authGSSServerClean.assert_called_once_with('context')

    def test_authenticated_realm_does_not_match(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            context=testing.DummyModel())
        request.context.users = DummyUsers()
        request.registry.settings = {}
        request.registry.settings['kerberos.user_finder'] = \
            'karl.security.kerberos_auth.login_user_finder'
        request.registry.settings['kerberos.allowed_realms'] = \
                'foo examplerealm'
        request.registry.settings['kerberos.allowed_domains'] = \
                'foo exampledomain'
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 1
        self.kerberos.authGSSServerUserName.return_value = \
                'joey\\exampledomain@anotherrealm'
        self.assertEqual(self.call_fut(request), None)
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')
        self.kerberos.authGSSServerUserName.assert_called_once_with('context')
        self.kerberos.authGSSServerClean.assert_called_once_with('context')

    def test_authenticated_domain_does_not_match(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            context=testing.DummyModel())
        request.context.users = DummyUsers()
        request.registry.settings = {}
        request.registry.settings['kerberos.user_finder'] = \
            'karl.security.kerberos_auth.login_user_finder'
        request.registry.settings['kerberos.allowed_realms'] = \
                'foo examplerealm'
        request.registry.settings['kerberos.allowed_domains'] = \
                'foo exampledomain'
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 1
        self.kerberos.authGSSServerUserName.return_value = \
                'joey\\anotherdomain@examplerealm'
        self.assertEqual(self.call_fut(request), None)
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')
        self.kerberos.authGSSServerUserName.assert_called_once_with('context')
        self.kerberos.authGSSServerClean.assert_called_once_with('context')

    def test_authenticated_with_mapping_user_finder(self):
        request = testing.DummyRequest(
            authorization=('Negotiate', 'ticket'),
            context=testing.DummyModel())
        request.context.users = DummyUsers()
        self.kerberos.authGSSServerInit.return_value = 1, 'context'
        self.kerberos.authGSSServerStep.return_value = 1
        self.kerberos.authGSSServerUserName.return_value = \
                'joey\\exampledomain@examplerealm'
        self.assertEqual(self.call_fut(request), 'joefrommexico')
        self.kerberos.authGSSServerInit.assert_called_once_with(
            'HTTP@example.com')
        self.kerberos.authGSSServerStep.assert_called_once_with(
            'context', 'ticket')
        self.kerberos.authGSSServerUserName.assert_called_once_with('context')
        self.kerberos.authGSSServerClean.assert_called_once_with('context')


class TestSSOIncludeMe(unittest.TestCase):

    def call_fut(self, config):
        from karl.security.sso import includeme as fut
        return fut(config)

    def test_not_configured(self):
        config = mock.Mock()
        config.registry.settings = {}
        self.call_fut(config)
        config.scan.assert_not_called()

    def test_github_provider(self):
        config = mock.Mock()
        config.registry.settings = {
            'sso': 'foo',
            'sso.foo.provider': 'github'}
        self.call_fut(config)
        config.scan.assert_called_once_with('karl.security.sso')
        config.include.assert_called_once_with('velruse.providers.github')
        config.add_github_login_from_settings.called_once_with(
            prefix='sso.foo.')

    def test_google_provider(self):
        config = mock.Mock()
        config.registry.settings = {
            'sso': 'foo',
            'sso.foo.provider': 'google',
            'sso.foo.realm': 'realm',
            'sso.foo.consumer_key': 'consumer_key',
            'sso.foo.consumer_secret': 'consumer_secret'}
        self.call_fut(config)
        config.scan.assert_called_once_with('karl.security.sso')
        config.include.assert_called_once_with('velruse.providers.google')
        config.add_google_login.called_once_with('realm', 'consumer_key',
                                                 'consumer_secret')

    def test_yahoo_provider(self):
        config = mock.Mock()
        config.registry.settings = {
            'sso': 'foo',
            'sso.foo.provider': 'yahoo',
            'sso.foo.realm': 'realm',
            'sso.foo.consumer_key': 'consumer_key',
            'sso.foo.consumer_secret': 'consumer_secret'}
        self.call_fut(config)
        config.scan.assert_called_once_with('karl.security.sso')
        config.include.assert_called_once_with('velruse.providers.yahoo')
        config.add_google_login.called_once_with('realm', 'consumer_key',
                                                 'consumer_secret')

    def test_yasso_provider(self):
        config = mock.Mock()
        config.registry.settings = {
            'sso': 'foo',
            'sso.foo.provider': 'yasso'}
        self.call_fut(config)
        config.scan.assert_called_once_with('karl.security.sso')
        config.include.assert_called_once_with('karl.security.sso_yasso')
        config.add_yasso_login_from_settings.called_once_with(
            prefix='sso.foo.')

    def test_bad_provider(self):
        config = mock.Mock()
        config.registry.settings = {
            'sso': 'foo',
            'sso.foo.provider': 'fake'}
        with self.assertRaises(ValueError):
            self.call_fut(config)


class TestSSOLoginSuccess(unittest.TestCase):

    def setUp(self):
        self.request = request = mock.Mock()
        request.registry.settings = self.settings = {}
        self.site = request.registry.queryUtility.return_value.return_value = \
            testing.DummyResource(users=mock.Mock())
        self.context = mock.Mock()
        self.context.profile = {}

    def call_fut(self):
        from karl.security.sso import sso_login_success as fut
        return fut(self.context, self.request)

    @mock.patch('karl.security.sso.remember_login')
    def test_mapping_finder_user_found(self, remember_login):
        self.context.profile['userid'] = 'theuser'
        self.site.users.get.return_value = {'id': 'theuser'}
        self.assertEqual(self.call_fut(), remember_login.return_value)

    def test_mapping_finder_user_not_found(self):
        self.context.profile['userid'] = 'theuser'
        self.site.users.get.return_value = None
        self.request.resource_url.return_value = 'redirect_to'
        response = self.call_fut()
        self.assertEqual(response.location, 'redirect_to')

    @mock.patch('karl.security.sso.remember_login')
    def test_login_finder(self, remember_login):
        self.context.profile['userid'] = 'theuser'
        self.site.users.get.return_value = {'id': 'theuser'}
        self.settings['sso_user_finder'] = 'karl.security.sso.login_user_finder'
        self.assertEqual(self.call_fut(), remember_login.return_value)


class TestSSOLoginFailure(unittest.TestCase):

    def test_it(self):
        from karl.security.sso import sso_login_failure as fut
        request = mock.Mock()
        site = request.registry.queryUtility.return_value.return_value
        response = fut(request)
        request.resource_url.assert_called_once_with(site, 'login.html',
            query={'reason': "Authentication failed at external provider."})
        self.assertEqual(response.location, request.resource_url.return_value)


class TestVerifiedEmailUserFinder(unittest.TestCase):

    def setUp(self):
        self.context = mock.Mock()
        self.context.profile = {}
        self.site = testing.DummyResource()
        self.site.users = mock.Mock()
        patcher = mock.patch('karl.security.sso.ICatalogSearch')
        self.addCleanup(patcher.stop)
        self.ICatalogSearch = patcher.start()

    def call_fut(self):
        from karl.security.sso import verified_email_user_finder as fut
        return fut(self.site, self.context)

    def test_no_verified_email(self):
        self.assertEqual(self.call_fut(), None)

    def test_user_not_found(self):
        from karl.models.interfaces import IProfile
        self.context.profile['verifiedEmail'] = 'john@fake'
        self.ICatalogSearch.return_value.return_value = (0, [], None)
        self.assertEqual(self.call_fut(), None)
        self.ICatalogSearch.assert_called_once_with(self.site)
        self.ICatalogSearch.return_value.assert_called_once_with(
            interfaces=[IProfile], email='john@fake')

    def test_too_many_users_found(self):
        from karl.models.interfaces import IProfile
        self.context.profile['verifiedEmail'] = 'john@fake'
        self.ICatalogSearch.return_value.return_value = (2, [], None)
        self.assertEqual(self.call_fut(), None)
        self.ICatalogSearch.assert_called_once_with(self.site)
        self.ICatalogSearch.return_value.assert_called_once_with(
            interfaces=[IProfile], email='john@fake')

    def test_one_user_found(self):
        from karl.models.interfaces import IProfile
        self.context.profile['verifiedEmail'] = 'john@fake'
        profile = mock.Mock()
        profile.__name__ = 'john'
        self.ICatalogSearch.return_value.return_value = (
            1, [profile], lambda x:x)
        self.site.users.get.return_value = 'identity'
        self.assertEqual(self.call_fut(), 'identity')
        self.ICatalogSearch.assert_called_once_with(self.site)
        self.ICatalogSearch.return_value.assert_called_once_with(
            interfaces=[IProfile], email='john@fake')
        self.site.users.called_once_with('john')


class DummyUsers(object):

    def __init__(self):
        self.data = {
            'login': {
                'id': 'userid',
                'groups': set(['a', 'b', 'c']),
                'password': 'password'
            },
            'joey': {
                'id': 'joefrommexico'
            }
        }
        self.sso_map = {
            'joey\\exampledomain@examplerealm': 'joey'
        }

    def get(self, userid=None, login=None):
        if not login:
            login = userid
        return self.data.get(login)


class DummyContent:
    pass

