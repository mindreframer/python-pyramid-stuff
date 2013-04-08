import unittest
from pyramid import testing

from pyramid.config import Configurator
from pyramid.threadlocal import get_current_registry

from karl.views.interfaces import IToolAddables
from karl.models.interfaces import IToolFactory
from repoze.lemonade.listitem import get_listitems
from zope.interface import implements

class TestPopulate(unittest.TestCase):
    """
    XXX Integration test.
    """
    def setUp(self):
        testing.cleanUp()

        import os
        os.environ['SUPPRESS_MAIL'] = 'true'

    def tearDown(self):
        testing.cleanUp()

        import os
        del os.environ['SUPPRESS_MAIL']

    def _registerComponents(self):
        # Install a bit of configuration that make_app() usually
        # does for us.
        from karl.application import configure_karl
        reg = get_current_registry()
        config = Configurator(reg, autocommit=True, package='karl.includes')
        config.setup_registry()
        config.registry.settings['who_secret'] = 'secret'
        config.registry.settings['who_cookie'] = 'oatmeal'
        configure_karl(config)
        from zope.interface import Interface
        config.registry.registerAdapter(DummyToolAddables,
                                        (Interface, Interface),
                                        IToolAddables)

    def _callFUT(self, root, do_transaction_begin=True):
        from karl.bootstrap.bootstrap import populate
        populate(root, do_transaction_begin=do_transaction_begin)

    def test_it(self):
        self._registerComponents()
        root = DummyDummy()
        connections = {}
        connections['main'] = DummyConnection(root, connections)
        root._p_jar = connections['main']

        self._callFUT(root, False)
        site = root['site']

        communities = site.get('communities')
        self.failUnless(communities)
        self.assertEqual(len(communities), 1)

        default_community = site['communities'].get('default')
        self.failUnless(default_community)

        profiles = site.get('profiles')
        self.failUnless(profiles)

        admin_profile = profiles.get('admin')
        self.failUnless(admin_profile)

    def test_external_catalog(self):
        self._registerComponents()
        root = DummyDummy()
        connections = {}
        connections['main'] = DummyConnection(root, connections)
        connections['catalog'] = DummyConnection(
            testing.DummyModel(), connections)
        root._p_jar = connections['main']

        self._callFUT(root, False)
        self.assertEquals(len(connections['catalog'].added), 1)

        catalog = connections['catalog'].root()['catalog']
        self.assertEquals(root['site'].catalog, catalog)


class DummyToolFactory:
    def add(self, context, request):
        self.context = context
        self.request = request

class DummySecurityWorkflow:
    initial_state_set = False

    def __init__(self, context):
        self.context = context

    def setInitialState(self):
        self.initial_state_set = True

class DummyConnection:
    def __init__(self, root, connections):
        self._root = root
        self.connections = connections
        self.added = []
    def get_connection(self, name):
        return self.connections[name]
    def root(self):
        return self._root
    def add(self, obj):
        self.added.append(obj)

class DummyDummy(dict):
    pass

EXCLUDE_TOOLS = ['intranets',]

class DummyToolAddables(object):
    implements(IToolAddables)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        """ What tools can go in a community?
        """
        tools = get_listitems(IToolFactory)
        return [tool for tool in tools if tool['name'] not in EXCLUDE_TOOLS]

