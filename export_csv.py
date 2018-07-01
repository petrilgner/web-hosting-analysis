#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from modules import database as db
from modules.classes import EvaluatedCategory


def print_category(category):
    db.open_connection()
    db.exec_query("SELECT * from results where `category`='{category}'".format(category=category))
    category_result = EvaluatedCategory(db.cur.fetchall())

    print(category_result)
    category_result.to_csv(file='export/' + category + '_export.csv')

    db.close_connection()


if __name__ == '__main__':

    # Parse command line args

    parser = argparse.ArgumentParser(description='Export info from DB to CSV file <category>_export.csv.')
    parser.add_argument('category', help='given category name')
    args = parser.parse_args()
    print_category(args.category)
