#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import argparse
import json
import process_page
from modules import database as db
from modules.classes import PreparedDomain


def error_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_file(filename, url_col, delimiter, quotechar, skiplines, category, restoreconn=False, reevaluate=False,
               cz_omit=True, subdom_omit=False, note_column=None):
    db.open_connection()  # create DB connection

    total = 0
    domains_unvisited = set()

    # Read CSV stream from given file
    with open(filename, 'r') as csvfile:
        filereader = csv.reader(csvfile, delimiter=delimiter, quotechar=quotechar)

        # Skip given count of lines
        for _ in range(skiplines):
            next(filereader)

        # Do for each line in CSV file
        for row in filereader:
            url = row[url_col - 1]

            # Selecting note

            if note_column == -1:  # save whole row
                note = json.dumps(row)

            elif note_column:
                note = row[note_column - 1]

            else:
                note = None

            # Check if domain name exists

            if url not in [None, "", "NA"]:
                domains_unvisited.add(PreparedDomain(url, note))

    print("Unique domain for visiting: ")

    # View the list of prepared objects
    domains_unvisited_list = list()
    for dom in domains_unvisited:
        domains_unvisited_list.append(dom.domain)

    print(', '.join(domains_unvisited_list))

    with open("output.txt", "a") as output:
        output.write(
            "DOMAIN\tM_WHOIS\tZM_REV\tM_Znamy\tM_MAIL\tServer IP\tDrzitel\tKontakt\tEmail\n"
            "---------------------------------------------------------------------------------\n")

        for domain in domains_unvisited:
            try:
                process_page.process_domain(domain, category, reevaluate, restoreconn, cz_omit, subdom_omit, output)
                total += 1

            except (KeyboardInterrupt, SystemExit):
                print("Exited by user.")
                exit(0)

            except RuntimeError:
                # report error and proceed
                print("[ERROR]", domain, " Unexcepted error:", sys.exc_info()[0])

    print("[STAT]: TOTAL " + repr(total) + "\n")

    db.close_connection()


if __name__ == '__main__':
    # Parse command line args

    parser = argparse.ArgumentParser(description='Process CSV file with website urls. ')

    parser.add_argument('category', help='Specifies the category of pages in given file, will save to results DB ',
                        type=str, metavar='CAT')
    parser.add_argument('filename', help='file with comma separed values')
    parser.add_argument('urlcolumn', metavar='N', type=int, help='column with URL', default=0)
    parser.add_argument('--notecolumn', metavar='N', type=int, help='column with note', default=None)
    parser.add_argument('--noterow', action='store_true', help='save whole CSV row as note', default=None)
    parser.add_argument('--delimiter', help='CSV file delimiter', default="\t", metavar='X')
    parser.add_argument('--quotechar', help='CSV file delimiter', default="\"", metavar='Q')
    parser.add_argument('--skip', help='Skip CSV header rows (how many)', default=0, type=int, metavar='S')
    parser.add_argument('--restoreconn', help='Restore connection to WHOIS automaticlly', action='store_true')
    parser.add_argument('--reevaluate', help='Overwrite the result in DB', action='store_true')
    parser.add_argument('--noczomit', help='Don\'t omit not CZ domains', action='store_true')
    parser.add_argument('--nosubdomomit', help='Don\'t omit subdomains', action='store_true')

    args = parser.parse_args()

    if args.noterow:
        # Save whole row as note
        note_column = -1
        if args.notecolumn:
            error_print('[ERROR] --noterow cannot be combined with --notecolumn')
            exit(1)

    else:
        note_column = args.notecolumn

    parse_file(args.filename, args.urlcolumn, args.delimiter, args.quotechar, args.skip, args.category,
               args.restoreconn, args.reevaluate, not args.noczomit, not args.nosubdomomit, note_column)
