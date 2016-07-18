import http.server
import subprocess
import os

from youtube_dl.extractor import youtube
from youtube_dl.utils import sanitized_Request
from youtube_dl.compat import (
    compat_basestring,
    compat_urllib_request
)
from youtube_dl.cache import Cache
from config import cfgoptions

class Downloader(object):
    params = None
    _opener = None
    _socket_timeout = None

    def __init__(self):
        self.params = {'prefer_insecure': False}
        self.cache = Cache(self)

    def to_screen(self, string, skip_eol=False):
        print(string)

    def report_warning(self, message):
        print(message)

    def urlopen(self, req):
        self._socket_timeout = 600
        if isinstance(req, compat_basestring):
            req = sanitized_Request(req)
        opener = compat_urllib_request.build_opener()
        self._opener = opener
        return self._opener.open(req, timeout=self._socket_timeout)

class MyHandler(http.server.BaseHTTPRequestHandler):
    def _getav(self, url):
        yie = youtube.YoutubeIE()
        downloader = Downloader()
        yie.set_downloader(downloader)
        result = yie._real_extract(url)
        if result:
            vlist = []
            alist = []
            for entry in result['formats']:
                if 'acodec' in entry:
                    if entry['acodec'] == 'none':
                        if 'height' in entry:
                            if entry['height'] is not None:
                                if entry['ext'] == 'mp4':
                                    vlist.append(entry)
                    else:
                        if 'abr' in entry:
                            if entry['abr'] is not None:
                                if entry['ext'] == 'm4a':
                                    alist.append(entry)
            if len(vlist) > 0 and len(alist) > 0:
                vlist.sort(key=lambda t: t['height'])
                alist.sort(key=lambda t: t['abr'])
                return [vlist[-1]['url'], alist[-1]['url']]
            else:
                return False
        else:
            return False

    def _handlepath(self, vid):
        baseurl = 'https://www.youtube.com/watch?v='
        url = baseurl + vid
        avurls = self._getav(url)
        if not avurls:
            return
        cmd = [cfgoptions.vlc, '--quiet', '--sout-mux-caching=9000', avurls[0], '--input-slave=' + avurls[1]]
        cmd.append('-I dummy')
        # cmd.append('--dummy-quiet')
        cmd.append('--sout')
        cmd.append(cfgoptions.preset_remux)
        cmd.append('vlc://quit')
        handle = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ)
        while handle.poll() is None:
            try:
                buffer = handle.stdout.read(188)
                if not buffer:
                    break
                self.wfile.write(buffer)
            except:
                handle.kill()
                return
        handle.kill()
        return

    def do_GET(self):
        if self.path[1:8] == 'youtube':
            self.send_response(200)
            self.send_header("Content-type", "video/x-flv")
            self.end_headers()
            self._handlepath(self.path[9:])
        return

    def do_HEAD(self):
        if self.path[1:8] == 'youtube':
            self.send_response(200)
            self.send_header("Content-type", "video/x-flv")
            self.end_headers()
        return


def main():
    if not os.path.isfile(cfgoptions.vlc):
        print('vlc not found.')
        return
    try:
        server = http.server.HTTPServer((cfgoptions.host, cfgoptions.port), MyHandler)  # TODO: add multi threading
        print('Started http server')
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()
    return


if __name__ == '__main__':
    main()
