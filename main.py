import streamlit as st
from streamlit_agraph import agraph, Node, Edge, TripleStore, Config

import numpy as np
import pandas as pd
import random
import json
import glob
import sklearn

from data_collection import get_feedly_data, get_feedparser_data, create_event_dict, keyword_extraction

from search_functions import event_search, twitter_search, get_link_preview

from linkpreview import link_preview

import tweepy as tw


import plotly.graph_objects as go



st.set_page_config(
    layout="wide",
    page_title="Disinformation Tracker",
    page_icon="🌎"
    )

##################################
# Global args.
##################################
# Define search args dict.
cursor_args = {
    "result_type" : "mixed",
    "language" : "en",
    "exclude" : "",
    "initial_search_count" : 50,
    "url_search_count" : 10
}

arg_map = {
    "English" : "en",
    "Spanish" : "es",
    "Russian" : "ru"
}

#################################
# Keys:

feedly_keys = {
}
##################################
# Global args - end
##################################


###########################################
# Sidebar
###########################################
st.sidebar.title("Application Settings Menu")

# Sidebar key upload
st.sidebar.markdown("[Example Keys input file](https://raw.githubusercontent.com/LordLean/Tracking-Sources-Of-Online-Disinformation/main/keys_example.json?token=AOI52XFBSULLS3PD542GIH3ASKV6K)")


# Collects user input features into dataframe
uploaded_file = st.sidebar.file_uploader("Upload your keys file", type=["json"])
if uploaded_file is not None:
    data = json.load(uploaded_file)
    feedly_keys = data.get("feedly", {})
    twitter_keys = data.get("twitter")
    if not len(twitter_keys):
        st.warning("No Twitter Keys Detected")
    else:
        consumer_key = twitter_keys.get("consumer_key") 
        consumer_secret = twitter_keys.get("consumer_secret") 
        access_token = twitter_keys.get("access_token") 
        access_token_secret = twitter_keys.get("access_token_secret") 
try:
    # Authenticate
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=False)
    cursor_args["api"] = api
except:
    pass






user_specified_domain = st.sidebar.text_input("Enter a News Website's Domain")

adv_choice = st.sidebar.selectbox("Select Twitter Search Parameters", ["Default", "Advanced"])
with st.sidebar:
    if adv_choice == "Advanced":

        c1, c2 = st.beta_columns(2)
        lang_option = c1.radio("Language", options=["English", "Spanish", "Russian"])
        cursor_args["language"] = arg_map.get(lang_option, "en")

        result_option = c2.radio("Result Type", options=["Mixed", "Popular", "Recent"])
        cursor_args["result_type"] = result_option.lower()

        cursor_args["initial_search_count"] = st.slider("Initial Search Maximum Number of Tweets", min_value=50, max_value=5000, step=50)
        cursor_args["url_search_count"] = st.slider("URL Specifc Maximum Number of Tweets", min_value=10, max_value=5000, step=10)

        cursor_args["exclude"] = st.text_input("Exclude Words")

###########################################
# Sidebar - end.
###########################################



###########################################
# Title
###########################################
title = "Disinformation Tracking Tool"
st.markdown("<h1 style='text-align: center; color: white;'>{}</h1>".format(title), unsafe_allow_html=True)
# st.markdown("<h3 style='text-align: center; color: #0E1117;'>{}</h3>".format(title), unsafe_allow_html=True)
st.text("")
st.text("")
###########################################
# Title - end
###########################################



