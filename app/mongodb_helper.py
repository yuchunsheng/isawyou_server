
from pymongo import uri_parser
from pymongo.read_preferences import ReadPreference
import pymongo

from flask_pymongo.wrappers import MongoClient
from flask_pymongo.wrappers import MongoReplicaSetClient


class MongodbHelper(object):
    """Automatically connects to MongoDB using parameters defined in Flask
    configuration.
    """

    def __init__(self, config=None, config_prefix='MONGO'):
        if config is not None:
            self.config_prefix = config_prefix
            self.init_app(config, config_prefix)

    def init_app(self, config, config_prefix='MONGO'):

        self.config_prefix = config_prefix

        def key(suffix):
            return '%s_%s' % (config_prefix, suffix)

        if key('URI') in config:
            # bootstrap configuration from the URL
            parsed = uri_parser.parse_uri(config[key('URI')])
            if not parsed.get('database'):
                raise ValueError('MongoDB URI does not contain database name')
            config[key('DBNAME')] = parsed['database']
            config[key('READ_PREFERENCE')] = parsed['options'].get('read_preference')
            config[key('USERNAME')] = parsed['username']
            config[key('PASSWORD')] = parsed['password']
            config[key('REPLICA_SET')] = parsed['options'].get('replica_set')
            config[key('MAX_POOL_SIZE')] = parsed['options'].get('max_pool_size')
            config[key('SOCKET_TIMEOUT_MS')] = parsed['options'].get('socket_timeout_ms', None)
            config[key('CONNECT_TIMEOUT_MS')] = parsed['options'].get('connect_timeout_ms', None)

            if pymongo.version_tuple[0] < 3:
                config[key('AUTO_START_REQUEST')] = parsed['options'].get('auto_start_request', True)
            else:
                config[key('CONNECT')] = parsed['options'].get('connect', True)

            # we will use the URI for connecting instead of HOST/PORT
            config.pop(key('HOST'), None)
            config.setdefault(key('PORT'), 27017)
            host = config[key('URI')]

        else:
            config.setdefault(key('HOST'), 'localhost')
            config.setdefault(key('PORT'), 27017)
            config.setdefault(key('DBNAME'), '')
            config.setdefault(key('READ_PREFERENCE'), None)
            config.setdefault(key('SOCKET_TIMEOUT_MS'), None)
            config.setdefault(key('CONNECT_TIMEOUT_MS'), None)

            if pymongo.version_tuple[0] < 3:
                config.setdefault(key('AUTO_START_REQUEST'), True)
            else:
                config.setdefault(key('CONNECT'), True)

            # these don't have defaults
            config.setdefault(key('USERNAME'), None)
            config.setdefault(key('PASSWORD'), None)
            config.setdefault(key('REPLICA_SET'), None)
            config.setdefault(key('MAX_POOL_SIZE'), None)

            try:
                int(config[key('PORT')])
            except ValueError:
                raise TypeError('%s_PORT must be an integer' % config_prefix)

            host = config[key('HOST')]

        username = config[key('USERNAME')]
        password = config[key('PASSWORD')]

        auth = (username, password)

        if any(auth) and not all(auth):
            raise Exception('Must set both USERNAME and PASSWORD or neither')

        read_preference = config[key('READ_PREFERENCE')]
        if isinstance(read_preference, str):
            # Assume the string to be the name of the read
            # preference, and look it up from PyMongo
            read_preference = getattr(ReadPreference, read_preference)
            if read_preference is None:
                raise ValueError(
                    '%s_READ_PREFERENCE: No such read preference name (%r)' % (
                        config_prefix, read_preference))
            config[key('READ_PREFERENCE')] = read_preference
        # Else assume read_preference is already a valid constant
        # from pymongo.read_preferences.ReadPreference or None

        replica_set = config[key('REPLICA_SET')]
        dbname = config[key('DBNAME')]
        max_pool_size = config[key('MAX_POOL_SIZE')]
        socket_timeout_ms = config[key('SOCKET_TIMEOUT_MS')]
        connect_timeout_ms = config[key('CONNECT_TIMEOUT_MS')]

        if pymongo.version_tuple[0] < 3:
            auto_start_request = config[key('AUTO_START_REQUEST')]
            if auto_start_request not in (True, False):
                raise TypeError('%s_AUTO_START_REQUEST must be a bool' % config_prefix)

        # document class is not supported by URI, using setdefault in all cases
        document_class = config.setdefault(key('DOCUMENT_CLASS'), None)

        args = [host]

        kwargs = {
            'port': int(config[key('PORT')]),
            'tz_aware': True,
        }
        if pymongo.version_tuple[0] < 3:
            kwargs['auto_start_request'] = auto_start_request
        else:
            kwargs['connect'] = config[key('CONNECT')]

        if read_preference is not None:
            kwargs['read_preference'] = read_preference

        if socket_timeout_ms is not None:
            kwargs['socketTimeoutMS'] = socket_timeout_ms

        if connect_timeout_ms is not None:
            kwargs['connectTimeoutMS'] = connect_timeout_ms

        if pymongo.version_tuple[0] < 3:
            if replica_set is not None:
                kwargs['replicaSet'] = replica_set
                connection_cls = MongoReplicaSetClient
            else:
                connection_cls = MongoClient
        else:
            kwargs['replicaSet'] = replica_set
            connection_cls = MongoClient

        if max_pool_size is not None:
            kwargs['max_pool_size'] = max_pool_size

        if document_class is not None:
            kwargs['document_class'] = document_class

        cx = connection_cls(*args, **kwargs)
        db = cx[dbname]

        if any(auth):
            db.authenticate(username, password)
        self.content = [cx, db]



    @property
    def cx(self):

        return self.content[0]

    @property
    def db(self):

        return self.content[1]


