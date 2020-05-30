#===========================================================================================================
# Dartmouth College, LING48: Computational Linguistics, Spring 2020
# Julian Grunauer (Julian.A.Grunauer.21@Dartmouth.edu) & Faustino Cortina (Faustino.Cortina.21@Dartmouth.edu)
# Culminating Project: Unbiased Word Similarity
#
# Methods:
# 
# Sources:
# https://hackersandslackers.com/scraping-urls-with-beautifulsoup/
#
#===========================================================================================================
from bs4 import BeautifulSoup
import requests
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Spoof headers in case site doesnt like web crawlers
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
q2e_url = "https://glosbe.com/qu/en/"
e2q_url = "https://glosbe.com/en/qu/"

# Sets for entire collection of words
E_tokens_all = set()
Q_tokens_all = set()

# Array of dicts: [{level: 0, E_word: Q_word, ...}, {level: 1, E_word: Q_word, ...}]
big_dicto = []

# Get words from user
print("Enter 2 Quechua words to see their estimated similarity and synonyms: ")
input = input().split()

# Crawl dictionary
def soupify(url, word):
	new_url = url + word # TODO: Add 2nd word later in "main" 
	req = requests.get(new_url, headers)
	soup = BeautifulSoup(req.content, 'html.parser')
	return soup

# Tokenize/filter to nouns
def tokenize_nouns(text):
	nouns = []
	for meaning in text:
		tokenizer = nltk.RegexpTokenizer(r"\w+") # Removes punctuation
		tokens_list = tokenizer.tokenize(meaning.get_text().lower()) # Tokenizes words
		pos_tagged = nltk.pos_tag(tokens_list) # POS tagger
		nouns += [item[0] for item in pos_tagged if item[1][0] == 'N'] # Filters nouns
	return nouns

# Quechua to English - take Q word, returns set of English nouns from definition 
def Q2E(word, first=False):
	# Crawl q2e dict
	soup = soupify(q2e_url, word)

	# Tokenize definitions
	main_meanings = soup.find_all(class_="phr")
	meanings = soup.select(".meaningContainer.hide-3rd div")
	meanings.extend(main_meanings)

	# Set level 0 of dicto
	if first == True:
		first_E_noun = tokenize_nouns(main_meanings)[0] # Nounify main meaning of inital word
		# Adding first E:Q item to dictionary
		dicto_item = {"level": 0, first_E_noun: word} # TODO: Change level: 1 when time comes
		big_dicto.append(dicto_item)

	# Tokenize/filter to nouns and add each English meanings to a set
	E_tokens = set()
	nouns = tokenize_nouns(meanings)
	for noun in nouns:
		E_tokens.add(noun)
		E_tokens_all.add(noun)
	return E_tokens
	
# English to Quechua - takes English word, builds dicto ({level: _, E:Q, ...}), returns set of Quechua words from definition
def E2Q(word):
	# Crawl e2q dict
	soup = soupify(e2q_url, word)

	Q_set = set()
	# Tokenize defintions
	main_meanings = soup.find_all(class_="phr")
	for Q in main_meanings:
		Q_set.add(Q.get_text().lower())
		Q_tokens_all.add(Q.get_text().lower())

	# Adding E:Q item to dictionary
	dicto_item = {"level": 1, word: Q_set} # TODO: Change level: 1 when time comes
	big_dicto.append(dicto_item)
	return Q_set
		

# Web crawling & building data data structure
def build_data(): 

	E_tokens = Q2E(input[0], first=True)
	print("E tokens: ", E_tokens)
	print("Big dicto: ", big_dicto)

	next_level_Qs = set()
	for E_word in E_tokens:
		next_level_Qs.update(E2Q(E_word))
	print("Big dicto: ", big_dicto)
	print("next level: ", next_level_Qs)

build_data()


# TODO: Loop through all
# TODO: 2 Words
# TODO: Crawling errors