###########################################
# Expander
###########################################
with st.beta_expander("Let's find some facts and some fiction!"):
    st.write("""
    Welcome to the Disinformation Tracking Tool  

    Thanks for choosing to use this application. This tool was designed as part of project for an undergraduate computer science degree from the University of Sussex. The goal was to create an application that would allow its users to jump straight into examining the diffusion of news through the Twitter platform.  
    
    Specifically this project targets disinformation (deliberately deceptive false news) however the tool can be used to search for anything you please! The quering function that searches Twitter operates the same as it does within Twitter's applications - we just make it easier for you to specify what's relevant information to you!

    Some information to get you started! The three columns below take you through the different parts of the application and provide helpful links to further documentation. 
    """)

    col1, _, col2, _, col3 = st.beta_columns((8,1,8,1,8))
    col1.markdown("<h2 style='text-align: center; color: white;'>{}</h2>".format("The Sidebar <br/>"), unsafe_allow_html=True)
    col2.markdown("<h2 style='text-align: center; color: white;'>{}</h2>".format("Querying <br/>."), unsafe_allow_html=True)
    col3.markdown("<h2 style='text-align: center; color: white;'>{}</h2>".format("Results <br/>."), unsafe_allow_html=True)

    col1.markdown("""
    * Controls application + search settings.
    * Upload keys using uploader widget.
        * Twitters keys are essential.
        * The Feedly key and user ID are so you can specify your own curated RSS news feed. 
    * If you do not submit a Feedly that is fine just remove that object from the keys file and leave the Twitter keys in the same format as the example.
    * Enter a News Website's domain takes a domain as per the example under the User Specified news column below.
    * Two options for Twitter Search parameter settings. Default and Advanced.
        * Default:
            * English language
            * Results are of the "mixed" type rather than recent or popular.
            * Initial search is set to max 500 Tweets (see querying section for what this means).
            * Url specific search is set to 50 Tweets. 
            * No words excluded
        * Advanced:
            * Radio options to control language and result type.
            * Sliders control counts of max Tweets desired.
            * Exclude text input tells Twitter search this is not a desired term and that returned results should not include the term(s).
            * Above can also be achieved by prefixing a "-" to a not desired word in query box.
        * [Twitter Documentation](https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/api-reference/get-search-tweets)
        * Twitter's standard search [operators](https://developer.twitter.com/en/docs/twitter-api/v1/rules-and-filtering/search-operators)
        

    """)

    col2.markdown("""
    * This application is built for those using Twitters v1 Standard Search API. The back-end leverages [Tweepy](https://www.tweepy.org/) and is not currently compatiable with the premium and enterprise APIs - to the best of my knowledge.
    * Enter queries in the event search text input.
    * This application performs its search by querying for an initial dataframe using the passed query. All unique links contained within the returned Tweets are then stored and used as URL queries for further Twitter Searches. The distribution of the URL specific searches is the data displayed in the graph visualization.
        * For example: If your initial search was only 100 Tweets, but all 100 contained unique links and you had then set your URL specific search to 50, you could end up finding 5000 Tweets.
        * Be wary as this is an easy way to max out your API limit, especially on Standard Search. 
    * Save query button will store that query into the variable passed to the search button so please ensure you save a query anytime you want to search lest you accidently search a previous query.
    * Selecting save query will also present you with suggested keywords using the [RAKE](https://github.com/LordLean/RAKE) algorithm. It is recommended you use these to get more general search results. Twitter's search splits queries by whitespace and treats those spaces as logical AND. I.e. Biden has Kittens will return Tweets containing biden AND kittens and has.
    * You can use the urls or headlines provided below in the news sections for inspiration for searches - with the exception of those who have the Feedly connectors, this works by web syndication (RSS parsers) of the revelant news websites. These columns are split by:
        * General news
        * False claim fact checks
        * User specified
    * User specified column gives examples. These can be copy and pasted directly into the sidebar text input. To check outside of the app whether a specific site has such a feed look for the orange RSS symbol or enter "/feed" or "/rss" at the end of the URL. Alternatively enter it here and we'll do it for you.
    * Using the exclude words field in the sidebar adds those strings to the query however with a "-" prefixed.
    """)

    col3.markdown("""
    * Three visualizations appear after a search, along with suggested articles curated from aggregate lists of users who have been sharing similar material to your query.
    * The main visualization is an interactive graph built using the [agraph](https://github.com/ChrisChross/streamlit-agraph) component for Streamlit - thank you C.Klose for that. This graph has the following structure:
    
        |Node Class |Colour |Size (1-5, 1 being largest)|
        |---|--|--:|
        |Headline/Query |Red |1|
        |Topic Classification| Yellow| 2|
        |Domain Name| Light Green |3|
        |URL |Dark Green| 4|
        |Datetime of Tweet| Dark Red/Brown|5|

    * Individual Tweet objects and overly identifying content (i.e. text/userIDs) are not accessible - this was out of the scope the research project this was built for.
    * The other two plots use Plotly's graphing libraries.
        * Time series bar graph for frequency of Tweets split by domain.
            * Can isolate specific time frames and domains. 
            * I recommend taking a minute to explore the chart and its capabilities.
            * Or refer to Plotly's documentation.
        * Radial Plot shows overall Tweet sentiment from all Tweets discovered in your search.
            * This uses the [VADER](https://www.aaai.org/ocs/index.php/ICWSM/ICWSM14/paper/view/8109) model for classification.
            * Tweets are classified by their polarity and strength of emotion.
            * This is generally well suited for social media analysis.
    """)
    st.write("")
    st.write("")
    st.markdown("""
    Lastly a huge thanks to the Streamlit team. Not only are their applications incredibily aestheic and high performing but they also have one of the nicest online communities out there.
    Strongly recommend anyone, especially those who wish to maximise the potential of their machine learning or data science workflows, to check out Streamlit and the technologies Streamlit has to offer.
    """)
