Welcome to the Disinformation Tracking Tool  

Thanks for choosing to use this application. This tool was designed as part of project for an undergraduate computer science degree from the University of Sussex. The goal was to create an application that would allow its users to jump straight into examining the diffusion of news through the Twitter platform.  

Specifically this project targets disinformation (deliberately deceptive false news) however the tool can be used to search for anything you please! The quering function that searches Twitter operates the same as it does within Twitter's applications - we just make it easier for you to specify what's relevant information to you!

Some information to get you started! The three columns below take you through the different parts of the application and provide helpful links to further documentation. 


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
Lastly a huge thanks to the Streamlit team. Not only are their applications incredibily aestheic and high performing but they also have one of the nicest online communities out there.
Strongly recommend anyone, especially those who wish to maximise the potential of their machine learning or data science workflows, to check out Streamlit and the technologies Streamlit has to offer.
