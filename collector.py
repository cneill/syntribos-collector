import json
import os.path
import random


cache = None
req_number = 0
req_dir = "reqs/"
hosts = [
    "localhost:9311"
]
header_transforms = {
    "x-auth-token": 'CALL_EXTERNAL|syntribos.extensions.identity.client:get_token_v2:["user"]|',
    "x-project-id": 'deadbeef{0}'.format(random.randint(10000, 99999))
}
all_paths = []


class RequestCache(object):

    def __init__(self):
        self.reqs = []

    @staticmethod
    def has_same_body_vars(req1, req2):
        return set(req1.body_vars.keys()) == set(req2.body_vars.keys())

    @staticmethod
    def has_same_headers(req1, req2):
        return set(req1.headers.keys()) == set(req2.headers.keys())

    @staticmethod
    def has_same_params(req1, req2):
        return set(req1.params.keys()) == set(req2.params.keys())

    def is_same(self, req1, req2):
        same_method = req1.method.upper() == req2.method.upper()
        same_type = req1.fuzzy_type == req2.fuzzy_type
        same_body_vars = self.has_same_body_vars(req1, req2)
        same_headers = self.has_same_headers(req1, req2)
        same_params = self.has_same_params(req1, req2)

        if same_method and same_type:
            return same_body_vars and same_headers and same_params
        else:
            return False

    def add(self, req):
        if req.host not in hosts:
            return
        for cached_req in self.reqs:
            if self.is_same(req, cached_req):
                break
        else:
            self.reqs.append(req)

    def write_all(self):
        for req in self.reqs:
            req.write_file()


class RequestObject(object):

    method = ""
    path = ""
    http_version = ""
    host = ""
    fuzzy_type = "text/plain"

    headers = {}
    params = {}
    url_vars = {}
    body_vars = {}
    raw = ""
    req_number = 0

    def __init__(self, flow):
        global req_number, req_dir, all_paths
        self.req_number = req_number = req_number + 1
        self.parse_request(flow)
        self.construct_raw_request()
        all_paths.append(self.path)

    def __repr__(self):
        return self.raw

    def __str__(self):
        return self.raw

    def parse_request(self, flow):
        self.parse_top_line(flow)
        self.parse_headers(flow.request.data.headers)
        self.parse_data(flow)
        self.host = "{0}:{1}".format(
            flow.request.pretty_host, flow.request.data.port)
        print self.host

    def parse_top_line(self, flow):
        dat = flow.request.data
        self.method = dat.method
        self.path = dat.path
        self.http_version = dat.http_version
        if flow.request.query:
            for var, val in flow.request.query:
                self.params[var] = val
        self.base_path = self.path.split("?")[0]
        print flow.request.path_components

    def parse_headers(self, headers):
        global header_transforms
        blacklist = ["content-length", "host", "user-agent", "connection"]

        for header, val in headers.iteritems():
            header = header.lower()
            if header in header_transforms:
                val = header_transforms[header]
            if header is "content-type":
                self.fuzzy_type = self.check_content_type(val)
            if header not in blacklist:
                # capitalize e.g. "Content-Type"
                name = "-".join(w.capitalize() for w in header.split("-"))
                self.headers[name] = val

    def parse_data(self, flow):
        self.raw_data = flow.request.data.content.strip()

        if flow.request.urlencoded_form:
            for var, val in flow.request.urlencoded_form:
                self.body_vars[var] = val

        elif flow.request.multipart_form:
            for var, val in flow.request.multipart_form:
                self.body_vars[var] = val

        elif self.raw_data:
            try:
                parsed_json = json.loads(self.raw_data)
                for var, val in parsed_json.iteritems():
                    self.body_vars[var] = val
            except Exception:
                pass

    def construct_url_line(self):
        return "{0} {1} {2}\n".format(
            self.method, self.path, self.http_version)

    def construct_headers_lines(self):
        raw = ""
        for header, val in self.headers.iteritems():
            raw += "{0}: {1}\n".format(header, val)

        return raw

    def construct_data_lines(self):
        return "\n{0}\n".format(self.raw_data)

    def construct_raw_request(self):
        self.raw = self.construct_url_line()
        self.raw += self.construct_headers_lines()
        self.raw += self.construct_data_lines()

    @staticmethod
    def check_content_type(header):
        """Returns a signal with info about a response's content type

        :param str header:
        :returns: fuzzy content type
        """

        # LOOKUP MAPS
        known_subtypes = ["xml", "json", "javascript", "html", "plain"]
        known_suffixes = ["xml", "json"]  # RFC6838

        raw_type = header.lower()
        fuzzy_type = ""

        # valid headers should be in form type/subtype
        if "/" not in raw_type:
            raise Exception("Not a valid content type. What happened?")

        # chop off encodings, etc (ex: application/json[; charset=utf-8])
        if ";" in raw_type:
            raw_type = raw_type.split(";")[0]

        _, subtype = raw_type.split("/")

        # if subtype is known, return that (ex: application/[json])
        if subtype in known_subtypes:
            fuzzy_type = subtype

        # check for known 'suffixes' (ex: application/atom+[xml])
        elif "+" in subtype:
            _, suffix = subtype.split("+")
            if suffix in known_suffixes:
                fuzzy_type = suffix

        # fuzzy search for other types (ex: text/[xml]-external-parsed-entity)
        else:
            for s in known_subtypes:
                if s in subtype:
                    fuzzy_type = s
                    break

        if not fuzzy_type:
            fuzzy_type = subtype

        return fuzzy_type.upper()

    def write_file(self):
        file_name = os.path.join(req_dir, "{0}_request_{1}.template".format(
            self.method, self.req_number))
        with open(file_name, "w") as f:
            f.write(self.raw)


def start(context, argv):
    global cache
    cache = RequestCache()


def request(context, flow):
    r = RequestObject(flow)
    print str(r)
    cache.add(r)


def done(context):
    global all_paths
    print "\n".join(all_paths)
    cache.write_all()
