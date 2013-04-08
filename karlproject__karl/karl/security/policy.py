from BTrees.IFBTree import multiunion
from BTrees.IFBTree import IFSet

from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import AllPermissionsList

VIEW = 'view'
EDIT = 'edit'
CREATE = 'create'
DELETE = 'delete'
DELETE_COMMUNITY = 'delete community'
EMAIL = 'email'
MODERATE = 'moderate'
ADMINISTER = 'administer'
COMMENT = 'comment'

GUEST_PERMS = (VIEW, COMMENT)
MEMBER_PERMS = GUEST_PERMS + (EDIT, CREATE, DELETE)
MODERATOR_PERMS = MEMBER_PERMS + (MODERATE,)
ADMINISTRATOR_PERMS = MODERATOR_PERMS + (ADMINISTER, DELETE_COMMUNITY, EMAIL)

ALL = AllPermissionsList()
NO_INHERIT = (Deny, Everyone, ALL)

class ACLChecker(object):
    """ 'Checker' object used as a ``attr_checker`` callback for a
    path index set up to use the __acl__ attribute as an
    ``attr_discriminator`` """
    def __init__(self, principals, permission='view'):
        self.principals = principals
        self.permission = permission

    def __call__(self, result):
        sets = []
        for (docid, acls), set in result:
            if not set:
                continue
            if self.check_acls(acls):
                sets.append(set)
        if not sets:
            return IFSet()
        return multiunion(sets)

    def check_acls(self, acls):
        acls = list(reversed(acls))
        for acl in acls:
            for ace in acl:
                ace_action, ace_principal, ace_permissions = ace
                if ace_principal in self.principals:
                    if not hasattr(ace_permissions, '__iter__'):
                        ace_permissions = [ace_permissions]
                    if self.permission in ace_permissions:
                        if ace_action == Allow:
                            return True
                        else:
                            # deny of any means deny all of everything
                            return False
        return False

def get_groups(identity, request):
    if 'groups' in identity:
        return identity['groups']

