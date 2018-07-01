from abc import ABC, abstractmethod
from unittest.mock import _ANY

import tldextract
import prettytable
import urllib.request
import json

from dns.e164 import query
from requests import get, ReadTimeout
import time
import subprocess
import csv
from ipwhois import IPWhois
from pyquery import PyQuery


class PreparedDomain:
    """Domain to be visited"""

    domain = None
    original_url = None
    note = None

    def __str__(self):
        return self.domain

    def __init__(self, original_url=None, note=None):
        ext = tldextract.extract(original_url)
        self.domain = '.'.join(ext[:3])
        self.original_url = original_url
        self.note = note


class EvaluatedPage:
    """Evaluated page results"""

    method_known_hoster = False
    method_reverse_dns = False
    method_email = False
    method_whois = False

    hosted = False

    score = 0
    score_dict = {}

    METHODS_SCORES = {
        1: (0, -0.5),  # REV
        2: (0.8, 0),  # KN
        3: (0, -0.4),  # WH
        4: (0, -0.6),  # EM
    }
    HOSTED_THRESHOLD = 0

    @staticmethod
    def bool2switcher(bool_value):
        switcher = {
            True: 'ANO',
            False: 'NE',
            None: "???"
        }
        return switcher[bool_value]

    def __init__(self, domain, method_reverse_dns, method_known_hoster, method_whois, method_email):
        self.domain = domain
        self.method_reverse_dns = method_reverse_dns
        self.method_known_hoster = method_known_hoster
        self.method_whois = method_whois
        self.method_email = method_email

        self.calc_score()

    def __str__(self):
        return "WHOIS: {rWh}, Email: {rEm}, Known hoster: {rKh}, Rev DNS: {rRd} ".format(
            rWh=self.bool2switcher(self.method_whois),
            rKh=self.bool2switcher(self.method_known_hoster),
            rEm=self.bool2switcher(self.method_email),
            rRd=self.bool2switcher(self.method_reverse_dns))

    def calc_score(self):
        self.score = 0
        for method_key, method_score in self.METHODS_SCORES.items():
            # Get method result for this method
            method_result = {1: self.method_reverse_dns,
                             2: self.method_known_hoster,
                             3: self.method_whois,
                             4: self.method_email}.get(method_key)

            if method_result is not None:
                if method_result is True:
                    self.score += method_score[0]  # In/Decrement score if is method result True
                    self.score_dict[method_key] = method_score[0]

                if method_result is False:
                    self.score += method_score[1]  # In/Decrement score if is method result False
                    self.score_dict[method_key] = method_score[1]
            else:
                pass

        if self.HOSTED_THRESHOLD <= self.score:
            self.hosted = True


