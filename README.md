# trakt_kinopoisk
This script imports movies from your kinopoisk.ru personal lists to trakt.tv account

# Manual

1. Login into your [kinopoisk account](https://www.kinopoisk.ru/mykp/), and export your lists to MS Excel files.
2. Create [New Trakt App](https://trakt.tv/oauth/applications/new)
3. Run trakt_kinopoisk.py First run will create new config.ini file:  

    [TRAKT]  
    client_id =   
    client_secret =   
    oauth_token =   
    baseurl = https://api.trakt.tv  
  
    [SETTINGS]  
    proxy = False  
    proxy_host = https://127.0.0.1  
    proxy_port = 3128  
    in_file =   
    list =   
  

4. Fill 'client_id' and 'client_secret' fields
5. Set 'in_file' and 'list' params with filename you previously exported from Kinopoisk. List name may be 'history', 'watchlist' or 'collection' for standardard Trakt account lists, or you may create your own list in Trakt Dashboard, and set its name in config then.
6. Run trakt_kinopoisk.py again. Follow on-screen instruction of creating the OAuth key.
7. Finally, run the script again, and proceed with adding your collection to trakt. Repeat the procedure with any other export files, just change 'in_file' parameter in config.ini

Sometimes API calls fail, thus script saves call data in request.cache file. You may repeat API call without searching your movies in Trakt again. Press n when script asks you to use cached data or delete 'request.cache' file manually before running the script.
