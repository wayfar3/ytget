import argparse
import html
import os
import re
import shutil
import subprocess
import sys

try:
    from pytube import Stream, YouTube, Playlist
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'pytube3'])
    print("Oops! Please try again.")
    sys.exit(-1)


class YoutubeManager:

    def __init__(self, url):
        self._yt, self._streams = self._fetch_all(url)
        self._sel = None

    @staticmethod
    def _fetch_all(url):
        results = []
        yt = YouTube(url)
        all_streams = yt.streams
        for s in all_streams:
            quality = s.resolution if s.resolution else s.abr
            if quality:
                results.append((
                    s,
                    {
                        'itag': s.itag,
                        'type': s.type,
                        'format': s.mime_type.split('/')[-1],
                        'quality': quality,
                        'size': '{:.2f}MB'.format(s.filesize / 1048576),
                        'progressive': 'available' if s.is_progressive else ''
                    }
                ))

        return yt, results

    @property
    def filename(self):
        return self._sanity_filename(self.title)

    @property
    def title(self):
        return self._yt.title

    @property
    def streams(self):
        return self._streams

    @property
    def selection(self):
        return self._sel

    @staticmethod
    def _sanity_filename(s):
        s = html.unescape(s)
        return re.sub(r'[\/:*?."<>|#]+', '', s)

    def _only_video(self):
        res = []
        for s in self.streams:
            if s[1]['type'] == 'video':
                res.append(s)
        return sorted(res, key=lambda a: int(a[1]['quality'][:-1]), reverse=True)

    def _only_audio(self):
        res = []
        for s in self.streams:
            if s[1]['type'] == 'audio':
                res.append(s)
        return sorted(res, key=lambda a: int(a[1]['quality'][:-4]), reverse=True)

    def best_audio(self):
        for s in self._only_audio():
            if s[1]['format'] == 'mp4':
                self._sel = s
                return self

    def best_video(self):
        for s in self._only_video():
            if s[1]['format'] == 'mp4' and s[1]['progressive'] == 'available':
                self._sel = s
                return self

    def stream_at(self, itag):
        for s in self.streams:
            if s[1]['itag'] == itag:
                self._sel = s
                break
        return self

    def download(self, path, on_progress=None):
        if not self.selection:
            raise Exception('cannot found any stream')

        if on_progress:
            # function=on_progress,args=(stream: Stream, chunk: bytes, bytes_remaining: int)
            self._yt.register_on_progress_callback(on_progress)

        self._sel[0].download(path, self._sanity_filename(self.title))


def render_progress_bar(bytes_recv, filesize, ch='\u258c', scale=0.85):
    cols = shutil.get_terminal_size().columns
    max_width = int(cols * scale)
    filled = int(round(max_width * bytes_recv / float(filesize)))
    remaining = max_width - filled
    progress_bar = ch * filled + ' ' * remaining
    percent = int(round(100.0 * bytes_recv / float(filesize), 1))
    print('\r {p}% |{ch}| {recv:.3f}MB/{size:.3f}MB '.format(ch=progress_bar,
                                                             p=percent, recv=bytes_recv / 1048576,
                                                             size=filesize / 1048576), end='\r')
    sys.stdout.flush()


def on_progress(stream: Stream, chunk: bytes, bytes_remaining: int):
    filesize = stream.filesize
    bytes_recv = filesize - bytes_remaining
    render_progress_bar(bytes_recv, filesize, scale=0.1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-d', metavar='DIR')
    parser.add_argument('-s', action='store_true')
    parser.add_argument('-a', action='store_true')
    parser.add_argument('-b', action='store_true')
    parser.add_argument('-n', type=int)

    args = parser.parse_args()

    url = args.url.strip()

    if not url or 'youtube' not in url:
        parser.print_help()
        return

    path = os.path.dirname(os.path.realpath(__file__)) if not args.d else args.d

    print('[+] loading video... ', end='')
    try:
        mgr = YoutubeManager(url)

        print('done')
        print('[i] {}'.format(mgr.title))

        if args.s:

            header = ['itag', 'type', 'format', 'quality', 'size', 'progressive']
            print('{h[0]:10}{h[1]:10}{h[2]:10}{h[3]:10}{h[4]:10}{h[5]:10}'.format(h=header))
            print('-' * 60)
            for stream in mgr.streams:
                s = stream[1]
                print(
                    '{:<10}{:10}{:10}{:10}{:10}{:10}'.format(s['itag'], s['type'], s['format'], s['quality'],
                                                             s['size'],
                                                             s['progressive']))

            return

        if args.a:
            mgr.best_audio()

        if args.b:
            mgr.best_video()

        if args.n:
            mgr.stream_at(args.n)

        print('[+] downloading... ')
        mgr.download(path, on_progress)

        print('\ndone')
    except Exception as e:
        print('fail')
        print('[-] {}'.format(e))


if __name__ == '__main__':
    main()