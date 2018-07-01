#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import tldextract

urlPattern = re.compile("(http|https):\/\/")
valid_relative_uri = re.compile("[a-z0-9.~\-_/]*", re.IGNORECASE)
czech_domain = re.compile("[a-z0-9-.]*\.cz", re.IGNORECASE)
tld = re.compile("(\w+\.cz)$")


def is_cz_domain(domain):
    return czech_domain.match(domain)


def extract(url):
    return tldextract.extract(url)


def extract_domain_str(domain):
    if domain is None or '':
        return None

    extracted = extract(domain)
    return "{domain}.{tld}".format(domain=extracted.domain, tld=extracted.suffix)


def clean_url(url):
    if url and url[-1] == '/':
        url = url[:-1]  # remove last / from url

    return url


def compare_domains(d1, d2):
    return d1 == d2


