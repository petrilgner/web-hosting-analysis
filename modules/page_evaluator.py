import socket
import dns.resolver
import re
from difflib import SequenceMatcher

from modules import database as db, urltools
from modules.classes import IPWhoisResult, EvaluatedPage

SIMILARITY_THRESHOLD = 0.7


def strip_company_name(company_name):
    return re.sub('\s?(LLC|Limited|(,?\s?(s\.r\.o\.|a\.s\.|S\.r\.l\.|s\.p\.|z\.s\.|v\.o\.s\.|k\.s\.)))$', '',
                  company_name)


def negate_exp(exp: bool) -> bool:
    return None if exp is None else not exp


def is_similar_string(str1: str, str2: str) -> bool:
    ratio = SequenceMatcher(None, str1, str2).ratio()
    print("[DEBUG][Comp-sim]: ", str1, "\t", str2, "\n\t Ratio: ", round(ratio, 2), "\n")
    return True if ratio > SIMILARITY_THRESHOLD else False


def evaluate_exp(exp1, exp2):
    if exp1 is None:
        return None

    return exp1 == exp2


def evaluate_domain(domain_info: dict, domain_whois: dict, network_whois: IPWhoisResult) -> EvaluatedPage:
    evaluation_res = EvaluatedPage(domain=domain_info['baseDomain'],
                                   method_reverse_dns=negate_exp(
                                       is_reverse_host_equal(domain_info['netDomain'], domain_info['baseDomain'])),
                                   method_whois=negate_exp(is_whois_info_equal(domain_whois, network_whois)),
                                   method_email=negate_exp(is_domain_ip_email_equal(domain_info, network_whois)),
                                   method_known_hoster=is_known_hoster(domain_info['netDomain']))

    return evaluation_res


def is_reverse_host_equal(netDomain, baseDomain):
    if netDomain is None:
        return None

    extracted_ndomain = urltools.extract(netDomain)
    extracted_bdomain = urltools.extract(baseDomain)

    # Comparing domain part of both domain, suffix or prefix can be different for pass the test

    if not extracted_ndomain or not extracted_bdomain:
        return None

    return True if (extracted_ndomain.domain == extracted_bdomain.domain) else False


def is_whois_info_equal(domain_whois: dict, network_whois: IPWhoisResult):
    if not domain_whois.get('holderName') or not network_whois.get_organization():
        return None
    if is_similar_string(strip_company_name(domain_whois.get('holderName')),
                         strip_company_name(network_whois.get_organization())):
        return True
    return False


def is_domain_ip_email_equal(domain_info: dict, ip_whois: IPWhoisResult):
    if not ip_whois.contact_email or not domain_info.get('baseDomain'):
        return None

    extracted_email = urltools.extract(ip_whois.contact_email)
    extracted_dom = urltools.extract(domain_info.get('baseDomain'))

    # Comparing domain part of both domain, suffix or prefix can be different for pass the test
    return True if (extracted_dom.domain == extracted_email.domain) else False


def is_known_hoster(hoster):
    db.open_connection()
    db.exec_query("SELECT COUNT(*) from webhoster where hoster_domain='{url}'".format(url=hoster))
    return True if db.cur.fetchone()[0] else False
    db.close_connection()


def name_to_ip(domain, www=False):
    result = None
    try:
        result = dns.resolver.query(("www." if www else "") + domain)[0].address

    except Exception as e:
        if www is True:
            print("[WARN][NAME2IPv4] ", e)
        else:
            print("[NOTICE][NAME2IP] Trying with www: ", domain)
            return name_to_ip(domain, True)

    return result


def name_to_ipv6(domain, www=False):
    result = None
    try:
        result = dns.resolver.query(("www." if www else "") + domain, 'AAAA')[0].address

    except Exception as e:
        if www is True:
            print("[WARN][NAME2IPv6] ", e)
        else:
            print("[NOTICE][NAME2I6] Trying with www: ", domain)
            return name_to_ipv6(domain, True)

    return result


def ip_2_name(ip):
    result = None
    try:
        result = socket.gethostbyaddr(ip)[0]

    except TypeError:
        pass
    except Exception as e:
        print("[WARN][IP2NAME] ", ip, e)

    return result


def extract_domain(domain):
    return urltools.extract_domain_str(domain) if domain else None


def get_domain_info(domain):
    domain_parts = urltools.extract(domain)
    extracted_domain = urltools.extract_domain_str(domain)
    primary_ip = name_to_ip(extracted_domain)
    primary_ipv6 = name_to_ipv6(extracted_domain)
    reverse_host = ip_2_name(primary_ip)
    return {'domain': extracted_domain,
            'subdomain': domain_parts.subdomain,
            'tld': domain_parts.suffix,
            'baseDomain': extracted_domain,
            'netDomain': urltools.extract_domain_str(reverse_host),
            'netDomainFull': reverse_host,
            'serverIp6': primary_ipv6,
            'serverIp': primary_ip}
