import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', metavar='PATH', dest='output', default=None)
    parser.add_argument('--format', default='mp3')
    parser.add_argument('-y', dest='yes', action='store_true')
    parser.add_argument('input')

    args = parser.parse_args()
    try:

        src = args.input
        f_name, f_ext = os.path.splitext(os.path.basename(src))
        fmt = args.format

        path = args.output if args.output else os.path.dirname(os.path.abspath(src))
        dest = os.path.join(path, '.'.join([f_name, fmt]))

        print(f'[+] Converting {f_ext.lstrip(".")} to {fmt}')

        os.system(f'ffmpeg -i "{src}" "{dest}" -hide_banner')

        opt = 'y' if args.yes else input(
            f'Do you want to remove the source file with name "{os.path.basename(src)}"?[y/N] ')
        if opt == 'y':
            os.remove(src)

        print('\n[+] Done')
    except Exception as e:
        print(e)
