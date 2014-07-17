# Retrieve papers from arXiv and post the most recent ones
# Gonzalo

import urllib2
from BeautifulSoup import BeautifulSoup
import re
import pandas as pd
from datetime import datetime, timedelta, date
import tweepy
import sys
import getopt
import time


class papers(object):

    def __init__(self, subjects, max_results):
        self.subjects = subjects
        self.max_results = max_results
        self.raw = None
        self.data = None


    def __getitem__(self, key):
        return self.data[key]


    def get(self):
        baseurl = 'http://export.arxiv.org/api/query?search_query=cat:'
        results = '&start=0&max_results={0}'.format(self.max_results)
        sorting = '&sortBy=submittedDate&sortOrder=descending'
        url = baseurl + '+OR+'.join(self.subjects) + results + sorting
        data = urllib2.urlopen(url).read()
        
        fulldoc = BeautifulSoup(data)
        self.raw = fulldoc.findAll('entry')


    def parse(self):

        def _clean_string(string):
            string = unicode(string).encode('utf-8')
            return re.sub('\n[ ]?', '', string)

        self.data = [{'time': i.published.text,
                    'title': _clean_string(i.title.text),
                    'link': i.id.text}
                     for i in self.raw]

    def validate(self, paper):
        def _prev_weekday(adate): 
            ''' from here: 
            http://stackoverflow.com/questions/12053633/previous-weekday-in-python
            '''
            adate -= timedelta(days=1)
            while adate.weekday() > 4:
                adate -= timedelta(days=1)
            return adate

        curr = datetime.strptime(paper['time'], '%Y-%m-%dT%H:%M:%SZ').date()
        return _prev_weekday(date.today()) == curr


    def output(self):
        self.parse()
        self.data = [i for i in self.data if self.validate(i)]


class tweet(object):

    def __init__(self, credentials, data):
        creds = pd.read_csv(credentials, header=None)
        auth = tweepy.OAuthHandler(creds.ix[0, 1], creds.ix[1, 1])
        auth.set_access_token(creds.ix[2, 1], creds.ix[3,1])
        self.api = tweepy.API(auth)
        self.data = data
        self.tweets = None

    def __getitem__(self, key):
        return self.data[key]

    def create_tweets(self):
        def _shorten(string):
            if len(string) > 121:
                string = string[0:118] + '...'
            return(string)
        self.tweets = ['{0} {1}'.format(_shorten(i['title']), i['link']) 
                       for i in self.data]
        

    def publish(self, sleeptime):
        if self.tweets:
            for i in self.tweets:
                try:
                    self.api.update_status(i)
                    print 'Status: "' + i[0:50] + '" succesfully tweeted'
                except tweepy.TweepError as e:
                    print e
                    time.sleep(sleeptime)
        else:
            print 'No tweet to publish'


def main(argv):
    max_results = 50
    subjects = ('stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.TH')
    publish = True
    try:
        opts, args = getopt.getopt(argv, 'c:m:n')
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'arxivbot.py -c <str> -m <int> -n'
            sys.exit()
        if opt == '-c':
            credentials = str(arg)
        if opt == '-m':
            max_results = int(arg)
        if opt == '-n':
            publish = False
    data = papers(subjects, max_results)
    data.get()
    data.output()

    tw = tweet(credentials, data)
    tw.create_tweets()
    if publish:
        tw.publish(60*10)
    else:
        for i in tw.tweets:
            print i + '\n'


if __name__ == "__main__":
    main(sys.argv[1:])
