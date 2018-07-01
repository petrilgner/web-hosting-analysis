#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from modules import whois_parser, page_evaluator, webserver_stats as wserver, database as db
from modules.classes import PreparedDomain, EvaluatedPage

# Database query templates
add_result = ("INSERT INTO results "
              "(`domain`, `hosted_rev`,	`hosted_known`,	`hosted_whois`,	`hosted_email`,	`server_httpd`,	`server_xpowerer`,	`server_type`,	`server_ip`, `server_ip_name`, `server_ip_domain`, `dnssec_keyset`,	`domain_holdername`,	`ip_holdername`, `category`, `original_url`, `note`, `https_support`, `ipv6_addr`) "
              "VALUES ('{domain}', '{res_rev}', '{res_known}', '{res_whois}', '{res_email}', '{s_server}', '{s_powerer}', '{s_type}', '{s_ip}', '{s_ip_name}', '{s_ip_domain}', '{dm_keyset}', '{dm_holdername}', '{ip_holdername}', '{category}', '{original_url}', '{note}', '{https_support}', '{ipv6_addr}' )")

delete_result = ("DELETE FROM results WHERE `domain` = '{domain}'")


def is_domain_evaluated(domain):
    """
    Detect if page has been evaluated in past.
    :param domain: Extracted domain name
    :return: Boolean value. True, if page is in db.
    """
    db.exec_query("SELECT COUNT(*) from results where `domain`='{domain}'".format(domain=domain))
    db_result = db.cur.fetchone()
    if db_result is None:
        return False

    return True if db_result[0] else False


def check_https(https_result: dict) -> bool:
    """
    It will check if page output from HTTPS has been OK.
    :param https_result: Result from webserver_stats module
    :return: Boolean value.
    """
    if https_result and https_result.get('status') == 200:
        return True

    return False


