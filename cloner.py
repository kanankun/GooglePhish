'''
Author: dmdhrumilmistry
Project: github.com/dmdhrumilmistry/GooglePhish
Module: cloner.py
Description: clone webpage
Usage: python cloner.py -u https://google.com/ -n google.html
'''

import argparse
import ipaddress
import os
import socket
from urllib.parse import urlparse

import requests


# VULN-3 fix: private/reserved networks that cloner must never reach
_BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),   # link-local / AWS metadata
    ipaddress.ip_network('100.64.0.0/10'),    # shared address space
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]


def is_safe_url(url: str) -> bool:
    """
    Returns True only when the URL uses http/https and resolves to a
    public IP address — blocks SSRF against internal/private hosts.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ('http', 'https'):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
    except (socket.gaierror, ValueError):
        return False

    for network in _BLOCKED_NETWORKS:
        if ip_obj in network:
            return False

    return True


def clone_page(url: str, page_name: str, save_dir: str) -> bool:
    if not is_safe_url(url):
        print(f'[!] Blocked request to unsafe/private URL: {url}')
        return False

    file_path = os.path.join(save_dir, page_name)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    session = requests.session()
    response = session.get(url, timeout=10)

    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return True

    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='cloner')
    parser.add_argument('-u', '--url', dest='url',
                        help='URL of webpage to clone', type=str, required=True)
    parser.add_argument('-n', '--name', dest='page_name',
                        help='save file name', type=str, required=True)
    parser.add_argument('-d', '--directory', dest='save_dir',
                        help='directory where file will be saved',
                        default=os.path.join(os.getcwd(), 'cloned'))

    args = parser.parse_args()

    if clone_page(url=args.url, page_name=args.page_name, save_dir=args.save_dir):
        print(f'[*] {args.url} cloned successfully → {args.save_dir}')
    else:
        print(f'[!] Failed to clone {args.url}')
