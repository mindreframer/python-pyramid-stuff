import os
import sys
import transaction

from sqlalchemy import create_engine

from ..models import (
    DBSession,
    User,
    Occurance,
    EventType,
    Base
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    dburl = argv[1]
    blastdb(dburl)

def blastdb(dburl = os.environ.get('DATABASE_URL')):
    engine = create_engine(dburl)
    DBSession.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    admin = User("shogunOfClicks")
    DBSession.add(admin)
    transaction.commit()

if __name__ == '__main__':
    main()
