# -*- coding: utf-8 -*-
import csv
import MySQLdb as mdb
import re
import urllib2
import urlparse
import requests
import string
import sys
import os
import urllib
import json
import time

# Put your own API here
face_api = '1bc17f562f65b08ea49e6a0bf70ec9b6'
face_secret = 'xiPAiwbRpFt_pAdCVi72zHk6vWigyWsu'
api_url = 'http://apicn.faceplusplus.com/v2/detection/detect'
out_file = open('detailedfaceresult.csv', 'wb')
csv_file = csv.writer(out_file)
csv_file.writerow(['main_url', 'url', 'face_id', 'gender', 'race', 'age', 'smiling'])

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0',
}

try:
    conn = mdb.connect('localhost', 'root', '123456', 'test_python')
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS faceplusplus")
    cur.execute("""CREATE TABLE faceplusplus(
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    main_url VARCHAR(255),
                    url VARCHAR(255),
                    face_id VARCHAR(255),
                    gender VARCHAR(10),
                    race VARCHAR(50),
                    age INT,
                    smiling VARCHAR(50)) """)
except mdb.Error, e:
    print e


#get the url and return json format data
def message(url, main_url):
    get_data = {
        'api_key': face_api,
        'api_secret': face_secret,
        'url': url,
        'attribute': 'glass,pose,gender,age,race,smiling'
    }
    response = requests.get(api_url, params=get_data, headers=headers)
    '''
    response = urllib2.urlopen(
        'http://apicn.faceplusplus.com/v2/detection/detect?api_key=' + face_api + '&api_secret=' + face_secret + '&url=' + url + '&attribute=glass,pose,gender,age,race,smiling')
    data = json.loads(response.read())
    '''
    data = response.json()
    try:
        url = data['url']
        #print data
        for face in data['face']:
            gender = face['attribute']['gender']['value']
            age = face['attribute']['age']['value']
            race = face['attribute']['race']['value']
            smiling = face['attribute']['smiling']['value']
            face_id = face['face_id']
            main_url = main_url
            print main_url, url, face_id, gender, race, age, smiling
            csv_file.writerow([main_url, url, face_id, gender, race, age, smiling])
            try:
                cur.execute("""INSERT INTO faceplusplus(main_url, url, face_id, gender, race, age, smiling)
                            VALUES(%s, %s, %s, %s, %s, %s, %s)""", [main_url, url, face_id, gender, race, age, smiling])
            except mdb.Error, e:
                print e
                cur.rollback()

    except Exception, e:
        print e

# crawl webpage to get all jpg image urls, we need fake ourselve as http header request
# or we need limit the number of images to analyze to avoid the request block.
def imgs(url, limit=10):
    imgcontent = requests.get(url, headers=headers).text  #crawl your webpage content
    #urllist = re.findall(r'http.+?\.jpg', imgcontent, re.I)  #analyze img urls
    urllist = re.findall(r'<img.*src=\"(.*?\.jpg|gif|png)\"', imgcontent, re.I)  #analyze img urls
    print urllist
    if not urllist:
        print 'images for this url are not found...'
    else:
        url_set = set(url for url in urllist) # duplicate filter
        url_set = list(url_set)
        url_length = len(url_set)
        # if limit is 0, it will crawl all pics in webpage
        if limit == 0:
            limit = url_length
        if limit > url_length:
            limit = url_length
        for x, imgurl in enumerate(url_set[:limit]):
            if 'http' not in imgurl:
                imgurl = urlparse.urljoin(url, imgurl)
            print imgurl
            print u'Processing the %sth pictures...' % str(x+1)
            message(imgurl,url)
            #time.sleep(3)


if __name__ == "__main__":
    #Open the wesite url you want to analyze or open a file with urls
    with open('url_data.txt', 'rb') as F:
        for line in F.readlines():
            print line
            print line.split()
            url, limit = line.split()
            imgs(url, int(limit))
    out_file.close()
    conn.commit()
    conn.close()

    '''
        txt file should be like this
        http://www.sina.com.cn 10
        http://www.sohu.com    15
        ....
    '''
