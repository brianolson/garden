#!/usr/bin/python3
#
# manage output of raspistill command like:
# raspistill -tl 30000 -n -dt -o /mnt/usb128/timelapse/i%d.jpg -t 0 -w 1920 -h 1080 -vf -hf

import glob
import os
import time
from wsgiref.simple_server import make_server
import wsgiref.util

timelapseRootPath = '/mnt/usb128/timelapse'

# Every WSGI application must have an application object - a callable
# object that accepts two arguments. For that purpose, we're going to
# use a function (note that you're not limited to a function, you can
# use a class for example). The first argument passed to the function
# is a dictionary containing CGI-style environment variables and the
# second variable is the callable object (see PEP 333).


# there must be a good standard library function for this somewhere?
def http_date(t):
    # Sun, 06 Nov 1994 08:49:37 GMT
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(t))

def serveImage(environ, start_response, imgPath, noCache=False):
    try:
        st = os.stat(imgPath)
        headers = [('Content-type', 'image/jpeg'),
                   ('Content-length', str(st.st_size))]
        if noCache:
            headers.append(('Cache-Control', 'no-cache'))
        else:
            headers.append(('Last-Modified', http_date(st.st_mtime)))
        start_response('200 OK', headers)
        return wsgiref.util.FileWrapper(open(imgPath, 'rb'))
    except FileNotFoundError as e:
        start_response('404', [('Content-type', 'text/plain; charset=utf-8')])
        return [b'not found']

def serveList(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
    yield b'''<!DOCTYPE html>
<html>
<head>
	<title>bpi3 timelapse</title>
	<meta charset="utf-8" />
</head>
<body style="background-color:#fff;">
<div><a href="/current">current</a></div>
'''
    for imgPath in sorted(filter(lambda x: x.endswith('.jpg'), os.listdir(timelapseRootPath)), reverse=True):
        yield ('<div><a href="/i/{fname}">{fname}</a></div>\n'.format(fname=imgPath)).encode('utf8')
    yield b'</body></html>\n'

def serveLatestImage(environ, start_response):
    imgPath = sorted(glob.glob(os.path.join(timelapseRootPath, 'i*.jpg')), reverse=True)[0]
    return serveImage(environ, start_response, imgPath, noCache=True)

def hello_world_app(environ, start_response):
    path = environ['PATH_INFO']
    if path.startswith('/list/'):
        return serveList(environ, start_response)

    if path.startswith('/i/'):
        imgPath = os.path.join(timelapseRootPath, path[3:])
        return serveImage(environ, start_response, imgPath)

    if path == '/latest' or path == '/latest/' or path == '/current' or path == '/current/':
        return serveLatestImage(environ, start_response)

    return serveList(environ, start_response)
    
    # status = '200 OK'  # HTTP Status
    # headers = [('Content-type', 'text/plain; charset=utf-8')]  # HTTP Headers
    # start_response(status, headers)

    # # The returned object is going to be printed
    # return [b"Hello World"]

httpd = make_server('', 8000, hello_world_app)
print("Serving on port 8000...")

# Serve until process is killed
httpd.serve_forever()

# import http.server

# timelapseRootPath = '/mnt/usb128/timelapse'

# class TimelapseServerRequestHandler(http.server.BaseHTTPRequestHandler):
#     def do_GET():
#         pass

# host = '0.0.0.0'
# port = 8080

# server = http.server.HTTPServer( (host, port), TimelapseServerRequestHandler)
# server.serve_forever()
