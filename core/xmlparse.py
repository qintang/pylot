#
#    Copyright (c) 2007-2009 Corey Goldberg (corey@goldb.org)
#    License: GNU GPLv3
#
#    This file is part of Pylot.
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.  See the GNU General Public License 
#    for more details.
#

import sys
from string import Template
try:
    import xml.etree.ElementTree as etree
except ImportError:
    sys.stderr.write('ERROR: Pylot was unable to find the XML parser.  Make sure you have Python 2.5+ installed.\n')
    sys.exit(1)
from engine import Request
from tenjinengine import TenjinEngine
from tenjinengine import saveStrTemaplate 


def load_xml_string_cases(tc_xml_blob):
    # parse xml and load request queue with core.engine.Request objects
    # variant to parse from a raw string instead of a filename
    dom = etree.ElementTree(etree.fromstring(tc_xml_blob))
    cases = load_xml_cases_dom(dom)
    return cases


def load_xml_cases(tc_xml_filename):
    # parse xml and load request queue with corey.engine.Request objects
    # variant to load the xml from a file (the default shell behavior)
    dom = etree.parse(tc_xml_filename)
    cases = load_xml_cases_dom(dom)
    return cases

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    import mimetypes
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def load_xml_cases_dom(dom):
    # load cases from an already-parsed XML DOM
    cases = []
    param_map = {}
    for child in dom.getiterator():
        if child.tag != dom.getroot().tag and child.tag == 'param':
            name = child.attrib.get('name')
            value = child.attrib.get('value')
            param_map[name] = value
        if child.tag != dom.getroot().tag and child.tag == 'case':
            req = Request()
            repeat = child.attrib.get('repeat')
            if repeat:
                req.repeat = int(repeat)
            else:
                req.repeat = 1
            # support tenjin template engine
            tenjintag = child.attrib.get('tenjin')
            if tenjintag and tenjintag.lower() == 'true':
                req.tenjin = True

            for element in child:
                if element.tag.lower() == 'url':
                    req.url_str = element.text
                if element.tag.lower() == 'method': 
                    req.method = element.text
                if element.tag.lower() == 'body':
                    file_payload = element.attrib.get('file')
                    if file_payload:
                        #req.body = open(file_payload, 'rb').read()
                        content_type, body = encode_multipart_formdata([],[('file',file_payload.split("/")[-1],open(file_payload, 'rb').read())])
                        req.add_header('content-type',content_type)
                        req.add_header('content-length', str(len(body)))
                        req.body_str = body
                        req.tenjin = False
                    else:
                        req.body_str = element.text
                if element.tag.lower() == 'verify': 
                    req.verify = element.text
                if element.tag.lower() == 'verify_negative': 
                    req.verify_negative = element.text
                if element.tag.lower() == 'timer_group': 
                    req.timer_group = element.text
                if element.tag.lower() == 'add_header':
                    # this protects against headers that contain colons
                    splat = element.text.split(':')
                    x = splat[0].strip()
                    del splat[0]
                    req.add_header(x, ''.join(splat).strip())
                if element.tag.lower() == 'add_header_tenjin':
                    req.add_header_tenjin(TenjinEngine().renderFunction(saveStrTemaplate(element.text)))
                        
            req = resolve_parameters(req, param_map)  # substitute vars
            # proces tenjin
            if req.tenjin:
                req.body = TenjinEngine().renderFunction(saveStrTemaplate(req.body_str))
                req.url = TenjinEngine().renderFunction(saveStrTemaplate(req.url_str))
            else:
                req.body = lambda : req.body_str
                req.url = lambda : req.url_str
            cases.append(req)
    return cases


def resolve_parameters(req, param_map):
    # substitute variables based on parameter mapping
    req.url_str = Template(req.url_str).substitute(param_map)
    req.body_str = Template(req.body_str).substitute(param_map)
    for header in req.headers:
        req.headers[header] = Template(req.headers[header]).substitute(param_map)
    return req
