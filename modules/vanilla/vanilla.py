  

from google.appengine.api import users
from models.models import Student
from models import custom_modules
from common import tags
from common import schema_fields
from xml.etree import cElementTree
from controllers import sites
from controllers import utils
from models.config import ConfigProperty
from models.counters import PerfCounter
from models import custom_modules
from models import models
from models import transforms
from controllers import sites
import logging

import base64
import binascii
import hashlib
import hmac
import json
import urllib
import webapp2
import cgi
import os
import urllib2
import urlparse


def error(code, message):
    """Convenience method that returns a dict representing an error.
    :param code: The code of the error.
    "param message: A user-readable message for the error.
    """
    return {
        'error': code,
        'message': message,
    }

class VanillaForumsTag(tags.BaseTag):
   

    @classmethod
    def name(cls):
        return 'Vanilla Forum'

    @classmethod
    def vendor(cls):
        return 'fi_ncsu'

    def render(self, node, unused_handler):
        """Embed just a <script> tag that will in turn create an <iframe>."""

        category = node.attrib.get('forum-category')
        course = sites.get_course_for_current_request().get_environ()['course']
        url = course['VANILLA_EMBED_URL']
        return cElementTree.XML(
            """
<div style='width: 750px;'>
  <script>window.location.hash = '/categories/%s';</script><script type="text/javascript" src="//%s/js/embed.js"></script><noscript>Please enable JavaScript to view discussions.</noscript>
</div>""" % (
    cgi.escape(category), cgi.escape(url)))

    def get_schema(self, unused_handler):

        reg = schema_fields.FieldRegistry('VanillaForums')
        reg.add_property(
            schema_fields.SchemaField(
                'forum-category', 'Forum Category ID', 'string',
                optional=False,
                description=('Provide the Forum Category ID'
                             '"(from when forum was created)')))

        return reg



def get_jsconnect_string(user, request, client_id, secret_key, secure=True):
    """Returns a JSONP formatted string suitable to be consumed by jsConnect. This is
    usually the only method you need to call in order to implement jsConnect.

    :param user:        A map containing the user information. The map should have the following keys:
        - uniqueid:         An ID that uniquely identifies the user in your system. This value should never change for a given user.
    :param request:     A map containing the query string for the current request. You usually just pass in request.getParameterMap().
    :param client_id:   The client ID for your site. This is usually configured on Vanilla's jsConnect configuration page.
    :param secret_key:  The secret for your site. This is usually configured on Vanilla's jsConnect configuration page.
    :param secure:      Whether or not to check security on the request. You can leave this false for testing, but you should make it true in production.

    :return:            The JSONP formatted string representing the current user.
    """
    vanilla_ts = int(request.get('timestamp', 0))
    current_ts = get_ts()

    sec_error = None

    if secure:
        if not 'client_id' in request:
            sec_error = error("invalid_request", "The client_id parameter is missing."+client_id)
        elif request['client_id'] != client_id:
            sec_error = error("invalid_client", "Unknown client " + request['client_id'] + ".  Expected: "+client_id)
        elif not 'timestamp' in request and not 'signature' in request:
            if user is not None and len(user) != 0:
                sec_error = {"name": user["name"], "photourl": user.get("photourl", "")}
            else:
                sec_error = {"name": "", "photourl": ""}
        elif vanilla_ts == 0:
            sec_error = error("invalid_request", "The timestamp is missing or invalid.")
        elif not 'signature' in request:
            sec_error = error("invalid_request", "The signature is missing.")
        elif abs(current_ts - vanilla_ts) > 30 * 60:
            sec_error = error("invalid_request", "The timestamp is invalid.")
        else:  # make sure the timestamp's signature checks out.
            vanilla_sig = hashlib.md5(str(vanilla_ts) + secret_key).hexdigest()
            if vanilla_sig != request["signature"]:
                sec_error = error("access_denied", "Signature invalid. "+vanilla_sig+"...."+request["signature"])

    result = {}

    if sec_error is not None:
        result = sec_error
    elif user is not None and len(user) != 0:
        result = dict(user)
        sign_jsconnect_string(result, client_id, secret_key, True)
    else:
        result["name"] = ""
        result["photourl"] = ""

    json_encoded = json.dumps(result)

    if not 'callback' in request:
        return json_encoded
    else:
        return "{0}({1})".format(request['callback'], json_encoded)


def sign_jsconnect_string(data, client_id, secret_key, set_data=False):
    """Sign a jsConnect response. Responses are signed so that the site requesting the
    response knows that this is a valid site signing in.

    :param data:        The data to sign.
    :param client_id:   Client ID of the site.
    :param secret_key:  Secret key of the site.
    :param setData:     Whether or not to add the signature information to the data.

    :return:            The computed signature of the data as a hex string.
    """
    # sort data, set key to lowercase, encode key=value as UTF-8, url encode
    sorted_data = [(k.lower().encode('UTF-8'), data[k].encode('UTF-8')) for k in sorted(data.keys())]
    sig_str = urllib.urlencode(sorted_data)
    signature = hashlib.md5(sig_str + secret_key).hexdigest()

    if set_data:
        data['client_id'] = client_id
        data['signature'] = signature

    return signature


def get_ts():
    """Returns the current timestamp of the server, suitable for synching with the site."""
    from time import time
    return int(time())


class AuthHandler(webapp2.RequestHandler):

    def get(self):
        param_map = {}
        for k in self.request.arguments():
            param_map[k] = self.request.get(k)
        client_id = param_map.get('client_id', 0)

        logging.debug("vanilla request: " + str(param_map))

        user = users.get_current_user()

        logging.debug(str(user))

        if user:
            student = Student.get_enrolled_student_by_email(user.email())
            user = {
                "name": student.name,
                "email": user.email(),
                "uniqueid": user.user_id(),
                "photourl": "",
            }
        course = self.app_context.get_environ()['course']

        client_id = course['VANILLA_CLIENT_ID']
        secret_key = course['VANILLA_SECRET_KEY']

        jsconn_str = get_jsconnect_string(user, param_map, client_id, secret_key)

        logging.debug("mooc-ed response: " + jsconn_str)

        self.response.out.write(jsconn_str)


def api_request(path, self, ext='JSON', method="GET", params=None):

    course = self.app_context.get_environ()['course']

    target_url = course['VANILLA_API_URL']+path+'.'+ext+'?access_token='+VANILLA['api_token']

    if method == "GET":
        target_url += '&' + urllib.urlencode(params)
        return urllib2.Request(target_url)
    else:
        return urllib2.Request(target_url, json.dumps(urllib.urlencode(params)))


def register_module():
    """Registers this module in the registry."""

    tags.Registry.add_tag_binding('vanilla-forum', VanillaForumsTag)
    # setup routes
    vanilla_handlers = [
          ('/vanilla_auth.json', AuthHandler),
        ]

    global custom_module
    custom_module = custom_modules.Module(
        'Vanilla Forums',
        'Integration with the Vanilla Forums application.',
        [],
        vanilla_handlers)
    return custom_module


def unregister_module():
    """Unregisters this module in the registry."""

    # set the page intializer to default.
   # utils.PageInitializerService.set(utils.DefaultPageInitializer)

    return custom_modules
