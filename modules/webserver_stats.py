#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import urllib3
import requests

if __name__ == '__main__':
    import formatter
else:
    from modules import formatter

urllib3.disable_warnings()


def probe_server(url, force_https=False):
    protos = {
        True: 'https://',
        False: 'http://'
    }

    try:

        r = requests.get(protos[force_https] + url, timeout=2)

    except (requests.ConnectTimeout, requests.Timeout):
        return {'status': 'timeout'}
    except (requests.ConnectionError, requests.TooManyRedirects):
        return {'status': 'conn_err'}
    except Exception:
        return {'status': 'generic_error'}

    return {
        'status': r.status_code or '',
        'reason': r.reason or '',
        'server': r.headers.get('Server') or '',
        'x_powerer': r.headers.get('X-Powered-By') or '',
        'c_type': r.headers.get('Content-Type') or ''
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gets basic stats from an webserver. ')
    parser.add_argument('-s', help='Use only HTTPS', action='store_true')
    parser.add_argument('url', help='Domain or URL to perform query')

    args = parser.parse_args()
    formatter.print_dict(probe_server(args.url, args.s))
