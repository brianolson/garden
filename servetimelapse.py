#!/usr/bin/python3
#
# manage output of raspistill command like:
# raspistill -tl 30000 -n -dt -o /mnt/usb128/timelapse/i%d.jpg -t 0 -w 1920 -h 1080 -vf -hf

import glob
import json
import os
import sys
import threading
import time
from wsgiref.simple_server import make_server
import wsgiref.util


import reader
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

def serveLatestImage(environ, start_response):
    imgPath = sorted(glob.glob(os.path.join(timelapseRootPath, 'i*.jpg')), reverse=True)[0]
    return serveImage(environ, start_response, imgPath, noCache=True)


class GardenServer(object):
    def __init__(self, tempHumid):
        self.tempHumid = tempHumid

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        if path.startswith('/list/'):
            return self.serveList(environ, start_response)

        if path.startswith('/i/'):
            imgPath = os.path.join(timelapseRootPath, path[3:])
            return serveImage(environ, start_response, imgPath)

        if path == '/latest' or path == '/latest/' or path == '/current' or path == '/current/':
            return serveLatestImage(environ, start_response)

        if path == '/th.js':
            return self.serveTempHumid(environ, start_response)

        return self.serveList(environ, start_response, limit=50)

    def serveTempHumid(self, environ, start_response):
        start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
        timeTempHumid = self.tempHumid.getLatest()
        out = {}
        if timeTempHumid is not None:
            out['timestamp'] = timeTempHumid.when
            out['tempHumids'] = timeTempHumid.tempHumids
        yield json.dumps(out).encode('utf8')

    def serveList(self, environ, start_response, limit=None):
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
        yield b'''<!DOCTYPE html>
<html>
<head>
	<title>bpi3 timelapse</title>
	<meta charset="utf-8" />
</head>
<body style="background-color:#fff;">
'''
        timeTempHumid = self.tempHumid.getLatest()
        if timeTempHumid is not None:
            yield ('<div>{:0.1f} °C {:0.1f} °F {:0.1f}% humidity</div>\n'.format(timeTempHumid.degC(), timeTempHumid.degF(), timeTempHumid.pctHumid())).encode('utf8')
        yield b'<div><a href="/current">current</a></div><div><img src="/current" width="480" height="270" /></div>\n'
        count = 0
        for imgPath in sorted(filter(lambda x: x.endswith('.jpg'), os.listdir(timelapseRootPath)), reverse=True):
            count += 1
            yield ('<div><a href="/i/{fname}">{fname}</a></div>\n'.format(fname=imgPath)).encode('utf8')
            if (limit is not None) and (count > limit):
                yield b'<div><a href="/list/" style="font-size: 130%">...</a></div>\n'
                break
        yield b'</body></html>\n'


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage:\n\treader.py /dev/cu.{port}\n")
        sys.exit(1)
    th = reader.Reader(sys.argv[1])
    garden = GardenServer(th)
    httpd = make_server('', 8000, garden)
    print("Serving on port 8000...")

    # Serve until process is killed
    #httpd.serve_forever()

    serve_thread = threading.Thread(target=httpd.serve_forever)
    sensor_thread = threading.Thread(target=th.run)
    serve_thread.start()
    sensor_thread.start()


if __name__ == '__main__':
    main()
