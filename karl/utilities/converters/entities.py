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
from karl.utilities.converters.entities2uc import entitydefs

# Matches entities
entity_reg = re.compile('&(.*?);')

def handler(x):
    """ Callback to convert entity to UC """
    v = x.group(1)
    if v.startswith('#'):
        try:
            return unichr(int(v[1:]))
        except ValueError:
            pass
    return entitydefs.get(v, '')

def convert_entities(text):
    """ replace all entities inside a unicode string """
    if not isinstance(text, unicode):
        text = text.decode('UTF-8')
    text = entity_reg.sub(handler, text)
    return text