class EvaluatedCategory:
    total = 0
    hosted = 0
    method_sums = {}
    scores = {}
    hosted_pages = list()

    @staticmethod
    def bool2switcher(bool_value: str) -> int:
        switcher = {
            'True': 1,
            'False': 0,
            'None': -1
        }
        return switcher[bool_value]

    @staticmethod
    def sbool_to_str(bool_value: str) -> str:
        switcher = {
            'True': 'Ano',
            'False': 'Ne',
            'None': '?'
        }
        return switcher[bool_value]

    @staticmethod
    def bool_to_str(bool_value: bool) -> str:
        switcher = {
            True: 'Ano',
            False: 'Ne',
            None: '?'
        }
        return switcher[bool_value]

    @staticmethod
    def str2bool(bool_value: str) -> bool:
        switcher = {
            'True': True,
            'False': False,
        }
        return switcher.get(bool_value, None)

    def __calc_category(self) -> None:
        sums = {1: 0, 2: 0, 3: 0, 4: 0}

        for p in self.category_entries:
            evaluated_page = EvaluatedPage(p[0], self.str2bool(p[2]), self.str2bool(p[3]), self.str2bool(p[4]),
                                           self.str2bool(p[5]))

            for key, val in evaluated_page.score_dict.items():
                if val:
                    sums[key] += 1

            if evaluated_page.hosted:
                self.hosted_pages.append(p[0])
                self.hosted += 1

            self.scores[p[0]] = evaluated_page.score
            self.total += 1

        sums["total"] = len(self.hosted_pages)
        self.method_sums = sums

    def get_score(self, domain):
        return self.scores.get(domain, 0)

    def is_hosted(self, domain):
        return domain in self.hosted_pages

    def get_percents(self):

        sums = self.method_sums.copy()

        for ind, sum_m in sums.items():
            sums[ind] = round((sum_m / self.total) * 100, 2)

        return sums

    def __str__(self):

        table = prettytable.PrettyTable(
            ["Domain", "REV_HOST", "KNOWN_HOSTER", "WHOIS", "EMAIL", "HOSTED", "SCORE", "IP", "NET", "Domain holder"])
        for p in self.category_entries:
            table.add_row([
                p[0],
                self.sbool_to_str(p[2]),
                self.sbool_to_str(p[3]),
                self.sbool_to_str(p[4]),
                self.sbool_to_str(p[5]),
                'A' if self.is_hosted(p[0]) else 'N',
                '{0:.2f}'.format(self.get_score(p[0])),
                p[9],
                p[11],
                p[13][:20]
            ])

        return str(table)

    def get_stats(self):

        table = prettytable.PrettyTable(
            ["COUNT","REV_HOST", "KNOWN_HOSTER", "WHOIS", "EMAIL", "HOSTED"])

        sums = self.method_sums
        percents = self.get_percents()

        table.add_row(
            [self.total, sums.get(1), sums.get(2), sums.get(3), sums.get(4), sums.get("total")])
        table.add_row(
            ["[%]",percents.get(1), percents.get(2), percents.get(3), percents.get(4), percents.get("total")])

        return str(table)

    @staticmethod
    def json_array(input_str: str) -> []:
        try:
            data = json.loads(input_str)
            return data

        except ValueError:
            return [input_str]

    def to_csv(self, file, delimiter="\t", quotechar="|"):
        with open(file, 'w') as csv_file:
            writer = csv.writer(csv_file, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                ['Orig URL', 'Timestamp', 'REV_HOST_RES', 'KNOWN_HOSTER_RES', 'WHOIS_RES', 'EMAIL_RES', 'HOSTED',
                 'SCORE', 'S_IP', 'S_IPv6', 'DOMAIN_HOLDER', 'ORIG_DATA'])
            for p in self.category_entries:
                writer.writerow([
                                    p[0],  # original_url
                                    p[1],  # timestamp
                                    self.bool2switcher(p[2]),
                                    self.bool2switcher(p[3]),
                                    self.bool2switcher(p[4]),
                                    self.bool2switcher(p[5]),
                                    1 if self.is_hosted(p[0]) else 0,
                                    '{0:.2f}'.format(self.get_score(p[0])),
                                    p[9],
                                    p[19],
                                    p[13]
                                ] + self.json_array(p[17]))

    def __init__(self, category_entries):
        self.category_entries = category_entries
        self.__calc_category()


class CZNICWhoisResult(ABC):
    __attempts_left = 3
    _service = None

    restore_conn = False

    result_obj = None
    result_data = {}
    query = None

    def __init__(self, query, restore_conn=False):
        self.query = query.lower()
        self.restore_conn = restore_conn
        self.result_obj = self._get_object()
        try:
            self.process_query()
        except Exception as e:
            print("[WHOIS][ERR]", self._service, e)

    def _get_object(self):
        doc = None
        try:
            r = get(url='http://www.nic.cz/whois/' + self._service + '/' + self.query + '/',
                    timeout=3)
            doc = PyQuery(r.text)

        except ReadTimeout:
            print("[WHOIS] Timeout! ", self._service, self.query)

        except ConnectionError:
            print("[WHOIS] Connection error! ", self._service, self.query)

        if self.restore_conn:
            conn_result = self.check_connectivity(doc)

            # If some attempts lefts try to restore connection
            if not conn_result and self.__attempts_left:
                self.__attempts_left -= 1
                subprocess.call("./restore_conn.sh")
                time.sleep(2)
                doc = self._get_object()

        return doc

    @staticmethod
    def check_connectivity(doc):
        if not doc:
            print("[CHECK_WHOIS_CONN] No WHOIS request result")
            return False

        elif doc("label[for=id_captcha]").text():
            print("[CHECK_WHOIS_CONN] WHOIS captcha in use")
            return False

        else:
            return True

    @abstractmethod
    def process_query(self):
        pass