###########################################
# Expander - end
###########################################




###########################################
# Query + Keywords
###########################################

# Define query columns
query_col, search_col = st.beta_columns((8,2))

# query = query_col.text_input('Event Search', value="Type or Paste Query Here", max_chars=150)

# Form container prevents the keywords displayed below from being augmented until the user reselects
# the form_submit_button.
form = query_col.form(key="Keyword Queries")
# Get query from Event Search input.
query = form.text_input('Event Search', value="Type or Paste Query Here", max_chars=150)

# Create event dictionary from query.
search_item = create_event_dict(query)

# Extract keywords.
k_words = keyword_extraction(search_item["headline"]) 
search_item["keywords"] = k_words

# Dynamically create columns based on amount of keywords.
if len(k_words) and query != "Type or Paste Query Here":
    num_cols = len(k_words)
    cols = st.beta_columns(num_cols)
    for i, (x_col, k_word) in enumerate(zip(cols, k_words)):
        x_col.markdown("""
        ```
        {}
        ```
        """.format(k_word))
k_button = form.form_submit_button(label="Save Query")

# Exclude words
exclude_words = ["-" + word for word in cursor_args["exclude"].split()]
search_item["query"] = query + " " + " ".join(exclude_words)



###########################################
# Query + Keywords - end
###########################################




###########################################
# Analysis Slot def
###########################################
# This is where the graph and plot components will be placed.
zero_query = st.empty()
analysis_graph_slot = st.empty()
analysis__plot_slot = st.empty()
suggested_articles_slot_title = st.empty()
suggested_articles_slot = st.empty()
###########################################
# Analysis Slot def
###########################################




###########################################
# Experimental Visualizations
###########################################

#############################################
def show_graph(event_dict):
    # Create node + edge lists.
    nodes = []
    edges = []
    # Create headline + topic nodes.
    headline_node = Node(id=event_dict["headline"], size=3000, color="#ee7772")
    topic_node = Node(id=event_dict["topic"], size=1500, color="#f2e3c4")
    # Add headline + topic nodes + edge connector to object lists.
    nodes.extend([headline_node, topic_node])
    edges.append(Edge(source=event_dict["headline"], target=event_dict["topic"], type="CURVE_SMOOTH", labelProperty="IsTopic"))
    # Get nodes IDs for each news domain.
    domains = list(event_dict["domains"].keys())
    # Create nodes for each news domain.
    nodes.extend([Node(id=domain, size=800) for domain in domains])
    # Connect each domain node to the headline. 
    edges.extend([Edge(source=event_dict["headline"], target=node, type="CURVE_SMOOTH", labelProperty="HasDomainPosting") for node in domains])
    # Iterate through each domain, through each specific url contained within, for each datetime within url specific dataframes.
    for domain in domains:
        for url in event_dict["domains"][domain].keys():
            nodes.append(Node(id=url,size=500, color="#2b4717"))#, renderLabel=False))
            edges.append(Edge(source=domain, target=url, type="CURVED_SMOOTH", color="#a6865c", labelProperty="HasSpecificUrl"))
            if event_dict["domains"][domain][url]["RT Datetime"] is not None:
                for timepoint in event_dict["domains"][domain][url]["RT Datetime"]:
                    timepoint_str = str(timepoint)
                    nodes.append(Node(id=timepoint_str, size=250, color="#653417", renderLabel=False))
                    edges.append(Edge(source=url, target=timepoint_str, type="CURVED_SMOOTH", labelProperty="PostsAtThisTime"))
                
    config = Config(width=3000, 
                    height=1000, 
                    directed=True,
                    nodeHighlightBehavior=True, 
                    highlightColor="#F7A7A6", # or "blue"
                    collapsible=False,
                    staticGraph = False,
                    staticGraphWithDragAndDrop=False,
                    ) 

    return_value = agraph(nodes=nodes, 
                        edges=edges, 
                        config=config)



