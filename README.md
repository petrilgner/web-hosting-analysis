This tools analyses the list of web servers. It detects if web page is hosted on shared 
environment, support of security protocols as a DNSSEC, HTTPS. It also provides an information about IPv6 support. 

The application requires an Python 3.5 or greater support. It is recommended to using with virtual environment (venv).

### Running the app using virtual environment
```
$ python3 -m venv env
$ source env/bin/activate
(env) $ == work in virtual environment ==
(env) $ deactivate
```

### Installing the requirements dependencies

Application requires couple of Python packages which are listed in `requirements.txt`. Using pip command you can 
easily install them:

``pip install -r requirements.txt``

### Creating an empty database 

SQLite database is used for storing evaluated pages. It supports division to certain categories. Empty database schema can be created:

``./database.py init``

### Processing pages

For evaluating input domains, you can use `process_page.py` or `process_csv.py` scripts. For example: `./process_page.py cat1 vutbr.cz`.

### Exporting results 

Obtained data stored in SQLite database can be viewed or exported using commands:

 - `./print_category.py` prints results within the category. 
 - `./print_stats.py` prints overall results of all categories.
 - `./print_pages.py` allows to print the webs which are hosted in network of some provider. You can create query by network address or provider domain name (--webhoster).
 - `./export_csv.py` it create an CSV output file named according the selected category.
 
 ### Database of known web hosters
 
 Some internal tests works with database of know hosters. To supply this database you can use command: 
 ``./database.py addhoster amazon.com`` 

### Server location map visualisation

The position of all detected webservers can be shown in map using command: `./build_map.py coords`. 

### Print server information

Using `modules/webserver_stats.py` command you can print the server information which are used in evaluating scripts. It includes informations such a server software version and allowance of monitored protocols.