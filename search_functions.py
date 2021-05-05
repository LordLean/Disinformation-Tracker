# -*- coding: utf-8 -*-
import os
import tweepy as tw
import pandas as pd

import tqdm
import string

import requests 
from bs4 import BeautifulSoup, SoupStrainer

# Top-level-domain extractor package.
from tldextract import extract

# Unidecoder
from unidecode import unidecode

# Download data collection.py
from data_collection import get_feedly_data, get_feedparser_data

# Download link previewer. 
from linkpreview import link_preview


"""## Standalone functions.

"""

def convert_urls(links):
  """
  Pull extended url str from str(dictionary) objects.
  """
  if links:
    if links[0] == "{":
      links = eval(links)
      links = links["expanded_url"]
  return links


def url_parse(url):
  """
  Parse url to its top level domain.
  """
  try:
    tsd, td, tsu = extract(url)
    return td + "." + tsu
  except TypeError:
    pass # Not all tweets have a url object.



"""# Twitter Search

## Search Functions

### Twitter Search Function
"""

def twitter_search(query_, result_type, max_tweets, language, api):
  # API Search - https://docs.tweepy.org/en/latest/api.html - ctrl+f "Search Methods"
  tweets = tw.Cursor(api.search,
                    q = query_,
                    result_type = result_type,
                    lang = language,
                    tweet_mode = "extended",
                    include_entities = True
                    ).items(max_tweets)

  # Pull info from tweets iterable.
  final_list = []
  for tweet in tweets:
    if hasattr(tweet, "retweeted_status") and tweet.entities["urls"]:
      tweet_info = [tweet.full_text, str(tweet.entities["urls"][0]), tweet.created_at, tweet.id_str, tweet.user.id_str, tweet.user.location, tweet.lang, tweet.source, tweet.retweeted_status.created_at, tweet.retweeted_status.id_str, tweet.retweeted_status.user.id_str, tweet.retweeted_status.user.location, tweet.retweeted_status.lang, tweet.retweeted_status.source, tweet.is_quote_status, hasattr(tweet, "retweeted_status"), tweet.retweet_count]
      final_list.append(tweet_info)
    elif not hasattr(tweet, "retweeted_status") and tweet.entities["urls"]:
      tweet_info = [tweet.full_text, tweet.entities["urls"][0]["expanded_url"], tweet.created_at, tweet.id_str, tweet.user.id_str, tweet.user.location, tweet.lang, tweet.source, None, None, None, None, None, None, tweet.is_quote_status, hasattr(tweet, "retweeted_status"), tweet.retweet_count]
      final_list.append(tweet_info)
    elif hasattr(tweet, "retweeted_status") and not tweet.entities["urls"]:
      tweet_info = [tweet.full_text, None, tweet.created_at, tweet.id_str, tweet.user.id_str, tweet.user.location, tweet.lang, tweet.source, tweet.retweeted_status.created_at, tweet.retweeted_status.id_str, tweet.retweeted_status.user.id_str, tweet.retweeted_status.user.location, tweet.retweeted_status.lang, tweet.retweeted_status.source, tweet.is_quote_status, hasattr(tweet, "retweeted_status"), tweet.retweet_count]
      final_list.append(tweet_info)
    elif not hasattr(tweet, "retweeted_status") and not tweet.entities["urls"]:
      tweet_info = [tweet.full_text, None, tweet.created_at, tweet.id_str, tweet.user.id_str, tweet.user.location, tweet.lang, tweet.source, None, None, None, None, None, None, tweet.is_quote_status, hasattr(tweet, "retweeted_status"), tweet.retweet_count]
      final_list.append(tweet_info)

  # Create dataframe for specified above information.
  df = pd.DataFrame(final_list,columns=["Full Text", "Tweet Links", "RT Datetime", "RT Id", "RT User Handle", "RT User Location", "RT User Language", "RT User Source", "Orig Datetime", "Orig Tweet Id", "Orig User Handle", "Orig User Location", "Orig User Language", "Orig User Source", "IsQuoteRetweet", "IsRetweet", "RetweetCount"])
  # Pull all extended urls.
  df["Tweet Links"] = df["Tweet Links"].apply(lambda links: convert_urls(links))

  return df


