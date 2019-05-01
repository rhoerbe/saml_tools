import argparse
import json
import re
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

filter_static_ext = {'.ico', '.jpg', '.png', '.css', '.ico'}


def main():
    trace = json.load(args.input)
    print(f"Trace start time: {trace['timestamp']}")
    formatted_lines = list(map(format_request, trace['requests']))
    print(''.join(formatted_lines))


def get_args():
    parser = argparse.ArgumentParser(description='Firefox SAML Trace Reporting')
    parser.add_argument(
        '-c', '--set-cookie', dest='set_cookie', action="store_true",
        help='Print response cookies')
    parser.add_argument(
        '-e', '--extra-resp-line', dest='extra_resp_line', action="store_true",
        help='Print response in extra line')
    parser.add_argument(
        '-i', '--requestid', dest='requestid', action="store_true",
        help='Print requestID')
    parser.add_argument(
        '-m', '--max-length', dest='max_length', default=100,
        type=int, choices=range(10, 1000),
        help='Remove arg and cookie values if longer than this value')
    parser.add_argument(
        '-s', '--no-static', dest='filter_static', action="store_true",
        help='skip GET for resources ending with .ico, .jpg, .png, .css, ico')
    parser.add_argument(
        'input', type=argparse.FileType('r', encoding='utf8'),
        help='SAML Trace export')
    return parser.parse_args()


def format_request(req):
    def format_req_id(reqid: str, reqid_opt: bool):
        return  reqid + ' ' if reqid_opt else ''

    def format_response(req: dict, extra_line: bool, reqid: str, maxlen: int):
        nl = '\n' + reqid if extra_line else ''
        http_status = req['responseStatusText'][9:]
        try:
            set_cookie_header: dict = list(filter(lambda x: x['value'] if x['name'] == 'Set-Cookie' else None, req['responseHeaders']))[0]
        except IndexError:
            return nl + '  ' + http_status
        simple_cookie = SimpleCookie()
        simple_cookie.load(set_cookie_header['value'])
        for k in simple_cookie:
            v = simple_cookie[k].value
            if len(v) > maxlen:
                simple_cookie[k].set(k, '[..]', '[..]')
            if len(simple_cookie[k].key) > 40:
                simple_cookie[k].set(k[:40], v, v)
        cookies_idented = re.sub(re.compile('^Set-', re.MULTILINE), ' ' * 7, str(simple_cookie))
        cookies_idented = re.sub(re.compile('Cookie: samesite=', re.MULTILINE), '        samesite= ', cookies_idented)
        return nl + '  ' + http_status + '\n' + cookies_idented

    def indent_saml(saml):
        saml_nl = '\n' + saml if saml else ''
        return re.sub(re.compile('^', re.MULTILINE), ' ' * 5, saml_nl)

    def shorten_url(url, maxlen):
        def shorten_query_arg(arg: tuple):
            key: str = arg[0]
            values: list = arg[1]
            qa = ''
            for v in values:
                v_short = v if len(v) < 10 else '[..]'
                qa += key + '=' + v_short
            return qa

        if len(req['url']) < maxlen:
            return req['url']
        else:
            u = urlparse(url)
            params = ';' + u.params if u.params else ''
            query_args = parse_qs(u.query)
            query_shortened = '  '.join(list(map(shorten_query_arg, query_args.items())))
            return u.netloc + u.path + params + query_shortened

    if args.filter_static and \
        req['method'] == 'GET' and \
        req['url'][-4:] in filter_static_ext:
        return ''
    else:
        req_id = format_req_id(req['requestId'], args.requestid)
        saml = indent_saml(req.get('saml', None))
        url = shorten_url(req['url'], args.max_length)
        resp = format_response(req, args.extra_resp_line, req_id, args.max_length)
        return (f"{req_id}{req['method']} {url}{saml} {resp}\n")


args = get_args()
main()
