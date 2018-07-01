#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import modules.database as db
import prettytable
from modules.classes import EvaluatedCategory


def print_summary():
    """
    Print stats from all evaluated categories in DB
    """

    db.open_connection()
    db.exec_query("SELECT category from results GROUP by category;")

    table_sum = prettytable.PrettyTable(["Category", "Evaluated", "Meth 1", "Meth 2", "Meth 3", "Meth 4", "Hosted"])
    categories = db.cur.fetchall()

    for p in categories:

        db.exec_query("SELECT * from results where `category`='{category}'".format(category=p[0]))
        ec = EvaluatedCategory(db.cur.fetchall())
        sums = ec.method_sums
        percent_sums = ec.get_percents()

        table_sum.add_row([
            p[0],
            ec.total,
            "{} ({}%)".format(sums[1], percent_sums[1]),
            "{} ({}%)".format(sums[2], percent_sums[2]),
            "{} ({}%)".format(sums[3], percent_sums[3]),
            "{} ({}%)".format(sums[4], percent_sums[4]),
            "{} ({}%)".format(sums["total"], percent_sums["total"]),
        ])

        print(table_sum)
        db.close_connection()


if __name__ == '__main__':

        parser = argparse.ArgumentParser(description='Print summary stats for all categories')
        parser.parse_args()
        print_summary()
