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

import os
import sys
import codecs
import ConfigParser
from bs4 import BeautifulSoup
import simplejson as json
import requests
requests.packages.urllib3.disable_warnings()


# settings
IN_FILE = 'kinopoisk.ru-favourites.xls'



_trakt = {
    # get these from https://trakt.tv/oauth/applications/new
    'client_id': '',  # Auth details for trakt API
    'client_secret': '',  # Auth details for trakt API
    # this comes from auth procedure
    'oauth_token': '',  # Auth details for trakt API
    'baseurl': 'https://api.trakt.tv'  # Sandbox environment https://api-staging.trakt.tv
}

_headers = {
    'Accept': 'application/json',  # required per API
    'Content-Type': 'application/json',  # required per API
    'User-Agent': 'Trakt importer',  # User-agent
    'Connection': 'Keep-Alive',  # Thanks to urllib3, keep-alive is 100% automatic within a session!
    'trakt-api-version': '2',  # required per API
    'trakt-api-key': '',  # required per API
    'Authorization': '',  # required per API
}

_proxy = {
    'proxy': False,  # True or False, trigger proxy use
    'host': 'https://127.0.0.1',  # Host/IP of the proxy
    'port': '3128'  # Port of the proxy
}

_proxyDict = {
    "http": _proxy['host']+':'+_proxy['port'],
    "https": _proxy['host']+':'+_proxy['port']
}


def read_config():
    """
    Read config file and if provided overwrite default values
    If no config file exist, create one with default values
    """
    global work_dir
    work_dir = ''
    if getattr(sys, 'frozen', False):
            work_dir = os.path.dirname(sys.executable)
    elif __file__:
            work_dir = os.path.dirname(__file__)
    _configfile = os.path.join(work_dir, 'config.ini')
    # if os.path.exists(options.config):
    #         _configfile = options.config
    # if options.verbose:
    #         print "Config file: {0}".format(_configfile)
    if os.path.exists(_configfile):
            try:
                    config = ConfigParser.SafeConfigParser()
                    config.read(_configfile)
                    if config.has_option('TRAKT', 'CLIENT_ID') and len(config.get('TRAKT', 'CLIENT_ID')) != 0:
                            _trakt['client_id'] = config.get('TRAKT', 'CLIENT_ID')
                    else:
                            print 'Error, you must specify a trakt.tv CLIENT_ID'
                            sys.exit(1)
                    if config.has_option('TRAKT', 'CLIENT_SECRET') and len(config.get('TRAKT', 'CLIENT_SECRET')) != 0:
                            _trakt['client_secret'] = config.get('TRAKT', 'CLIENT_SECRET')
                    else:
                            print 'Error, you must specify a trakt.tv CLIENT_SECRET'
                            sys.exit(1)
                    if config.has_option('TRAKT', 'OAUTH_TOKEN') and len(config.get('TRAKT', 'OAUTH_TOKEN')) != 0:
                            _trakt['oauth_token'] = config.get('TRAKT', 'OAUTH_TOKEN')
                    else:
                            print 'Warning, authentification is required'
                    if config.has_option('TRAKT', 'BASEURL'):
                            _trakt['baseurl'] = config.get('TRAKT','BASEURL')
                    if config.has_option('SETTINGS', 'PROXY'):
                            _proxy['proxy'] = config.getboolean('SETTINGS','PROXY')
                    if _proxy['proxy'] and config.has_option('SETTINGS','PROXY_HOST') and config.has_option('SETTINGS', 'PROXY_PORT'):
                            _proxy['host'] = config.get('SETTINGS', 'PROXY_HOST')
                            _proxy['port'] = config.get('SETTINGS', 'PROXY_PORT')
                            _proxyDict['http'] = _proxy['host']+':'+_proxy['port']
                            _proxyDict['https'] = _proxy['host']+':'+_proxy['port']
            except:
                    print "Error reading configuration file {0}".format(_configfile)
                    sys.exit(1)
    else:
            try:
                    print '%s file was not found!' % _configfile
                    config = ConfigParser.RawConfigParser()
                    config.add_section('TRAKT')
                    config.set('TRAKT', 'CLIENT_ID', '')
                    config.set('TRAKT', 'CLIENT_SECRET', '')
                    config.set('TRAKT', 'OAUTH_TOKEN', '')
                    config.set('TRAKT', 'BASEURL', 'https://api.trakt.tv')
                    config.add_section('SETTINGS')
                    config.set('SETTINGS', 'PROXY', False)
                    config.set('SETTINGS', 'PROXY_HOST', 'https://127.0.0.1')
                    config.set('SETTINGS', 'PROXY_PORT', '3128')
                    with open(_configfile, 'wb') as configfile:
                            config.write(configfile)
                            print "Default settings wrote to file {0}".format(_configfile)
            except:
                    print "Error writing configuration file {0}".format(_configfile)
            sys.exit(1)


