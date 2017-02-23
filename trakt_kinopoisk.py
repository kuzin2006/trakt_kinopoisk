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
IN_FILE = ''
work_dir = ''
list_to_update = ''


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
                    if config.has_option('SETTINGS', 'IN_FILE'):
                        global IN_FILE
                        if config.get('SETTINGS', 'IN_FILE') != '':
                            IN_FILE = os.path.join(work_dir, config.get('SETTINGS', 'IN_FILE'))
                            if not os.path.exists(IN_FILE):
                                print 'Input data file {0} not found, exiting'.format(IN_FILE)
                                sys.exit(1)
                        else:
                            print 'Please copy input file to script dir, and set its name in config.ini as IN_FILE'
                            sys.exit(1)
                    if config.has_option('SETTINGS', 'LIST'):
                        global list_to_update
                        list_to_update = config.get('SETTINGS', 'LIST')
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
                    config.set('SETTINGS', 'IN_FILE', '')
                    config.set('SETTINGS', 'LIST', '')
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


# universal api request
def api_request(url, request_type='get', post_data=None):
    response = {
        'result': False,
        'HTTP': '',
        'json': ''
    }
    if _proxy['proxy']:
        if request_type == 'get':
            r = requests.get(url, headers=_headers, proxies=_proxyDict, timeout=(10, 60))
        else:
            r = requests.post(url, data=post_data, headers=_headers, proxies=_proxyDict, timeout=(10, 60))
    else:
        if request_type == 'get':
            r = requests.get(url, headers=_headers, timeout=(5, 60))
        else:
            r = requests.post(url, data=post_data, headers=_headers, timeout=(10, 60))

    if r.status_code not in [200, 201, 204]:
        response['result'] = False
        response['HTTP'] = 'Error code: {0} [{1}]'.format(r.status_code, r.text)
    else:
        response['result'] = True
        response['HTTP'] = 'Success: {0}'.format(r.status_code)
        response['json'] = json.loads(r.text.encode('utf-8'))
    return response


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
    search_result = api_request(url)
    if not search_result['result']:
        print "Error Get ID lookup results: {0}".format(search_result['HTTP'])
        return None
    else:
        return search_result['json']


# api add to list
def api_add_items(values, target_list=None):
    # get username
    url = _trakt['baseurl'] + '/users/settings'
    r = api_request(url)
    if not r['result']:
        print 'Error: %s' % r['HTTP']
        return None
    else:
        username = r['json']['user']['ids']['slug']
        # sync with watchlist or collection, otherwise add items to given list name
        if target_list in ['collection', 'watchlist', 'history', 'ratings']:
            url = _trakt['baseurl'] + '/sync/{0}'.format(target_list)
        else:
            url = _trakt['baseurl'] + '/users/{0}/lists/{1}/items'.format(username, target_list)
        r = api_request(url, request_type='POST', post_data=values)
        return r


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
        movies.append((cells[0].get_text(), cells[1].get_text(), cells[2].get_text()[:4], cells[9].get_text()))
    return movies


# create trakt POST data
def get_items(list_items):
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
                rating = list_item[3]
            else:
                rating = None
            for i, item in enumerate(search_result):
                    curr_obj = item[item['type']]
                    if item['type'] == 'episode':
                        curr_obj['year'] = item['show']['year']
                    link = 'https://trakt.tv/search/trakt/%s?id_type=%s' % (curr_obj['ids']['trakt'], item['type'])
                    print '%d - [%s] Title: %s, Year: %s, Trakt ID: %s, Link: %s' % (i+1, item['type'], curr_obj['title'], curr_obj['year'], curr_obj['ids']['trakt'], link)
            if objects_found == 1:
                chosen_item = search_result[0]
                print 'Only one item found, adding to list.'
            else:
                print 'More than one item found.'
                # now choose one to add
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
                chosen_item = search_result[choice]

            curr_obj = chosen_item[chosen_item['type']]
            print 'Add - [%s] Title: %s, Year: %s, Trakt ID: %s, Link: %s' % (chosen_item['type'], curr_obj['title'], curr_obj['year'], curr_obj['ids']['trakt'], link)
            if rating is not None:
                curr_obj['rating'] = int(rating)
                print 'Personal rating added: %s' % rating
            sync_values[chosen_item['type']+'s'].append(curr_obj)
        print '--------------------------'
    return sync_values