class DomainWhoisResult(CZNICWhoisResult):
    _service = 'domain'

    def process_query(self):
        doc = self.result_obj
        domain_rec = doc("div#domain_record span.handle").text()

        if self.query != domain_rec:
            return

        holder = doc("td.holder")
        holder_id = holder("a")

        registrar_id = doc("div#domain_record td.sponsoring-registrar a")

        nsset = doc("div#nsset_record td.handle")
        keyset = doc("div#keyset_record td.handle")

        nservers_el = doc("td.name-server span.dns_name")
        nservers = nservers_el.text().split(' ')

        self.result_data = {'domain': domain_rec,
                            'holderName': holder("span").text(),
                            'holderId': holder_id.text(),
                            'registrarId': registrar_id.text(),
                            'keyset': keyset.text(),
                            'nsset': nsset.text(),
                            'nameServers': nservers}


class ContactWhoisResult(CZNICWhoisResult):
    _service = 'contact'

    def process_query(self):
        doc = self.result_obj
        contact_rec = doc("table.result.contact span.handle").text()

        if self.query != contact_rec.lower():
            return

        organization = doc("td.organization")
        ident = doc("td.ident-value")
        name = doc("td.full-name")
        email = doc("td.email a")

        registrar_id = doc("td.sponsoring-registrar a")

        self.result_data = {'contactId': contact_rec or '',
                            'ident': ident.text() or '',
                            'organization': organization.text() or '',
                            'name': name.text() or '',
                            'email': email.text() or '',
                            'registrarId': registrar_id.text() or ''}


class GeoCoordinates:
    lat = None
    lon = None

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "({0}, {1})".format(self.lat, self.lon)


class GeoIPResult:
    ip = None
    country = None
    postal_code = None
    region = None
    city = None
    coordinates = None
    organization = None
    as_desc = None
    isp = None

    def __init__(self, ip):
        self.ip = ip

    def __str__(self):
        return "Country: {0}, Region: {3}, City: {1}, Org: {2}".format(self.country, self.city, self.organization,
                                                                       self.region)

    def get_from_geoip(self):
        with urllib.request.urlopen(url="http://ip-api.com/json/" + self.ip, timeout=3) as url:
            data = json.loads(url.read().decode())

            self.country = data.get('countryCode')
            self.postal_code = data.get('zip')
            self.region = data.get('regionName')
            self.city = data.get('city')
            self.coordinates = GeoCoordinates(data.get('lat'), data.get('lon'))
            self.as_desc = data.get('as')
            self.organization = data.get('org')
            self.isp = data.get('isp')


class IPWhoisResult:
    ip = None
    geo_ip = None
    contact_email = None
    contact_name = None
    contact_address = None

    def __init__(self, ip):
        self.ip = ip
        self.geo_ip = GeoIPResult(ip)

    def get_organization(self):
        return self.geo_ip.organization if self.geo_ip.organization else self.contact_name

    def get_from_whois(self):

        try:

            obj = IPWhois(self.ip)
            results = obj.lookup_rdap()
            objects = results['objects']

            contact = next(iter(objects.values()))['contact']
            self.contact_email = contact['email'][0]['value']
            self.contact_address = contact['address'][0]['value']
            address_split = self.contact_address.split("\n")
            self.contact_name = address_split[0]

        except Exception as e:
            print("[EXC-IPWHOIS]", e)

    def get_from_geoip(self):
        self.geo_ip.get_from_geoip()