def process_domain(domain: PreparedDomain, category: str, reevaluate: bool = False, restoreconn: bool = False,
                   cz_omit: bool = True, subdom_omit: bool = False,
                   output: object = None, db_conn: object = None) -> None:

    """
    It will process given domain. The base evaluation function.
    :param domain: Domain name
    :param category: Category for this page
    :param reevaluate: Reevaluate if found in db
    :param restoreconn: It will call external script in case no WHOIS connectivity
    :param cz_omit: It will omit domain within .cz domain zone
    :param subdom_omit: It will omit domain on 3rd and higher level
    :param output: Reference to opened file to write output log
    :param db_conn: Reference to opened database connection
    :return: 
    """

    if db_conn is None:
        db.open_connection()
        db_conn_created = True
    else:
        db.take_connection(db_conn)
        db_conn_created = False

    print("\n========================================================================\nProcessing page:", domain)

    di = page_evaluator.get_domain_info(domain.domain)

    if not di.get('serverIp'):
        print("[ERROR][NO_DNS]", domain, 'Unable to translate domain. Skipping...')
        return

    if cz_omit:
        if di.get('tld') != 'cz':
            print("[NOTICE][NO_CZ]", domain, "omitted, not in CZ zone.")
            return

    if subdom_omit:
        if di.get('subdomain').lower() not in ['', 'www', None]:
            print("[NOTICE][SUBDOM]", domain, "is subdomain, omitted.")
            return

    if is_domain_evaluated(di.get('baseDomain')):
        if reevaluate:
            db.exec_query(delete_result.format(domain=di.get('baseDomain')))
            db.commit()

        else:
            print("[NOTICE] Been evaluated in past:", domain, "skipping...")
            return

    whois_info = whois_parser.probe_domain(di['baseDomain'], restoreconn)

    if whois_info is {}:
        print("[ERROR][WHOIS_NIC] - no valid response for ", domain)
        return

    # Get WHOIS and GEO data about IP

    try:
        whois_ip_info = whois_parser.probe_ip(di['serverIp'])

    except Exception as e:
        print("[ERROR][WHOIS_IP] for ", di['serverIp'], e)
        return

    server_stats = wserver.probe_server(di['baseDomain'])
    server_stats_https = wserver.probe_server(di['baseDomain'], True)
    https_supported = check_https(server_stats_https)

    if whois_info.get('holderId'):
        contact_info = whois_parser.probe_contact(whois_info.get('holderId'), restoreconn)
    else:
        contact_info = {}

    evaluated = page_evaluator.evaluate_domain(di, whois_info, whois_ip_info)

    # Print given note
    if domain.note:
        print("[DOMAIN-NOTE]", domain.note)

    print("[INFO][DOMAIN] b.dom: {bDomain}, s.IP: {IP}, s.IPv6 {IP6}, s.IP name: {IP_name}".format(
        bDomain=di.get('baseDomain'),
        IP=di.get('serverIp'),
        IP6=di.get('serverIp6'),
        IP_name=di.get('netDomainFull')))

    if whois_info is not {}:
        print("[INFO][CZNIC_WHOIS] holder: {hold}, NS: {nsset}".format(hold=whois_info.get('holderName'),
                                                                       nsset=whois_info.get('nsset')))

    if contact_info is not {}:
        print("[INFO][CZNIC_CONTACT] email: {email}, ident: {ident}".format(email=contact_info.get('email'),
                                                                            ident=contact_info.get('ident')))

    print("[INFO][NET] email: {email}, org: {ident}, GEO {geo}".format(email=whois_ip_info.contact_email,
                                                                       ident=whois_ip_info.get_organization(),
                                                                       geo=whois_ip_info.geo_ip))

    print("[INFO][WEBSRV] stat: {status}, sign: {sign}, HTTPS: {https_sup}".format(status=server_stats.get('status'),
                                                                                   sign=server_stats.get('server'),
                                                                                   https_sup=https_supported))

    print("\n[EVAL][RESULTS] ", evaluated)

    # Write to DB if was given category to store results
    if category:
        db.exec_query(add_result.format(
            domain=di.get('baseDomain'),
            res_rev=evaluated.method_reverse_dns,
            res_known=evaluated.method_known_hoster,
            res_whois=evaluated.method_whois,
            res_email=evaluated.method_email,
            s_server=server_stats.get('server'),
            s_powerer=server_stats.get('x_powerer'),
            s_type=server_stats.get('c_type'),
            s_ip=di.get('serverIp'),
            s_ip_name=di.get('netDomainFull'),
            s_ip_domain=di.get('netDomain'),
            dm_keyset=whois_info.get('keyset'),
            dm_holdername=whois_info.get('holderName'),
            ip_holdername=whois_ip_info.get_organization(),
            category=category,
            original_url=domain.original_url,
            note=domain.note,
            ipv6_addr=di.get('serverIp6'),
            https_support=https_supported

        ))
        db.commit()

    if output is not None or False:
        output.write("{dom}\t{m_wh}\t{m_rd}\t{m_h}\t{m_e}\t{s_ip}\t{d_hold}\t{ip_org}\t{ip_em}\n".format(
            dom=di.get('domain'),
            m_wh=EvaluatedPage.bool2switcher(evaluated.method_whois),
            m_rd=EvaluatedPage.bool2switcher(evaluated.method_reverse_dns),
            m_h=EvaluatedPage.bool2switcher(evaluated.method_known_hoster),
            m_e=EvaluatedPage.bool2switcher(evaluated.method_email),
            s_ip=di.get('serverIp'),
            d_hold=whois_info.get('holderName'),
            ip_org=whois_ip_info.get_organization(),
            ip_em=whois_ip_info.contact_email

        ))

    if db_conn_created is True:
        db.close_connection()


if __name__ == '__main__':

    # Parse command line args
    parser = argparse.ArgumentParser(description='Process given website url ')

    parser.add_argument('category', help='Specifies the category of pages in given file, will save to results DB ',
                        type=str, metavar='CAT')
    parser.add_argument('--restoreconn', help='Restore connection to WHOIS automatically', action='store_true')
    parser.add_argument('--reevaluate', help='Overwrite the result in DB', action='store_true')
    parser.add_argument('--noczomit', help='Don\'t omit not CZ domains', action='store_true')
    parser.add_argument('domain', metavar='DOMAIN', type=str, help='domain to process', default='')

    args = parser.parse_args()

    process_domain(PreparedDomain(args.domain), args.category, args.reevaluate, args.restoreconn, not args.noczomit)
