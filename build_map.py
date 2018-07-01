#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import folium

from modules import database as db


def coords_map():
    """
    Create map from DB results
    :return: 
    """

    tileset = r'https://api.mapbox.com/styles/v1/mapbox/light-v9/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1IjoicGV0cmlsZ25lciIsImEiOiJjajI4cGlxbDgwMDVxMzJvanBldTlibWNrIn0.9W5sqnxpaPXlJe1VjlZaZA'
    folium_map = folium.Map(location=[49.19, 16.60], tiles=tileset, attr='Coords')

    db.exec_query(
        "SELECT lat,lon,city,COUNT(lat) as count from webserver GROUP by lat,lon")
    for e in db.cur.fetchall():
        radius = e[3] * 5
        folium.CircleMarker(location=[e[0], e[1]], popup="{} ({})".format(e[2], e[3]),
                            radius=15 if radius > 15 else radius).add_to(folium_map)

    folium_map.save('visualisation/coords.html')


if __name__ == '__main__':

    # Parse command line args
    parser = argparse.ArgumentParser(description='Provides some basic data operations ')

    parser.add_argument('type', help='Type of request', type=str, choices=['coords'])

    args = parser.parse_args()
    db.open_connection()
    if args.type == 'coords':
        coords_map()

    db.close_connection()
