from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound


class WikiViews(object):

    def __init__(self, request):
        self.request = request
        renderer = get_renderer("templates/layout.pt")
        self.layout = renderer.implementation().macros['layout']

    @view_config(route_name='wiki_view', renderer='templates/wiki_view.pt')
    def wiki_view(self):
        return dict(title='Welcome to the Wiki')

    @view_config(route_name='wikipage_add', renderer='templates/wikipage_addedit.pt')
    def wikipage_add(self):
        return dict(title='Add Wiki Page')

    @view_config(route_name='wikipage_view', renderer='templates/wikipage_view.pt')
    def wikipage_view(self):
        uid = self.request.matchdict['uid']
        return dict(title='View Wiki Page', uid=uid)

    @view_config(route_name='wikipage_edit', renderer='templates/wikipage_addedit.pt')
    def wikipage_edit(self):
        return dict(title='Edit Wiki Page')

    @view_config(route_name='wikipage_delete')
    def wikipage_delete(self):
        return HTTPFound('/')
