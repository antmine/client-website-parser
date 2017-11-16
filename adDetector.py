#!/usr/bin/env python2.7

#lib to query a website
import urllib2
import os
import json
import sys
import datetime;
#beautifulSoup4 lib to parse data from imported website
from bs4 import BeautifulSoup

from urllib import FancyURLopener
from random import choice
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, Table, update


with open('./conf/' + os.getenv('CONFIG_FILE', 'config') + '.json', 'r') as f:
	configData = json.load(f)

#create the connection with mysql db
engine = create_engine(configData["SQL"]["type"]+configData["SQL"]["user"]+':'+configData["SQL"]["password"]+'@' + configData["SQL"]["url"]+'/'+configData["SQL"]["databaseName"], convert_unicode=True)
metadata = MetaData(bind = engine)

#loads all the WEBSITE table details
adminWebsiteTable = Table("WEBSITE", metadata, autoload=True)

Session = sessionmaker(bind=engine)
connection = engine.raw_connection()
con = engine.connect()



try:
    cursor = connection.cursor()
    cursor.callproc("GET_WEBSITE_TO_CHECK", [configData["nbDaysCheck"]])
    result = list(cursor.fetchall())
    cursor.close()
    connection.commit()
except:
	print ("Unexpected error:", sys.exc_info()[1])
finally:
    connection.close()

user_agents = [
   'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
   'Opera/9.25 (Windows NT 5.1; U; en)',
   'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
   'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
   'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
   'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9'
]

class MyOpener(FancyURLopener, object):
    version = choice(user_agents)

myOpener = MyOpener()
print('result ==>', result)
for website in result:
    try:
        page = myOpener.open(website[1])
        soup = BeautifulSoup(page, "html.parser")
        soup.prettify()
        date = datetime.datetime.now()
        session = Session()
        if not soup.script.string:
            print "no ads"
            update = update(adminWebsiteTable)
            update = update.values({"DATE_CHECK": date.strftime("%Y-%m-%d %H:%M"), "IS_ENABLE": 1})
            update = update.where(adminWebsiteTable.c.ID_WEBSITE == website[0])
            session.execute(update)
            session.commit()
        else:
            print "website " + website[0] + " script balise present"
            if "ads" in soup.script.string:
                update = update(adminWebsiteTable)
                update = update.values({"DATE_CHECK": date.strftime("%Y-%m-%d %H:%M"), "IS_ENABLE": 0})
                update = update.where(adminWebsiteTable.c.ID_WEBSITE == website[0])
                session.execute(update)
                session.commit()
                print "website " + website[0] + " contains ads"
        session.close()
    except urllib2.HTTPError,e:
        print e.fp.read()
