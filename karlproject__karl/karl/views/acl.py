# Copyright (C) 2008-2009 Open Society Institute
#               Thomas Moroz: tmoroz@sorosny.org
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License Version 2 as published
# by the Free Software Foundation.  You may not use, modify or distribute
# this program under any other version of the GNU General Public License.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import re

from pyramid.renderers import render_to_response
from pyramid.traversal import resource_path
from pyramid.url import resource_url

from repoze.folder.interfaces import IFolder
from repoze.lemonade.content import get_content_type
from repoze.lemonade.content import is_content
from repoze.workflow import get_workflow

from karl.security.policy import NO_INHERIT
from karl.security.workflow import get_security_states
from karl.security.workflow import postorder

from karl.utils import find_catalog

COMMA_WS = re.compile(r'[\s,]+')

def get_context_workflow(context):
    """
    If context is content and part of a workflow will return the workflow.
    Otherwise returns None.
    """
    if is_content(context):
        content_type = get_content_type(context)
        return get_workflow(content_type, 'security', context)

def edit_acl_view(context, request):

    acl = original_acl = getattr(context, '__acl__', [])
    if acl and acl[-1] == NO_INHERIT:
        acl = acl[:-1]
        epilog = [NO_INHERIT]
    else:
        epilog = []

    if 'form.move_up' in request.POST:
        index = int(request.POST['index'])
        if index > 0:
            new = acl[:]
            new[index-1], new[index] = new[index], new[index-1]
            acl = new

    elif 'form.move_down' in request.POST:
        index = int(request.POST['index'])
        if index < len(acl) - 1:
            new = acl[:]
            new[index+1], new[index] = new[index], new[index+1]
            acl = new

    elif 'form.remove' in request.POST:
        index = int(request.POST['index'])
        new = acl[:]
        del new[index]
        acl = new

    elif 'form.add' in request.POST:
        verb = request.POST['verb']
        principal = request.POST['principal']
        permissions = tuple(filter(None,
                              COMMA_WS.split(request.POST['permissions'])))
        new = acl[:]
        new.append((verb, principal, permissions))
        acl = new

    elif 'form.inherit' in request.POST:
        no_inherit = request.POST['inherit'] == 'disabled'
        if no_inherit:
            epilog = [NO_INHERIT]
        else:
            epilog = []

    elif 'form.security_state' in request.POST:
        new_state = request.POST['security_state']
        if new_state != 'CUSTOM':
            workflow = get_context_workflow(context)
            if hasattr(context, '__custom_acl__'):
                workflow.reset(context)
                del context.__custom_acl__
            workflow.transition_to_state(context, request, new_state)

    acl = acl + epilog

    if acl != original_acl:
        context.__custom_acl__ = acl # added so we can find customized obs later
        context.__acl__ = acl
        catalog = find_catalog(context)
        if catalog is not None:
            allowed = catalog.get('allowed')
            if allowed is not None:
                for node in postorder(context):
                    allowed.reindex_doc(node.docid, node)
                catalog.invalidate()

    workflow = get_context_workflow(context)
    if workflow is not None:
        if hasattr(context, '__custom_acl__'):
            security_state = 'CUSTOM'
            security_states = [s['name'] for s in
                               workflow.state_info(context, request)]
            security_states.insert(0, 'CUSTOM')
        else:
            security_state = workflow.state_of(context)
            security_states = [s['name'] for s in
                               get_security_states(workflow, context, request)]

    else:
        security_state = None
        security_states = None

    parent = context.__parent__
    parent_acl = []
    while parent is not None:
        p_acl = getattr(parent, '__acl__', ())
        stop = False
        for ace in p_acl:
            if ace == NO_INHERIT:
                stop = True
            else:
                parent_acl.append(ace)
        if stop:
            break
        parent = parent.__parent__

    local_acl = []
    inheriting = 'enabled'
    l_acl = getattr(context, '__acl__', ())
    for l_ace in l_acl:
        if l_ace == NO_INHERIT:
            inheriting = 'disabled'
            break
        local_acl.append(l_ace)


    return render_to_response(
        'templates/edit_acl.pt',
        dict(parent_acl=parent_acl or (),
             local_acl=local_acl,
             inheriting=inheriting,
             security_state=security_state,
             security_states=security_states),
        request=request,
        )

def make_acls(node, request, acls=None, offset=0):
    if acls is None:
        acls = []
    path = resource_path(node)
    url = resource_url(node, request)
    acl = getattr(node, '__acl__', None)
    folderish = IFolder.providedBy(node)
    name = node.__name__ or '/'
    has_children = False
    security_state = getattr(node, 'security_state', None)
    if folderish:
        has_children = bool(len(node))
    if (folderish and has_children) or acl is not None:
        acls.append({'offset':offset, 'path':path, 'acl':acl, 'name':name,
                     'security_state':security_state, 'url':url})
    if folderish:
        children = list(node.items())
        children.sort()
        for childname, child in children:
            make_acls(child, request, acls, offset+1)
    node._p_deactivate()
    return acls

def acl_tree_view(context, request):
    acls = make_acls(context, request)
    return render_to_response(
        'templates/acl_tree.pt',
        dict(acls = acls),
        request=request)





