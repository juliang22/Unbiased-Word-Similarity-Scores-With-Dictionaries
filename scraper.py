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

# Quechua words for each level {level: [Q words], ...}
big_dicto = {}

# Get two Quechua words from user
print("Enter 2 Quechua words to see their estimated similarity and synonyms: ")
input = input().split()
if len(input) != 2:
	print("Please type exactly two inputs.")
	exit()
if input[0].lower() == input[1].lower():
	print("Please type two different Quechua words.")
	exit()

# Crawl dictionary
def soupify(url, word):
	new_url = url + word 
	req = requests.get(new_url, headers)
	soup = BeautifulSoup(req.content, 'html.parser')

	# Website throws an error after too much use
	too_many_connections = soup.select(".g-recaptcha")
	if too_many_connections != []:
		print("Whoops the online dictionary thinks you're a robot. Please navigate to https://glosbe.com/qu/en/ and confirm that you are human to continue.")
		exit()
	return soup

# Check if input exists in Quechua dictionary
def input_exists(input):
	for word in input:
		soup = soupify(q2e_url, word)
		# If input word are not found in Quechua Dictionary
		does_exist = soup.select(".alert.alert-info")
		if does_exist != []:
			print(does_exist[0].get_text())
			exit()

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
def Q2E(word, curr_level):
	# Crawl q2e dict
	if curr_level == 1:
		soup = soupify(q2e_url, word)
	soup = soupify(q2e_url, word)

	# Tokenize definitions
	main_meanings = soup.find_all(class_="phr")
	meanings = soup.select(".meaningContainer.hide-3rd div")
	meanings.extend(main_meanings)

	# Tokenize/filter to nouns and add each English meanings to a set
	E_tokens = set()
	nouns = tokenize_nouns(meanings)
	for noun in nouns:
		if noun not in E_tokens_all:
			E_tokens.add(noun)	
		E_tokens_all.add(noun)
	return E_tokens
	
# English to Quechua - takes English word, builds dicto ({level: _, E:Q, ...}), returns set of Quechua words from definition
def E2Q(word, curr_level):
	# Crawl e2q dict
	soup = soupify(e2q_url, word)

	# Tokenize defintions
	Q_tokens = set()
	main_meanings = soup.find_all(class_="phr")
	for Q in main_meanings:
		Q = Q.get_text().lower()
		# If we havent seen this Q word before, add to next bigdicto and use in next layer to find more E words
		if Q not in Q_tokens_all:
			Q_tokens.add(Q)
			big_dicto[str(curr_level)].append(Q)  
		Q_tokens_all.add(Q)
	return Q_tokens
		
# Web crawling & building data data structure
def build_data(target, levels): 
	# Build dictionary {level: [Q words], ...}
	for i in range(levels):
		big_dicto[str(i)] = []

	# Add input word (if it exists) to level 0 
	Q_tokens_all.add(target)
	big_dicto["0"] = target	

	curr_level = 1 # Level 0 is hardcoded input Q
	curr_level_Qs = set()
	next_level_Qs = {target}
	while levels != curr_level:
		curr_level_Qs = next_level_Qs
		next_level_Qs = set()
		for Q_word in curr_level_Qs:
			E_tokens = Q2E(Q_word.lower(), curr_level)
			# print("E tokens: ", E_tokens)
			# print("Big dicto: ", big_dicto)

			for E_word in E_tokens:
				next_level_Qs.update(E2Q(E_word.lower(), curr_level))
				# print("next level: ", next_level_Qs)

		# Printing main structure	
		if curr_level == 1:
			print("0: ", big_dicto["0"])	
		print(str(curr_level) + ": ", sorted(big_dicto[str(curr_level)]))
		curr_level += 1

def main():
	input_exists(input)
	build_data(input[0], 3) #this is 2 levels deep, dont surpass it or else the dictionary will think we're a bot
	build_data(input[1], 3)

main()







