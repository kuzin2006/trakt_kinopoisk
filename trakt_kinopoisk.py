# -*- coding: utf-8 -*-

# Trakt (https://trakt.tv) transcoding utility
# Program takes export .xls files from kinopoisk.ru account and imports data to Trakt list
# files are pure HTML indeed

# input file rows description
# <tr>
#  0    <td bgcolor="#f2f2f2" height="40" valign="top"><i>русскоязычное название</i></td>
#  1    <td bgcolor="#f2f2f2" valign="top"><i>оригинальное название</i></td>
#  2    <td bgcolor="#f2f2f2" valign="top"><i>год</i></td>
#  3    <td bgcolor="#f2f2f2" valign="top"><i>страны</i></td>
#  4    <td bgcolor="#f2f2f2" valign="top"><i>режисcёр</i></td>
#  5    <td bgcolor="#f2f2f2" valign="top"><i>актёры</i></td>
#  6    <td bgcolor="#f2f2f2" valign="top"><i>жанры</i></td>
#  7    <td bgcolor="#f2f2f2" valign="top"><i>возраст</i></td>
#  8    <td bgcolor="#f2f2f2" valign="top"><i>время</i></td>
#  9    <td bgcolor="#f2f2f2" valign="top"><i>моя оценка</i></td>
# 10    <td bgcolor="#f2f2f2" valign="top"><i>рейтинг КиноПоиска</i></td>
# 11    <td bgcolor="#f2f2f2" valign="top"><i>число оценок</i></td>
# 12    <td bgcolor="#f2f2f2" valign="top"><i>рейтинг IMDb</i></td>
# 13    <td bgcolor="#f2f2f2" valign="top"><i>число оценок IMDb</i></td>
# 14    <td bgcolor="#f2f2f2" valign="top"><i>рейтинг MPAA</i></td>
# 15    <td bgcolor="#f2f2f2" valign="top"><i>мировая премьера</i></td>
# 16    <td bgcolor="#f2f2f2" valign="top"><i>премьера в РФ</i></td>
# 17    <td bgcolor="#f2f2f2" valign="top"><i>релиз на DVD</i></td>
# 18    <td bgcolor="#f2f2f2" valign="top"><i>мой комментарий</i></td>
# 19    <td bgcolor="#f2f2f2" valign="top"><i>бюджет</i><br />$</td>
# 20    <td bgcolor="#f2f2f2" valign="top"><i>сборы США</i><br />$</td>
# 21    <td bgcolor="#f2f2f2" valign="top"><i>сборы МИР</i><br />$</td>
# 22    <td bgcolor="#f2f2f2" valign="top"><i>сборы РФ</i><br />$</td>
# </tr>

import sys
from bs4 import BeautifulSoup
import simplejson as json
import requests
requests.packages.urllib3.disable_warnings()


# settings
IN_FILE = 'kinopoisk.ru-favourites.xls'
# get these from https://trakt.tv/oauth/applications/new
CLIENT_ID = '548b3d1241db6b1624c3d1e38bb8c1521589ea30dcb5a0c51995e6635e2d7c85'
CLIENT_SECRET = '69ce8e0bf361e506f3ce9a466eda131a735036e6ff40d984e279cd6b3c28200c'

_trakt = {
        'client_id'     :       '', # Auth details for trakt API
        'client_secret' :       '', # Auth details for trakt API
        'oauth_token'   :       '', # Auth details for trakt API
        'baseurl'       :       'https://api.trakt.tv'  # Sandbox environment https://api-staging.trakt.tv
}

_headers = {
        'Accept'            : 'application/json',   # required per API
        'Content-Type'      : 'application/json',   # required per API
        'User-Agent'        : 'Tratk importer',     # User-agent
        'Connection'        : 'Keep-Alive',         # Thanks to urllib3, keep-alive is 100% automatic within a session!
        'trakt-api-version' : '2',                  # required per API
        'trakt-api-key'     : '',                   # required per API
        'Authorization'     : '',                   # required per API
}

# TODO: config reader
_trakt['client_id'] = CLIENT_ID
_trakt['client_secret'] = CLIENT_SECRET

# parse input file, collect original movie name and year
def parse_input(input_file):
    movies = []
    soup = BeautifulSoup(open(IN_FILE), 'html.parser')
    items = soup.find_all('tr')[1:]
    for row in items:
        # row[1] - original name
        # row[2] - year
        cells = row.find_all('td')
        movies.append((cells[1].get_text(), cells[2].get_text()))
    return movies

print parse_input(IN_FILE)