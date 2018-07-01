#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from modules import database


def print_pages_webhoster(webhoster, stats=False):

    if stats:

        database.print_query_result("SELECT COUNT(*) as 'Pages count', "
                                    "COUNT(DISTINCT server_ip) as 'Servers count', "
                                    "(COUNT(*)/COUNT(DISTINCT server_ip)) as 'Average pages on server' "
                                    "FROM results"
                                    " WHERE server_ip_name LIKE '%{}' ".format(webhoster))

    else:
        print("Hosted pages:")
        database.print_query_result(
            "SELECT domain, server_ip_name as 'Server domain name', server_ip, category from results "
            "WHERE server_ip_name LIKE '%{}%' "
            "ORDER by domain".format(webhoster))

        print("\nUnique servers:")
        database.print_query_result("SELECT server_ip_name, server_ip from results "
                                    "WHERE server_ip_name LIKE '%{}' "
                                    "GROUP by server_ip".format(webhoster))


def print_pages_ip(ip, stats=False):
    # It will match pattern like 10.0.0.0/8 or 10.0.0.1.
    m = re.match(
        r'^(?P<addr>(?P<b1>\d{1,3})\.(?P<b2>\d{1,3})\.(?P<b3>\d{1,3})\.(?P<b4>\d{1,3}))(\/(?P<mask>\d{1,2}))?$', ip)

    if not m:
        print("Incorrect input. Use input like 10.0.0.0/8 or 10.0.0.1.")
        return

    input_m = m.groupdict()
    addr = input_m.get('addr')
    mask = int(input_m.get('mask'))

    if not mask:
        query = "= '{}'".format(addr)

    else:
        if mask == 24:
            query = "LIKE '{}.{}.{}.%'".format(input_m.get('b1'), input_m.get('b2'), input_m.get('b3'))
        if mask == 16:
            query = "LIKE '{}.{}.%.%'".format(input_m.get('b1'), input_m.get('b2'))
        if mask == 8:
            query = "LIKE '{}.%.%.%'".format(input_m.get('b1'))

    if stats:

        database.print_query_result(
            "SELECT COUNT(*) as 'Pages on specified server/net' FROM results "
            "WHERE server_ip {} ".format(query))

    else:
        database.print_query_result(
            "SELECT domain, server_ip as 'Server IP', server_ip_name as 'Server domain name' from results "
            "WHERE server_ip {}"
            "ORDER by domain".format(query))

        print("Hosted pages:")
        database.print_query_result(
            "SELECT domain, category from results "
            "WHERE server_ip LIKE '%{}%' "
            "ORDER by domain".format(ip))


if __name__ == '__main__':
    # Argument parsing section
    parser = argparse.ArgumentParser(description='Print list of detected page on specified webserver. ')

    parser.add_argument('query', help='IP/Network/webhoster query', type=str)
    parser.add_argument('--summary', help='Print summary', action='store_true')
    parser.add_argument('--webhoster', help='Print pages hosted on specified webhosting', action='store_true')
    args = parser.parse_args()
    database.open_connection()
    if args.webhoster:
        print_pages_webhoster(args.query, args.summary)
    else:
        print_pages_ip(args.query, args.summary)

    database.close_connection()