"""### Disinformation Event Search Function"""
# import streamlit as st
# @st.cache()
def event_search(event_dict, query=None, cursor_args={}):
  """
  For a given event/news item: search for query then search all urls returned from initial query.
  Store all search results in the passed news_item dictionary in newly created keys. 
  Keys:
    "keywords" : Ranked sets of keywords. 
    "query" : Keywords formatted for Twitter's search API.
    "dataframe" : Dataframe housing initial search results (using keyword query).
    "domains" : For housing url specific search queries, grouped by top-level domains.
  Function augments passed new_item dict with new keys and values.
  """
  # Pull article headline.
  headline = event_dict["headline"]
  # Build query from keywords - unidecode to handle any special chars for twitter query.
  event_dict["query"] = unidecode(" ".join(event_dict["keywords"])) if query == None else unidecode(query)
  # Create outer dictionary to store url specific information.
  event_dict["domains"] = {}
  # Create outer sources dictionary.
  event_dict["sources"] = {}

  # Run twitter search, store resultant dataframe in dictionary.
  event_dict["dataframe"] = twitter_search(
    event_dict["query"],
    result_type = cursor_args.get("result_type","mixed"),
    max_tweets = cursor_args.get("initial_tweet_count", 500),
    language = cursor_args.get("language","en"),
    api = cursor_args.get("api")
  )
  # Get all unique links used in tweets collection.
  urls = event_dict["dataframe"]["Tweet Links"].value_counts().index.to_list()
  for url in urls:
    try:
      if url is not None:
        # Get top-level-domain per url.
        tld = url_parse(url)
        if tld == "twitter.com":
          # Skip url searches if twitter.com features.
          continue
        # Use full url as search query argument.
        url_queried_df = twitter_search(
          query_="url:{}".format(url),
          result_type = cursor_args.get("result_type","mixed"),
          max_tweets = cursor_args.get("url_specific_tweet_count", 50),
          language = cursor_args.get("language","en"),
          api = cursor_args.get("api")
        )
        # If unseen top level domain, create inner dictionary.
        if tld not in event_dict["domains"].keys():
          event_dict["domains"][tld] = {url : url_queried_df}
        # If previously seen top level domain, add to inner dictionary.
        else:
          event_dict["domains"].get(tld)[url] = url_queried_df
    # Handles tweepy 403 errors. Certain urls cannot be searched.
    except tw.TweepError: # Alternatively could just PASS FOR CONSISTENCY.
      # If not the first unsearchable url, add url as dict key with nonetype value.
      if "unsearchable_urls" in event_dict["domains"]:
        event_dict["domains"].get("unsearchable_urls")[url] = None
      # If first unsearchable url, create dict with url as key and nonetype value.
      else:
        event_dict["domains"]["unsearchable_urls"] = {url : None}

  # Store grouped relevant infromation in easy access location.
  # Create group specific list objs.
  event_dict["sources"]["youtube"] = []
  # event_dict["sources"]["twitter"] = [] # Twitter is removed as this contains specific links to user.
  event_dict["sources"]["articles"] = []  
  for key in event_dict["domains"].keys():
    # Match keys into categories and extend empty lists to include lower level domains.
    if key in ["youtube.com", "youtu.be"]:
      ext = list(event_dict["domains"][key].keys())
      event_dict["sources"]["youtube"].extend(ext)
    # if key in ["twitter.com"]: # As before - Twitter links are removed to protect Twitter user anonymity.
    #   ext = list(event_dict["domains"][key].keys())
    #   event_dict["sources"]["twitter"].extend(ext)
    else:
      ext = list(event_dict["domains"][key].keys())
      event_dict["sources"]["articles"].extend(ext)

  # Suggested articles:
  event_dict=event_suggested_articles(event_dict,cursor_args.get("api"))

  return event_dict


"""# Extensions"""

def get_active_users(df, num=2):
  """
  Return list of tuples (user, occurence) of the "num" of most observed users for a twitter_search dataframe.
  For use in event_active_users function.
  """
  if df is not None:
    # Get most active from "orig user handle" column.
    series_orig = df.loc[:, "Orig User Handle"].value_counts()
    tuples_orig = [tuple((handle,count)) for handle, count in series_orig.items()]
    # Get most active from "rt user handle" column.
    series_rt = df.loc[:, "RT User Handle"].value_counts()
    tuples_rt = [tuple((handle,count)) for handle, count in series_rt.items()]
    return tuples_orig[:num] + tuples_rt[:num]


def event_active_users(event_dict, num=3):
  """
  Return dictionary object containing top level domains as keys and lists of observed active users of length "num".
  """
  tld_user_dict = {}
  # Order information hierarchy similar to what's present in top_level_domains.
  for key in event_dict["domains"]:
    # Ignore unsearchable_urls, this key has no dataframes attached to it (as it was unsearchable).
    if key != "unsearchable_urls":
      # Running list of screen name and occurences count. This will span all dataframes under a single top_level_domain. 
      running_list = []
      for inner_key in event_dict["domains"][key]:
        # Get the url specific dataframe.
        url_specific_df = event_dict["domains"][key][inner_key]
        # Call function to get most active users from a url specific dataframe.
        running_list.extend(get_active_users(url_specific_df))
      # Ignore if only one user to draw data from - system requires aggregated user data to protect anonymity.
      if len(running_list) > 1:
        # Get unique totals from the running list. 
        running_dict = {}
        for screen_name, count in running_list:
          # If screen name is already seen in another df, add the occurences (value) to the original key.
          if screen_name in running_dict:
            running_dict[screen_name] = running_dict.get(screen_name) + count
          # Else create key with count value in running_dict.
          else:
            running_dict[screen_name] = count
        # Sort the observed most active users for a single top_level_domain. Select the first "num" amount of users per key.
        sorted_users_occurences = sorted(running_dict.items(), key = lambda x: x[1], reverse=True)[:num]
        users = [user for user, count in sorted_users_occurences]
        tld_user_dict[key] = users
  return tld_user_dict


def get_suggested_articles(user_list,api,count=50):
  articles_list = []
  for user in user_list:
    statuses = tw.Cursor(api.user_timeline, id=user).items(count)
    articles_list.extend([tweet.entities["urls"][0]["expanded_url"] for tweet in statuses if tweet.entities["urls"] and "twitter" not in tweet.entities["urls"][0]["expanded_url"]])
  return articles_list


def event_suggested_articles(event_dict, api):
  # Create inner dictionary to hold articles.
  event_dict["suggested_articles"] = {}
  # Get dictionary of top level domain, active users list. 
  tld_user_dict = event_active_users(event_dict)
  for tld, user_list in tld_user_dict.items():
    # Augment event_dict with new key, suggested_articles. This contains a list of articles these users also have shared on their timeline. 
    event_dict["suggested_articles"][tld] = list(set(get_suggested_articles(user_list,api=api)))
  return event_dict



import streamlit as st
@st.cache()
def get_link_preview(link):
  """
  Return information for displaying generic datacard for web link.
  """
  try:
    preview = link_preview(link,parser="lxml")
    return {
        "title":preview.title,
        "description":preview.description,
        "image":preview.image,
        "force_title":preview.force_title,
        "absolute_image":preview.absolute_image,
        "link":link
    }
  except:
    pass
