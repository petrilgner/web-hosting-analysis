#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from modules import database as db
from modules.classes import EvaluatedCategory


def print_category(category):
    """
    Function for printing category results to stdout.
    :param category: 
    """
    db.open_connection()
    db.exec_query("SELECT * from results where `category`='{category}'".format(category=category))

    # Creating object EvaluatedCategory, pass DB result to class constructor
    category_result = EvaluatedCategory(db.cur.fetchall())

    print(category_result)
    print(category_result.get_stats())

    db.close_connection()

if __name__ == '__main__':

    # Parse command line args

    parser = argparse.ArgumentParser(description='Print info from DB ')
    parser.add_argument('category', help='given category name')

    args = parser.parse_args()
    print_category(args.category)
