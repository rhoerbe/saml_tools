import argparse
import json
import re

blacklist = {'.ico', '.jpg', '.png', '.css', '.ico'}


def main():
    trace = json.load(args.input)
    print(f"Trace start time: {trace['timestamp']}")
    formatted_lines = list(map(format_request, trace['requests']))
    print(''.join(formatted_lines))


def get_args():
    parser = argparse.ArgumentParser(description='Firefox SAML Trace Reporting')
    parser.add_argument(
        '-i', '--requestid', dest='requestid', action="store_true",
        help='Print requestID')
    parser.add_argument(
        '-s', '--no-static', dest='filter_static', action="store_true",
        help='skip GET for resources ending with .ico, .jpg, .png, .css, ico')
    parser.add_argument(
        '-u', '--url-max-length', dest='url_max_length', default=100,
        type=int, choices=range(20, 1000),
        help='Person adding the input record (current user)')
    parser.add_argument(
        'input', type=argparse.FileType('r', encoding='utf8'),
        help='SAML Trace export')
    return parser.parse_args()


def format_request(req):
    def format_req_id():
        return req['requestId'] + ' ' if args.requestid else ''

    def format_saml():
        saml = req.get('saml', None)
        saml = '\n' + saml if saml else ''
        return re.sub(re.compile('^', re.MULTILINE), ' ' * 5, saml)

    if args.filter_static and \
        req['method'] == 'GET' and \
        req['url'][-4:] in blacklist:
        return ''

    req_id = format_req_id()
    saml = format_saml()
    return (f"{req_id}{req['method']} {req['url'][0:args.url_max_length]} {req['responseStatusText']}{saml}\n")


args = get_args()
main()