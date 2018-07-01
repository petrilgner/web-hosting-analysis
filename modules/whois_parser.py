#!/usr/bin/env python3

import argparse
if __name__ == '__main__':

    import database as db, formatter
    from classes import DomainWhoisResult, ContactWhoisResult, IPWhoisResult, GeoCoordinates

else:

    from modules import database as db, formatter
    from modules.classes import DomainWhoisResult, ContactWhoisResult, IPWhoisResult, GeoCoordinates


add_websrv_result = ("INSERT INTO `webserver` "
                     "(`ip`, `as`,	`organization`,	`isp`,	`country`,	`lat`,	`lon`, `city`, `region`, `postal_code`,	`contact_email`, `contact_address`) "
                     "VALUES ('{ip}', '{as_desc}', '{organization}', '{isp}', '{country}', '{lat}', '{lon}', '{city}', '{region}', '{postal_code}', '{contact_email}', '{contact_address}')")

select_websrv_result = ("SELECT * FROM `webserver` WHERE `ip`='{ip}'")


def probe_domain(domain, restore_conn=False):
    whois = DomainWhoisResult(domain, restore_conn)
    return whois.result_data


def probe_contact(contact_id, restore_conn=False):
    whois = ContactWhoisResult(contact_id, restore_conn)
    return whois.result_data


def probe_ip(ip):
    whois = IPWhoisResult(ip)

    db.open_connection()
    db.exec_query(select_websrv_result.format(ip=ip))

    db_row = db.cur.fetchone()
    if db_row:
        # Take result from local DB

        whois.contact_name = db_row[3]
        whois.contact_email = db_row[11]
        whois.contact_address = db_row[12]
        whois.geo_ip.organization = db_row[3]
        whois.geo_ip.isp = db_row[4]

        whois.geo_ip.city = db_row[8]
        whois.geo_ip.country = db_row[5]
        whois.geo_ip.region = db_row[9]
        whois.geo_ip.postal_code = db_row[10]
        whois.geo_ip.as_desc = db_row[2]

        whois.geo_ip.coordinates = GeoCoordinates(db_row[6], db_row[7])

    else:
        # Perform queries on remote DBs
        whois.get_from_whois()
        whois.get_from_geoip()

        db.exec_query(add_websrv_result.format(
            ip=ip,
            as_desc=whois.geo_ip.as_desc,
            organization=whois.geo_ip.organization,
            isp=whois.geo_ip.isp,
            country=whois.geo_ip.country,
            region=whois.geo_ip.region,
            city=whois.geo_ip.city,
            postal_code=whois.geo_ip.postal_code,
            contact_email=whois.contact_email,
            contact_address=whois.contact_address,
            lat=whois.geo_ip.coordinates.lat,
            lon=whois.geo_ip.coordinates.lon
        ))
        db.commit()

    db.close_connection()

    return whois


def print_ip(ip, restore_conn=False):

    whois = probe_ip(ip)
    if whois:
        return {
            'contact_name': whois.contact_name,
            'contact_email': whois.contact_email,
            'contact_address': whois.contact_address,
            'geo_ip': str(whois.geo_ip)
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform an WHOIS query for given subject. ')

    parser.add_argument('type', help='Type of query', default="domain", type=str, choices=['domain', 'contact', 'ip'])
    parser.add_argument('subject', help='Subject for query')
    parser.add_argument('--restoreconn', help='Restore connection to WHOIS automaticlly', action='store_true')

    args = parser.parse_args()

    funcs = {
        "domain": probe_domain,
        "ip": print_ip,
        "contact": probe_contact
    }

    formatter.print_dict(funcs[args.type](args.subject, args.restoreconn))
