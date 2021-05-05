# -*- coding: utf-8 -*-
import streamlit as st

import json
import datetime
from time import mktime
import sklearn

import feedparser

import requests
from bs4 import BeautifulSoup

################################
# News classifier:
import string
import nltk

nltk.download("stopwords", quiet=True)
# try:
#   nltk.download("wordnet", quiet=True)
# except:
#   nltk.download("wordnet", quiet=True)

from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem import SnowballStemmer

import pickle
multi_nb_clf = pickle.load(open("pickled/news_class_clf.pickle","rb"))
tfidf_vectorizer = pickle.load(open("pickled/news_class_vect.pickle","rb"))
ix_to_cat = pickle.load(open("pickled/ix_to_cat_map.pickle", "rb"))

# Set-up for preprocessing text.
STOP = set(stopwords.words("english")+["politifact", "factcheck", "no", "factchecking"])
PUNC = set(string.punctuation)
lemma = WordNetLemmatizer()
snow_stemmer = SnowballStemmer("english")

################################


# Install keyword extractor package.
from rake import Rake
# Initialize Rake obj.
raker = Rake()


################################

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in STOP])
    punc_free = ''.join(ch for ch in stop_free if ch not in PUNC)
    normalized = " ".join(snow_stemmer.stem(lemma.lemmatize(word)) for word in punc_free.split())
    return normalized

################################

def convert_to_datetime(ms):
  """
  Convert ms to timestamp.
  """
  return datetime.datetime.fromtimestamp(ms).strftime('%Y-%m-%d %H:%M:%S')

################################

def keyword_extraction(text, n=10):
  """
  Run the RAKE algorithm on the text.
  Returns ranked keywords.
  """
  raker.load(text, STOP)
  return [x[0] for x in raker.get_ranked_keywords(top_n=n)]
  
################################



"""# Feedly"""

@st.cache()
def get_feedly_data(item_count=5, feedly_keys={}):
  """
  Pull feedly headlines. 
  """
  # Get access token and userID for authenticating and pulling feedly headlines.
  access_token = feedly_keys.get("access_token")
  user_id = feedly_keys.get("user_id")

  selection = "user/{}/category/global.all".format(user_id)
  url = "http://cloud.feedly.com/v3/streams/contents?streamId=" + selection + "&count=" + str(item_count)
  headers = {'Authorization': 'OAuth ' + access_token}
  response = requests.get(url=url, headers=headers)
  news = response.json()
  return [{"headline" : item["title"],
           "topic": ix_to_cat[multi_nb_clf.predict(tfidf_vectorizer.transform([clean(item["title"] + BeautifulSoup(item["summary"]["content"],"lxml").get_text())]))[0]],
           "summary" : BeautifulSoup(item["summary"]["content"], "lxml").get_text(),
           "date" : convert_to_datetime(item["published"]/1000),
           "link" : item["originId"],
           "keywords" : keyword_extraction(item["title"])
           }
           if "summary" in item else
           {"headline" : item["title"],
           "topic": ix_to_cat[multi_nb_clf.predict(tfidf_vectorizer.transform([clean(item["title"])]))[0]],
           "summary" : "No Content",
           "date" : convert_to_datetime(item["published"]/1000),
           "link" : item["originId"],
           "keywords" : keyword_extraction(item["title"])
           }
           for item in news["items"]]

"""# FeedParser """

@st.cache()
def get_feedparser_data(feed):
  """
  Return published date and title. 
  Example accepted feeds: 
  http://fetchrss.com/rss/603d5db627c7f627e1734842603d6346fd9fd74dae2c2ce2.xml, 
  https://www.truthorfiction.com/category/fact-checks/disinformation/feed/
  """
  NewsFeed = feedparser.parse(feed)
  return [{"headline" : entry.title,
           "date" : convert_to_datetime(mktime(entry.published_parsed)),
           "link" : entry.link,
           "summary" : BeautifulSoup(entry["summary"],"lxml").get_text(),
           "topic": ix_to_cat[multi_nb_clf.predict(tfidf_vectorizer.transform([clean(entry.title +  BeautifulSoup(entry["summary"],"lxml").get_text())]))[0]],
           } for entry in NewsFeed.entries]

# @st.cache()
def create_event_dict(text):
  return {
    "headline" : text,
    # "keywords" : keyword_extraction(text),
    "topic": ix_to_cat[multi_nb_clf.predict(tfidf_vectorizer.transform([clean(text)]))[0]],
  }
  