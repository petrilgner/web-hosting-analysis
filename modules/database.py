#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3 as lite
import argparse
import sys
import prettytable

con = None
cur = None

add_known_hoster = ("INSERT INTO webhoster "
                    "(`hoster_domain`, `company`) VALUES ('{domain}', '{company}')")

truncate_table_query = ("DELETE FROM `{table}`")


def open_connection():
    global con, cur
    try:

        con = lite.connect('evaluation.db')
        cur = con.cursor()

    except lite.Error as e:
        print("Error %s:" % e.args[0])
        sys.exit(1)


def close_connection():
    if con:
        con.close()


def take_connection(given_conn):
    global con, cur
    con = given_conn
    cur = con.cursor()


def exec_query(*exc_args):
    try:
        cur.execute(*exc_args)

    except lite.Error as e:
        sys.stderr.write("Error executing SQL statement: %s." % e.args[0])

        if "no such table:" in e.args[0]:
            sys.stderr.write("\n\nIt seems no database schema is created. Try to run \"./database.py init\".\n")

        sys.exit(1)


def commit():
    """
    It will commit actual transaction to SQLite database. 
    """
    con.commit()


def insert_known_hoster(hoster_domain, company=None):
    """
    It will insert given webhoster domain and trade name pair to DB as known hoster.
    :param hoster_domain: 
    :param company: 
    :return: 
    """
    exec_query(add_known_hoster.format(
        domain=hoster_domain,
        company=company
    ))
    commit()


def truncate_table(table_name):
    """
    It will truncate table with given name
    :param table_name: Table name
    """
    exec_query(truncate_table_query.format(
        table=table_name
    ))
    commit()


def run_script(filename):
    """
    It will run given SQL file
    :param filename: SQL file location 
    """
    global cur
    try:
        schema_query = open(filename, 'r').read()
        cur.executescript(schema_query)
        commit()
    except FileNotFoundError:
        print("Unable to find SQL file", filename)


def init_db():
    """
    Create DB schema using eval_schema.sql SQL file queries.
    """
    run_script('eval_schema.sql')


def print_query_result(query):
    """
    It will run given query and print result as formatted table
    :param query: Requested query
    :return Queries count
    """
    exec_query(query)

    table = prettytable.from_db_cursor(cur)
    print(table)


def arg_parser():
    # Parse command line args

    # Process just "init" variant without argument
    if len(sys.argv) == 2 and "init" in sys.argv:
        open_connection()
        init_db()
        close_connection()
        return

    parser = argparse.ArgumentParser(description='Provides some basic data operations ')

    parser.add_argument('type', help='Type of request', type=str, choices=['addhoster', 'clean', 'init', 'runscript', 'query'])
    parser.add_argument('subject', help='Object for request', type=str, default=None, metavar='SUB')

    args = parser.parse_args()

    open_connection()

    if args.type == 'addhoster':
        insert_known_hoster(args.subject)

    if args.type == 'clean':
        truncate_table(args.subject)

    if args.type == 'runscript':
        run_script(args.subject)

    if args.type == 'query':
        print_query_result(args.subject)

    if args.type == 'init':
        init_db()

    close_connection()


if __name__ == '__main__':
    arg_parser()