def api_auth():
    # API call for authentification OAUTH
    print("Open the link in a browser and paste the pincode when prompted")
    print("https://trakt.tv/oauth/authorize?response_type=code&"
          "client_id={0}&redirect_uri=urn:ietf:wg:oauth:2.0:oob".format(_trakt["client_id"]))
    pincode = str(raw_input('Input:'))
    url = _trakt['baseurl'] + '/oauth/token'
    values = {
        "code": pincode,
        "client_id": _trakt["client_id"],
        "client_secret": _trakt["client_secret"],
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "authorization_code"
    }

    request = requests.post(url, data=values)
    response = request.json()
    _headers['Authorization'] = 'Bearer ' + response["access_token"]
    _headers['trakt-api-key'] = _trakt['client_id']
    print 'Save as "oauth_token" in file {0}: {1}'.format('config.ini', response["access_token"])


# api text search
# possible values: movie , show , episode , person , list
def api_search(object, search_type='movie,show,episode'):
    # API call for Search
    # some years differ by one on two sites
    def year_range(year):
        int_year = int(year)
        return str(int_year-1) + '-' + str(int_year+1)
    # query name and year
    # for some russian movies there's no english name, so take russian
    query = (object[1], object[0].encode('utf-8'))[object[1] == '']

    url = _trakt['baseurl'] + '/search/' + search_type + '?query={0}&fields={1}&years={2}'.format(query, 'title,translations', year_range(object[2]))
    # print url
    # if options.verbose:
    #     print(url)
    if _proxy['proxy']:
        r = requests.get(url, headers=_headers, proxies=_proxyDict, timeout=(10, 60))
    else:
        r = requests.get(url, headers=_headers, timeout=(5, 60))
    if r.status_code != 200:
        print "Error Get ID lookup results: {0} [{1}]".format(r.status_code, r.text)
        return None
    else:
        return json.loads(r.text)


# parse input file, collect original movie name and year
def parse_input(input_file):
    movies = []
    # open in std encoding
    f = codecs.open(input_file, encoding='cp1251')
    soup = BeautifulSoup(f, 'html.parser')
    items = soup.find_all('tr')[1:]
    for row in items:
        # row[0] - name RU
        # row[1] - original name EN
        # row[2] - year
        # row[9] - user rating
        cells = row.find_all('td')
        movies.append((cells[0].get_text(), cells[1].get_text(), cells[2].get_text(), cells[9].get_text()))
    return movies


read_config()
# Display oauth token if exist, otherwise authenticate to get one
if _trakt['oauth_token']:
    _headers['Authorization'] = 'Bearer ' + _trakt['oauth_token']
    _headers['trakt-api-key'] = _trakt['client_id']
else:
    api_auth()
# get movies list
list_items = parse_input(IN_FILE)
sync_values = {
    'movies': [],
    'shows': [],
    'episodes': []
}
for list_item in list_items:
    # search in Trakt DB
    search_result = api_search(list_item)
    objects_found = len(search_result)
    if objects_found == 0:
        print 'Not found - %s(%s)' % (list_item[0], list_item[2])
    else:
        print '%s(%s) - %d objects' % (list_item[0], list_item[2], len(search_result))
        if list_item[3] not in ['', 'zero']:
            print 'Personal rating: ' + list_item[3]
        for i, item in enumerate(search_result):
            # if item['type'] == 'movie':
            #     link = 'https://trakt.tv/search/trakt/%s?id_type=%s' % (item['movie']['ids']['trakt'], item['type'])
            #     print '%d - [MOVIE] Title: %s, Year: %s, Trakt ID: %s, Link: %s' % (i+1, item['movie']['title'], item['movie']['year'], item['movie']['ids']['trakt'], link)
            # elif item['type'] == 'episode':
            #     link = 'https://trakt.tv/search/trakt/%s?id_type=%s' % (item['episode']['ids']['trakt'], item['type'])
            #     print '%d - [EPISODE] Title: %s, Trakt ID: %s, Show: %s, Year: %s, Link: %s' % (i+1, item['episode']['title'], item['episode']['ids']['trakt'], item['show']['title'], item['show']['year'], link)
            # elif item['type'] == 'show':
            #     link = 'https://trakt.tv/search/trakt/%s?id_type=%s' % (item['show']['ids']['trakt'], item['type'])
            #     print '%d - [SHOW] Title: %s, Year: %s, Trakt ID: %s, Link: %s' % (i+1, item['show']['title'], item['show']['year'], item['show']['ids']['trakt'], link)
            # else:
            #     print 'Unknown type - %s' % item['type']
            curr_obj = item[item['type']]
            if item['type'] == 'episode':
                curr_obj['year'] = item['show']['year']
            link = 'https://trakt.tv/search/trakt/%s?id_type=%s' % (curr_obj['ids']['trakt'], item['type'])
            print '%d - [%s] Title: %s, Year: %s, Trakt ID: %s, Link: %s' % (i+1, item['type'], curr_obj['title'], curr_obj['year'], curr_obj['ids']['trakt'], link)
        if objects_found == 1:
            #TODO: add procedure
            sync_values[item['type']+'s'].append(item)
            add_id = item[item['type']]['ids']['trakt']
            print 'Only one item found, adding to list. ID: %s' % add_id
        else:
            print 'More than one item found.'
            choice = -1
            while choice not in range(objects_found):
                try:
                    raw_result = raw_input('Choose element number[1]:')
                    if raw_result == '':
                        choice = 0
                    else:
                        choice = int(raw_result) - 1
                except ValueError:
                    choice = -1
                print choice
            chosen_item = search_result[choice]
            print chosen_item

    print '--------------------------'

print 'Sync Values:'
print sync_values