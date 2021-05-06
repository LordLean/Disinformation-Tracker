import operator
import re
import string

class Rake:

  """
  The Rake object contains the logic to extract keywords from text using the RAKE algorithm.
  Implementation follows the steps laid out in the paper detailed below.
    
    Paper title : Automatic Keyword Extraction from Individual Documents (2010)
    DOI : 10.1002/9780470689646.ch1
    Paper authors : Rose, Stuart & Engel, Dave & Cramer, Nick & Cowley, Wendy.


  Parameters
  ----------
  None

  Attributes
  ----------
  text : str
      Stores the text from which keywords will be extracted.
  stopwords : list
      Stores the list of stopwords which should be omitted from keyword extraction. Acts as a delimiter for the RAKE algorithm.
  allwords : list
      Stores all unique candidate keywords.
  keywords : list
      Stores composite keywords. I.e. keyword phrases.
  cooccurences : dict
      Stores dictionary of unique words an nested dictionary of words and their cooccurences count. E.g. {word : {word:2, neighbouring_word:1}}
  word_scores : dict
      Stores dictionary of unique words and their frequency, degree and overall scores.
  keyword_scores : dict
      Stores dictionary of keyword phrases and their composite scores - the sum of their individual keyword scores.
  """

  def __init__(self):
    self.__init()


  def __init(self):
    """
    Re-initialize Rake object.
    """
    self.text = None
    self.stopwords = None
    self.allwords = []
    self.keywords = []
    self.word_scores = {}
    self.keyword_scores = {}


  def load(self, text, stopwords):
    """
    Load the text to extract keywords from and the stopwords to omit.

            Parameters:
                    text (str): The text to extract keywords from.
                    stopwords (list): List of stopwords to omit.
    """
    self.__init()
    self.text = text
    self.stopwords = stopwords
    self.__run()


  def __run(self):
    """
    Run all private methods to calculate keywords scores.  
    """
    self.__get_candidate_keywords()
    self.__get_cooccurences()
    self.__get_word_scores()
    self.__get_keyword_scores()


  def __get_candidate_keywords(self):
    """
    Save unique words in all words and keywords (individual words and phrases) in keywords attribute.
    """
    # Separate text by newlines, whitespace, punctuation and some regex delimiters.
    wk_text = ". ".join(self.text.split("\n"))
    r = re.compile("\n|\s|[,;.-?!‘’']|^a-zA-Z]+".format(re.escape(string.punctuation+"‘’'")))
    wk_text = r.split(wk_text)
    wk_text = [word.lower() for word in wk_text]
    curr = []
    for i, word in enumerate(wk_text):
      if word not in self.stopwords and word not in string.punctuation:
        curr.append(word)
        self.allwords.append(word)
        if i != len(wk_text) - 1:
          curr = " ".join(curr)
          self.keywords.append(curr)
      else:
        if len(curr):
          curr = " ".join(curr)
          self.keywords.append(curr)
        curr = []


  def __get_cooccurences(self):
    """
    Get count of coocurrences of all words in text.
    """
    # Generate unique word list.
    unique = sorted(list(set(self.allwords)))
    # Create cooccurences dictionary.
    self.cooccurences = {word:{} for word in unique}
    for candidate in self.keywords:
      candidate_list = candidate.split()
      if len(candidate_list) == 1:
        if candidate not in self.cooccurences[candidate]:
          self.cooccurences[candidate][candidate] = 1
        else:
          self.cooccurences[candidate][candidate] += 1
      else:
        for item_i in candidate_list:
          for item_j in candidate_list:
            if item_j not in self.cooccurences[item_i]:
              self.cooccurences[item_i][item_j] = 1
            else:
              self.cooccurences[item_i][item_j] +=1


  def __get_word_scores(self):
    """
    Calculate frequency, degree, word scores for each keyword.
    """
    for key, inner_dict in self.cooccurences.items():
      # Word frequency.
      freq = inner_dict[key]
      # Word degree - sum of a word's coocurrences (including itself).
      deg = sum(inner_dict.values())
      # Word score - word degree divided by word frequency.
      score = deg / freq
      # Write to dict.
      self.word_scores[key] = {"frequency" : freq, "degree" : deg, "score" : score}


  def __get_keyword_scores(self):
    """
    Calculate composite scores for each keyword phrase, a sum of all individual keyword's scores.
    """
    for candidate in self.keywords:
      candidate_list = candidate.split()
      if len(candidate_list) == 1:
        self.keyword_scores[candidate] = round(self.word_scores[candidate]["score"],2)
      else:
        sum = 0
        # Split composite keyword string into individual keywords.
        for word in candidate.split():
          sum += self.word_scores[word]["score"]
        self.keyword_scores[candidate] = round(sum,2)


  def get_ranked_keywords(self, top_n=10):
    """
    Return sorted list of keywords phrases with highest scores. 
    Run after loading text and stopwords to return keyword phrases.

            Parameters:
                    top_n (int): Integer to specify number of desired items to return

            Returns:
                    sorted() (list): List of tuples with (keyword_phrase, composite_score).
    """
    return sorted(self.keyword_scores.items(), key=operator.itemgetter(1), reverse=True)[:top_n]
