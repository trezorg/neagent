Neagent tracker
====================================

Tracks neagent announcements by search link
Requires python 3.6+


Dependencies
------------------------------------

* colorama
* lxml
* aiohttp
* cssselect
* daemons

Install
------------------------------------

    sudo apt-get install unixodbc unixodbc-dev libsqliteodbc

    git clone https://github.com/trezorg/neagent.git
    cd neagent
    python setup.py install

    or

    pip install . --user


Using
------------------------------------

    neagent --help
