# -*- coding: utf-8 -*-

"""a simple facepp sdk
example:
api = API(key, secret)
api.detect(img = File('/tmp/test.jpg'))"""
import uuid

import io
import sys
import socket
import urllib
import json
import os.path
import mimetypes
import time
from collections import Iterable
import configparser


__all__ = ['File', 'APIError', 'API']


DEBUG_LEVEL = 1



class File(object):

    """an object representing a local file"""
    path = None
    content = None

    def __init__(self, path):
        self.path = path
        self._get_content()

    def _get_content(self):
        """read image content"""

        if os.path.getsize(self.path) > 2 * 1024 * 1024:
            raise APIError(-1, None, 'image file size too large')
        else:
            with open(self.path, 'rb') as f:
                self.content = f.read()


    def get_filename(self):
        return os.path.basename(self.path)


class FileMongodb(object):

    """an object representing a local file"""
    path = None
    content = None

    def __init__(self, file_obj):
        self.name = file_obj.name
        self.content = file_obj.read()

    def get_filename(self):
        return self.name


class APIError(Exception):
    code = None
    """HTTP status code"""

    url = None
    """request URL"""

    body = None
    """server response body; or detailed error information"""

    def __init__(self, code, url, body):
        self.code = code
        self.url = url
        self.body = body

    def __str__(self):
        return 'code={s.code}\nurl={s.url}\n{s.body}'.format(s=self)

    __repr__ = __str__


class API(object):
    key = None
    secret = None
    server = None

    decode_result = True
    timeout = None
    max_retries = None
    retry_delay = None

    def __init__(self, decode_result=True, timeout=30, max_retries=10,
                 retry_delay=5):
        """:param srv: The API server address
        :param decode_result: whether to json_decode the result
        :param timeout: HTTP request timeout in seconds
        :param max_retries: maximal number of retries after catching URL error
            or socket error
        :param retry_delay: time to sleep before retrying"""

        config = configparser.ConfigParser()
        mydir = os.path.dirname(os.path.abspath(__file__))
        new_path = os.path.join(mydir,  'apikey.cfg')
        config.read(new_path)

        self.key = config['DEFAULT']['API_KEY']
        self.secret = config['DEFAULT']['API_SECRET']
        self.server = config['DEFAULT']['SERVER']

        # self.key = key
        # self.secret = secret
        # if srv:
        #     self.server = srv
        self.decode_result = decode_result
        assert timeout >= 0 or timeout is None
        assert max_retries >= 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        _setup_apiobj(self, self, [])

    def update_request(self, request):
        """overwrite this function to update the request before sending it to
        server"""
        pass


def _setup_apiobj(self, api, path):
    if self is not api:
        self._api = api
        self._urlbase = api.server + '/'.join(path)

    lvl = len(path)
    done = set()
    for i in _APIS:
        if len(i) <= lvl:
            continue
        cur = i[lvl]
        if i[:lvl] == path and cur not in done:
            done.add(cur)
            setattr(self, cur, _APIProxy(api, i[:lvl + 1]))


class _APIProxy(object):
    _api = None
    """underlying :class:`API` object"""

    _urlbase = None

    def __init__(self, api, path):
        _setup_apiobj(self, api, path)

    def __call__(self, *args, **kargs):

        if len(args):
            raise TypeError('Only keyword arguments are allowed')

        form = _MultiPartForm()
        for (k, v) in kargs.items():
            if isinstance(v, FileMongodb):
                form.add_file(k, v.get_filename(), v.content)

        url = self._urlbase

        for k, v in self._mkarg(kargs).items():
            form.add_field(k, v)

        # url = 'https://api-us.faceplusplus.com/facepp/v3/faceset/create'
        body = bytes(form)

        request = urllib.request.Request(url, data=body)
        print(body)
        request.add_header('Content-type', form.get_content_type())
        request.add_header('Content-length', str(len(body)))

        self._api.update_request(request)

        retry = self._api.max_retries
        while True:
            retry -= 1
            try:
                print('url open')
                ret = urllib.request.urlopen(request, timeout=self._api.timeout).read()
                print('url open is done')
                break
            except urllib.request.HTTPError as e:
                raise APIError(e.code, url, e.read())
            except (socket.error, urllib.request.URLError) as e:
                if retry < 0:
                    raise e
                _print_debug('caught error: {}; retrying'.format(e))
                time.sleep(self._api.retry_delay)

        if self._api.decode_result:
            try:
                ret = json.loads(ret.decode('utf-8'))
                print('return json object')
            except:
                raise APIError(-1, url, 'json decode error, value={0!r}'.format(ret))
        return ret

    def _mkarg(self, kargs):
        """change the argument list (encode value, add api key/secret)
        :return: the new argument list"""
        def enc(x):
            # if isinstance(x, unicode):
            #     return x.encode('utf-8')
            return str(x)

        kargs_new = kargs.copy()
        kargs_new['api_key'] = self._api.key
        kargs_new['api_secret'] = self._api.secret
        for (k, v) in kargs.items():
            if isinstance(v, Iterable) and not isinstance(v, str):
                kargs_new[k] = ','.join([enc(i) for i in v])
            elif isinstance(v, File) or v is None:
                del kargs_new[k]
            else:
                kargs_new[k] = enc(v)

        return kargs_new

# https://pymotw.com/3/urllib.request/index.html
class _MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # Use a large random byte string to separate
        # parts of the MIME data.
        self.boundary = uuid.uuid4().hex.encode('utf-8')
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary={}'.format(
            self.boundary.decode('utf-8'))

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, content,
                 mimetype=None):
        """Add a file to be uploaded."""
        body = content
        if mimetype is None:
            mimetype = (
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream'
            )
        self.files.append((fieldname, filename, mimetype, body))
        return

    @staticmethod
    def _form_data(name):
        return ('Content-Disposition: form-data; '
                'name="{}"\r\n').format(name).encode('utf-8')

    @staticmethod
    def _attached_file(name, filename):
        return ('Content-Disposition: file; '
                'name="{}"; filename="{}"\r\n').format(
                    name, filename).encode('utf-8')

    @staticmethod
    def _content_type(ct):
        return 'Content-Type: {}\r\n'.format(ct).encode('utf-8')

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()
        boundary = b'--' + self.boundary + b'\r\n'

        # Add the form fields
        for name, value in self.form_fields:
            buffer.write(boundary)
            buffer.write(self._form_data(name))
            buffer.write(b'\r\n')
            buffer.write(value.encode('utf-8'))
            buffer.write(b'\r\n')

        # Add the files to upload
        for f_name, filename, f_content_type, body in self.files:
            buffer.write(boundary)
            buffer.write(self._attached_file(f_name, filename))
            buffer.write(self._content_type(f_content_type))
            buffer.write(b'\r\n')
            buffer.write(body)
            buffer.write(b'\r\n')

        buffer.write(b'--' + self.boundary + b'--\r\n')
        return buffer.getvalue()


def _print_debug(msg):
    if DEBUG_LEVEL:
        sys.stderr.write(str(msg) + '\n')

_APIS = [
    '/detect',
    '/compare',
    '/search',
    '/faceset/create',
    '/faceset/addface',
    '/faceset/removeface',
    '/faceset/update',
    '/faceset/getdetail',
    '/faceset/delete',
    '/faceset/getfacesets',
    '/face/analyze',
    '/face/getdetail',
    '/face/setuserid'
]

_APIS = [i.split('/')[1:] for i in _APIS]