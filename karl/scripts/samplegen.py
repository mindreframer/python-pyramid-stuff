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
"""Generate sample content in a KARL site.
"""


# XXX XXX This file is in fact not used any more because we use it
# XXX XXX via karlsample. Remove this, to avoid a duplication?


from ConfigParser import ConfigParser
from karl.scripting import get_default_config
from karl.scripting import open_root
from karl.utilities.samplegen import add_sample_community
from karl.utilities.samplegen import add_sample_users
import logging
import optparse
import os
import sys
import transaction

import logging
logging.basicConfig()

def main(argv=sys.argv):
    logging.basicConfig()
    logging.getLogger('karl').setLevel(logging.INFO)

    parser = optparse.OptionParser(description=__doc__)
    parser.add_option('-C', '--config', dest='config',
        help='Path to configuration file (defaults to $CWD/etc/karl.ini)',
        metavar='FILE')
    parser.add_option('-c', '--communities', dest='communities',
        default='10',
        help='Number of communities to add (default 10)')
    parser.add_option('--dry-run', dest='dryrun',
        action='store_true', default=False,
        help="Don't actually commit the transaction")
    options, args = parser.parse_args(argv[1:])
    if args:
        parser.error("Too many parameters: %s" % repr(args))

    config = options.config
    if config is None:
        config = get_default_config()
    root, closer = open_root(config)

    try:
        add_sample_users(root)
        for i in range(int(options.communities)):
            add_sample_community(root, more_files=i==0)
    except:
        transaction.abort()
        raise
    else:
        if options.dryrun:
            transaction.abort()
        else:
            transaction.commit()

if __name__ == '__main__':
    main()