# main
read_config()
# Display oauth token if exist, otherwise authenticate to get one
if _trakt['oauth_token']:
    _headers['Authorization'] = 'Bearer ' + _trakt['oauth_token']
    _headers['trakt-api-key'] = _trakt['client_id']
else:
    api_auth()
# get movies list from cache
cache_file = os.path.join(work_dir, 'request.cache')
if os.path.exists(cache_file):
    cache_choice = raw_input('Cached request data found. Enter \'y\' to use it:')
else:
    cache_choice = 'n'

if cache_choice == 'y':
    print 'Read cached request data from {0}. Delete this file for new parse.'.format(cache_file)
    try:
        f = codecs.open(cache_file, encoding='utf-8')
        string = f.readline()
        trakt_items = json.loads(string.encode('utf-8'))
        # print trakt_items
    except Exception as e:
        print "Error reading cache file {0}".format(cache_file) + e.message
        sys.exit(1)
    finally:
        f.close()
else:
    print 'Cache not found or rejected, starting import from %s' % IN_FILE
    try:
        kinopoisk_items = parse_input(IN_FILE)
        trakt_items = get_items(kinopoisk_items)
        print 'Items read: %d' % len(kinopoisk_items)
        f = codecs.open(cache_file, mode='wb', encoding='utf-8')
        f.writelines(json.dumps(trakt_items).encode('utf-8'))
    except Exception as e:
        print "Error writing cache file {0} - {1}".format(cache_file. e.message)
        sys.exit(1)
    finally:
        f.close()
# stats
print 'Items found in Trakt: %d' % int(len(trakt_items['movies'])+len(trakt_items['shows'])+len(trakt_items['episodes']))
# print 'Sync Values:'
# print trakt_items
print 'Trakt list for items: %s' % list_to_update
continue_choice = raw_input('If all settings correct, enter \'y\' to send list to Trakt, or \'r\' to update ratings only:')
template = '{:<10}{:<8}{:<7}{:<10}'
if continue_choice == 'y':
    # api request for sync
    response = api_add_items(json.dumps(trakt_items), target_list=list_to_update)
    if not response['result']:
        print 'API list update error: %s' % response['HTTP']
    else:
        print 'API call success:\n---------------------------------'
        print template.format('', 'Movies', 'Shows', 'Episodes')
        print template.format('Added', response['json']['added']['movies'], '', response['json']['added']['episodes'])
        if list_to_update != 'history':
            print template.format('Existing', response['json']['existing']['movies'], '', response['json']['existing']['episodes'])
    # update ratings
    response = api_add_items(json.dumps(trakt_items), target_list='ratings')
    if not response['result']:
        print 'API ratings update error: %s' % response['HTTP']
    else:
        print 'API update ratings:'
        template_items = []
        for media_type in ['movies', 'shows', 'episodes']:
            try:
                template_items.append(response['json']['added'][media_type])
            except:
                template_items.append('')
        print template.format('Rated', template_items[0], template_items[1], template_items[2])
elif continue_choice == 'r':
    # update ratings
    response = api_add_items(json.dumps(trakt_items), target_list='ratings')
    if not response['result']:
        print 'API ratings update error: %s' % response['HTTP']
    else:
        print 'API call success:\n---------------------------------'
        print template.format('', 'Movies', 'Shows', 'Episodes')
        print 'API update ratings:'
        template_items = []
        for media_type in ['movies', 'shows', 'episodes']:
            try:
                template_items.append(response['json']['added'][media_type])
            except:
                template_items.append('')
        print template.format('Rated', template_items[0], template_items[1], template_items[2])
else:
    print 'User cancelled, no data sent. Bye.'
    sys.exit(0)

