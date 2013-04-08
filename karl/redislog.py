import json
import logging
import StringIO
import time
import traceback
import uuid

try:
    import redis
    redis # stfu pyflakes
except:
    redis = None


ERROR = 'ERROR'
WARN = 'WARN'
INFO = 'INFO'
DEBUG = 'DEBUG'

log_levels = {
    logging.ERROR: ERROR,
    logging.WARN: WARN,
    logging.INFO: INFO,
    logging.DEBUG: DEBUG}

NORECORD = '\0' * 16


class RedisLog(object):

    def __init__(self, host='localhost', port=6379, db=0, prefix='log',
                 expires=7, password=None): # days
        self.redis = redis.StrictRedis(host=host, port=port, db=db,
                                      password=password)
        self.prefix = prefix
        self.ttl = expires * 24 * 3600 # seconds

    def log(self, level, category, message, exc_info=False):
        prefix = self.prefix

        if isinstance(level, int):
            level = log_levels[level]
        if exc_info:
            tb_info  = traceback.format_exc()
        else:
            tb_info = None

        id = uuid.uuid1()
        entry = RedisLogEntry(level, category, message, tb_info)

        head_key = '%s:head' % prefix
        level_key = '%s:level:%s' % (prefix, level)
        category_key = '%s:category:%s' % (prefix, category)
        level_category_key = '%s:level:%s:category:%s' % (
            prefix, level, category)
        tx = self.redis.pipeline()
        for key in (head_key, level_key, category_key, level_category_key):
            tx.getset(key, id.bytes)
        record = [(key if key else NORECORD) for key in tx.execute()]
        record.append(entry.as_json())
        tx = self.redis.pipeline()
        tx.setex('%s:%s' % (prefix, str(id)), self.ttl, ''.join(record))
        if level == 'ERROR':
            alarm_key = '%s:alarm' % prefix
            tx.sadd(alarm_key, category)
        levels_key = '%s:levels' % prefix
        tx.sadd(levels_key, level)
        categories_key = '%s:categories' % prefix
        tx.sadd(categories_key, category)
        tx.execute()

    def iterate(self, level=None, category=None, start=0, count=-1):
        prefix = self.prefix
        if level and category:
            head = '%s:level:%s:category:%s' % (prefix, level, category)
            thread = 3
        elif not(level or category):
            head = '%s:head' % prefix
            thread = 0
        elif level:
            head = '%s:level:%s' % (prefix, level)
            thread = 1
        else:
            head = '%s:category:%s' % (prefix, category)
            thread = 2
        r = self.redis
        next_id = r.get(head)
        if not next_id:
            next_id = NORECORD
        while next_id != NORECORD:
            key = '%s:%s' % (prefix, str(uuid.UUID(bytes=bytes(next_id))))
            record = r.get(key)
            if not record:
                break
            record = StringIO.StringIO(record)
            next_ids = [record.read(16) for i in xrange(4)]
            if start:
                start -= 1
            else:
                yield RedisLogEntry.from_json(record.read())
                count -= 1
                if not count:
                    break
            next_id = next_ids[thread]

    def alarm(self):
        return self.redis.smembers('%s:alarm' % self.prefix)

    def clear_alarm(self):
        self.redis.delete('%s:alarm' % self.prefix)

    def levels(self):
        return self.redis.smembers('%s:levels' % self.prefix)

    def categories(self):
        return self.redis.smembers('%s:categories' % self.prefix)


class RedisLogEntry(object):

    @classmethod
    def from_json(cls, s):
        entry = cls.__new__(cls)
        entry.__dict__.update(json.loads(s))
        return entry

    def __init__(self, level, category, message, traceback):
        self.level = level
        self.category = category
        self.message = message
        self.traceback = traceback
        self.timestamp = time.time()

    def as_json(self):
        return json.dumps(self.__dict__)