def plotly_time_series(event_dict):
    holding = {}
    for domain, url_specific_dict in event_dict["domains"].items():
        merged = pd.concat([df["RT Datetime"] for df in url_specific_dict.values()])
        if len(merged):
            rounded = pd.Series(merged).dt.round("H")
            v_counts = rounded.value_counts()
            holding[domain] = v_counts
    data = [go.Bar(x = data_.index.to_list(), y = data_.to_list() ,name=domain_name,opacity = 0.8) for domain_name, data_ in holding.items()]
    fig = go.Figure(data)
    return fig
#############################################



#############################################
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download("vader_lexicon",quiet=True)
sid = SentimentIntensityAnalyzer()

def get_vader(sent):
  ss = sid.polarity_scores(sent)
  # del ss["compound"]
  return ss


def get_sentiment_plot(event_dict):
  main_sentiment = [get_vader(text) for text in event_dict["dataframe"]["Full Text"]]
  for domain, url_dicts in event_dict["domains"].items():
    for df in url_dicts.values():
      df_sentiment = [get_vader(text) for text in df["Full Text"]]
      main_sentiment.extend(df_sentiment)

  pos, neg, neu = [], [], []
  for sent_dict in main_sentiment:
    pos.append(sent_dict["pos"])
    neg.append(sent_dict["neg"])
    neu.append(sent_dict["neu"])

  pos_score = sum(pos) / len(pos)
  neg_score = sum(neg) / len(neg)
  neu_score = sum(neu) / len(neu)

  maximum = max([max(pos),max(neg),max(neg)])


  categories = ["Neutral", "Positive", "Negative"]

  fig = go.Figure()

  fig.add_trace(go.Scatterpolar(
        r=[neu_score, pos_score, neg_score],
        theta=categories,
        fill='toself',
        name='Tweet Sentiment'
  ))

  fig.update_layout(
    polar=dict(
      radialaxis=dict(
        visible=True,
      )),
    showlegend=False
  )

  return fig
#############################################




searched_item = None
search_col.markdown((""))
search_col.markdown((""))
if search_col.button("Search"):
    # Print check
    # st.write("Query Searched for: {}".format(query))
    # st.write(cursor_args)
    for excluded_word in cursor_args["exclude"].split():
        for word in query.split():
            if word == excluded_word:
                st.error("Invalid search - please avoid logical contridictions, do not use a query that also contains the exact string of the excluded word.")
                st.stop()
    with st.spinner("Running Search..."):
        try:
            searched_item = event_search(
                search_item,
                query=search_item["query"],
                cursor_args=cursor_args
                )
        except AttributeError:
            st.error("Unable to search - have you uploaded the required keys?")
            st.stop()
        except tw.TweepError as e:
            st.error(e)
            st.error("Unable to search - rate limit exceeded.")
            st.stop()
        

    with analysis_graph_slot.beta_container():
        # Print check
        # st.write(cursor_args)
        st.text("")
        with st.spinner("Loading Graph..."):
            try:
                show_graph(searched_item)
            except TypeError:
                st.error("Sorry your search returned 0 results. Please try a different query.")
    time_plot, radar_plot = analysis__plot_slot.beta_columns((2,1))

    plot_font_size = 14
    with time_plot:
        fig = plotly_time_series(searched_item)
        fig.update_layout(
            title = dict(
                text="Tweet Activity",
                font=dict(
                    size=24
                )
            ),
            legend = dict(font = dict(size=plot_font_size))
            )
        st.plotly_chart(fig,use_container_width=True, height=1200)

    with radar_plot:
        try:
            fig = get_sentiment_plot(searched_item)
            fig.update_layout(
            polar=dict(
            radialaxis=dict(
                visible=False,
            ),
            angularaxis=dict(
                tickfont=dict(size=plot_font_size))),
            showlegend=False,
            title = dict(
                text="Tweet Sentiment",
                font=dict(
                    size=24
                )
            )
            )
            st.plotly_chart(fig, use_container_width=True)
        except ZeroDivisionError:
            sorry = zero_query.beta_container()
            sorry.error("Sorry your search returned 0 results. Please try a different query.")
            st.stop()

    ##########################################
    # Suggested articles
    ##########################################
    with suggested_articles_slot_title.beta_container():
        st.markdown("## Suggested Articles")
    suggested_news_col1, _, suggested_news_col2, _, suggested_news_col3 = suggested_articles_slot.beta_columns((8,1,8,1,8))
    suggested_articles = [articles_list for articles_list in searched_item["suggested_articles"].values()]
    suggested_articles = [item for mini in suggested_articles for item in mini]

    if len(suggested_articles)>=3:
        with st.spinner("Loading Suggested Articles"):
            samples = random.sample(suggested_articles,3)
            cols = [suggested_news_col1,suggested_news_col2,suggested_news_col3]
            for col, link in zip(cols, samples):
                try:
                    prev = get_link_preview(link)
                    col.image(prev["image"], width=300)
                    col.markdown("""
                    ```
                    {}
                    ```
                    """.format(prev["title"]))
                    desc = prev["description"].split()[:21]
                    desc = " ".join(desc)+"..."
                    col.markdown("""{}  [link]({})""".format(desc,prev["link"]))
                    col.write("")
                    col.write("")
                except:
                    pass
    else:
        suggested_news_col1.write("No Suggested News")
        suggested_news_col2.write("No Suggested News")
        suggested_news_col3.write("No Suggested News")


    ##########################################
    # Suggested articles - end
    ##########################################

