## Retrieve papers from arXiv and post the most recent ones
## Gonzalo

import urllib2
from BeautifulSoup import BeautifulSoup
import re
from datetime import datetime, timedelta
import tweepy
import sys, getopt, time

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
api = tweepy.API(auth)

def get_papers(max_results):
    baseurl = 'http://export.arxiv.org/api/query?'
    subjects = ('stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.TH')
    results = '&start=0&max_results={0}'.format(max_results)
    sorting = '&sortBy=submittedDate&sortOrder=descending'    
    url = baseurl + 'search_query=cat:' + '+OR+'.join(subjects) + results + sorting
    data = urllib2.urlopen(url).read()
    
    fulldoc = BeautifulSoup(data)
    papers = fulldoc.findAll('entry')
    return papers

def clean_string(string):
    string = unicode(string).encode('utf-8')
    return re.sub('\n[ ]?', '', string)

def parse_paper(papers):
    titlink = [{'time': i.published.text, 
                'title': clean_string(i.title.text),
                'link': i.link['href']} 
               for i in papers]
    return(titlink)

def valid_paper(paper, diff):
    diff = timedelta(hours=diff)
    curr = datetime.strptime(paper['time'], '%Y-%m-%dT%H:%M:%SZ') 
    return datetime.now() - curr < diff

def subset_papers(papers, diff):
    return [i for i in papers if valid_paper(i, diff)]

def shorten(string):
    if len(string) > 121:
        string = string[0:118] + '...'
    return(string)
        
def create_tweets(max_tweets, how_old):
    data = get_papers(max_tweets)
    papers = parse_paper(data)
    papers = subset_papers(papers, how_old)
    return ['{0} {1}'.format(shorten(i['title']), i['link']) for i in papers]

def publish_tweets(api, tweets, sleeptime):
    if tweets:
        for i in tweets:
            try:
                api.update_status(i)
                print 'Status: "' + i[0:50] + '" succesfully tweeted'
            except tweepy.TweepError as e:
                pass
            time.sleep(sleeptime)

def main(argv):
    max_tweets = None
    how_old = None
    try:
        opts, args = getopt.getopt(argv, 'hm:d:' ,['maxtweets=','delta='])
    except getopt.GetoptError:
        print 'test.py -m <maxtweets> -d <deltatime>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -m <maxtweets> -d <delta>'
            sys.exit()
        elif opt in ("-m", "--maxtweets"):
            max_tweets = int(arg)
        elif opt in ("-d", "--delta"):
            how_old = int(arg)
    tweets = create_tweets(max_tweets, how_old)
    publish_tweets(api, tweets, 60*30)

if __name__ == "__main__":
    main(sys.argv[1:])