###########################################
# Experimental Visualizations - end
###########################################





###########################################
# Top articles
###########################################
news_col1, _, news_col2, _, news_col3 = st.beta_columns((8,1,8,1,8))
news_col1.markdown("## General News")
news_col2.markdown("## Fact Checks")
news_col3.markdown("## User Specified")
news_col1.write("")
news_col2.write("")
news_col3.write("")

if not user_specified_domain:
    news_col3.markdown("""
        Enter a preferred news domain in the sidebar and we'll check whether its compatible with our system's RSS Parser.

        Examples include:
        
            babylonbee.com
            
    """)
    news_col3.markdown("""
    ```
    factcheck.org/fake-news
    ```
    """)
    news_col3.markdown("""
    ```
    redstate.com
    ```
    """)


    
with st.spinner("Loading News..."):
    # General
    news_general = get_feedparser_data("http://feeds.bbci.co.uk/news/uk/rss.xml#")
    # False claim fact checks
    try:
        if feedly_keys:
            news_fact_check = get_feedly_data(15, feedly_keys)
            news_fact_check = [item for item in news_fact_check if len(item["link"]) != 32]
        else:
            news_fact_check = get_feedparser_data("https://www.snopes.com/fact-check/rating/false/feed/")
    # If feedly API calls have been maxed out for 6+hour period.
    except:
        news_fact_check = get_feedparser_data("https://www.snopes.com/fact-check/rating/false/feed/")
    # User specified
    try:
        news_user_specified = get_feedparser_data("https://{}/feed/".format(user_specified_domain))
    except:
        news_user_specified = "factcheck.org"
    
    num_items = 5
    for item in news_general[:num_items]:
        prev = get_link_preview(item["link"])
        news_col1.image(prev["image"], width=300)
        news_col1.markdown("""
        ```
        {}
        ```
        """.format(prev["title"]))
        news_col1.markdown("""{}  [link]({})""".format(prev["description"],prev["link"]))
        # news_col1.write(prev["description"])
        # news_col1.write(prev["link"])
        news_col1.write("")
        news_col1.write("")


    for item in news_fact_check[:num_items]:
        prev = get_link_preview(item["link"])
        news_col2.image(prev["image"], width=300)
        news_col2.markdown("""
        ```
        {}
        ```
        """.format(prev["title"]))
        news_col2.markdown("""{}  [link]({})""".format(prev["description"],prev["link"]))
        # news_col2.write(prev["description"])
        # news_col2.write(prev["link"])
        news_col2.write("")
        news_col2.write("")

    if not news_user_specified:
        news_user_specified = "factcheck.org"

    for item in news_user_specified[:num_items]:
        try:
            prev = get_link_preview(item["link"])
            news_col3.image(prev["image"], width=300)
            news_col3.markdown("""
            ```
            {}
            ```
            """.format(prev["title"]))
            desc = prev["description"].split()[:21]
            desc = " ".join(desc)+"..."
            news_col3.markdown("""{}  [link]({})""".format(desc,prev["link"]))
            news_col3.write("")
            news_col3.write("")
        except:
            pass

###########################################
# Top articles - end
###########################################




# https://blog.streamlit.io/the-streamlit-agraph-component/
