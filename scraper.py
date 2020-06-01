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
import fasttext
from numpy import dot
from numpy.linalg import norm

nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Spoof headers in case site doesnt like web crawlers
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
q2e_url = "https://glosbe.com/qu/en/"
e2q_url = "https://glosbe.com/en/qu/"
webster_url = "https://www.merriam-webster.com/dictionary/"

# Sets for entire collection of words
E_tokens_all = set()
Q_tokens_all = set()

# Quechua words for each level {level: [Q words], ...}
big_dicto = {}

# Weird phrases or common insignificant words (Ex: 'not', 'be', 'then')
stop_words = ['-y','ama','ari','a','kay']

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
def input_exists():
	# Get two Quechua words from user
	print("Enter 3 Quechua words to see how the first word compares with the other two: ")
	user_input = input().split()
	if len(user_input) != 3:
		print("Please type exactly three inputs.")
		exit()
	if len(user_input) != len(set(user_input)):
		print("Please type 3 different Quechua words.")
		exit()
	for word in user_input:
		soup = soupify(q2e_url, word)
		# If input word are not found in Quechua Dictionary
		does_exist = soup.select(".alert.alert-info")
		if does_exist != []:
			print(does_exist[0].get_text())
			exit()
	return user_input

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
	# if curr_level == 1:
	# 	soup = soupify(q2e_url, word)
	soup = soupify(q2e_url, word)
	# Tokenize definitions
	main_meanings = soup.find_all(class_="phr")
	meanings = soup.select(".meaningContainer.hide-3rd div")
	meanings.extend(main_meanings)

	# Tokenize/filter to nouns and add each English meanings to a set
	E_tokens = set()
	nouns = tokenize_nouns(meanings)
	for noun in nouns:
		E_tokens.add(noun)
	return E_tokens
	
# English to Quechua - takes English word, builds dicto ({level: _, E:Q, ...}), returns set of Quechua words from definition
def E2Q(word, curr_level, word_prefix):
	# Crawl e2q dict
	soup = soupify(e2q_url, word)

	# Tokenize defintions
	Q_tokens = set()
	main_meanings = soup.find_all(class_="phr")
	for Q in main_meanings:
		Q = Q.get_text().lower()
		# If we havent seen this Q word before, add to next bigdicto and use in next layer to find more E words
		if Q not in stop_words:
			Q_tokens.add(Q)
			big_dicto[word_prefix + str(curr_level)].add(Q)
	return Q_tokens
		
# Web crawling & building data data structure
def build_data(target, levels, word_prefix):
	# Build dictionary {level: [Q words], ...}
	for i in range(levels):
		big_dicto[word_prefix + str(i)] = set()

	# Add input word (if it exists) to level 0 
	big_dicto[word_prefix + "0"] = {target}

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
				next_level_Qs.update(E2Q(E_word.lower(), curr_level, word_prefix))
				# print("next level: ", next_level_Qs)
		# Printing main structure
		if curr_level == 1:
			print("0: ", big_dicto[word_prefix + "0"])
		print(str(curr_level) + ": ", sorted(big_dicto[word_prefix + str(curr_level)]))
		curr_level += 1

def check_dict_similarities(list1, list2):
	minLen = min(len(list1), len(list2))
	matches = 0
	for word1 in list1:
		for word2 in list2:
			# if word1 == 'qhari' or word2 == 'qhari':
			# 	print(word1,word2,list1,list2)
			if word1 == word2:
				matches += 1
	return matches/minLen

def check_word2vec_similarities(word1, word2):
	ft = fasttext.load_model('cc.qu.100.bin')
	a = ft.get_word_vector(word1)
	b = ft.get_word_vector(word2)
	return dot(a, b) / (norm(a) * norm(b))

def get_score(secondWordPrefix):
	num_layers = len(big_dicto) // 3
	totalScore = 0
	for layer in range(1,num_layers):
		weight = 1/(2**layer)
		word1List = big_dicto['a' + str(layer)]
		word2List = big_dicto[secondWordPrefix + str(layer)]
		unWeightedScore = 0
		unWeightedScore += check_dict_similarities(word1List, word2List)
		for compLayer in range(layer):
			if layer != compLayer:
				word1CompList = big_dicto['a' + str(compLayer)]
				word2CompList = big_dicto[secondWordPrefix + str(compLayer)]
				unWeightedScore += 0.5 * check_dict_similarities(word1List, word2CompList)
				unWeightedScore += 0.5 * check_dict_similarities(word2List, word1CompList)
		totalScore += weight * unWeightedScore
		# print(unWeightedScore, totalScore)
	return totalScore

def get_pch(score1,score2):
	if score1 == 0:
		return 'infinity'
	return str((score2-score1) / score1 * 100) + '%'

def main():
	global big_dicto
	scores = {}

	'''Don't delete comments below, they are saved dictionaries for some word pairs that take a while to compute'''
	# house-woman vs house-man
	# input = ['wasi', 'warmi','qhari']
	# big_dicto = {'a0': {'wasi'}, 'a1': {"ch'usaq pacha", 'uchuy llaqta', 'sumaq wasichay kamay', "t'anta", 'pruphisyun', 'kawsaq', 'puririy', 'wasichay', 'kulunya', 'llaqta', "ch'amanaku", "llamk'ay", 'kunan pacha', 'saqru', "khipu q'aytu", 'runa llaqta', "p'acha", 'huasi', 'pacha', 'wasi', 'yaku qullqi', 'kawsay', 'ruray', 'wasi qata', 'casa', 'karka', 'kawsachikuy', 'kawsaykuq tantalli', 'tantanakuy', 'pampa suyu', 'wasi ukhu', 'wasikuna', 'uywa', 'p’unchay', 'pampa', 'hatun kamachi', 'qurpa', 'hatun llaqta'}, 'a2': {'rimay', "ich'ikapuru", 'atipakuy', "llamk'ana", "p'achallina", 'wayu', "q'isa", 'raqta', "q'imi", 'laqa', 'iskay chunka', 'yuyupa', 'simiki', 'linti', 'ankichiy', 'g', 'machu', 'wisina', 'waki', 'musyay', "rak'i", 'chaka', 'pachamama', 'tiqsimuyu', 'tanta', 'yachay wayllukuy', 'wallata', "wat'a", 'chunka iskayniyuq', 'qhari', 'uchuy llaqta', 'mikhuna', 'kurkumanta yachay', 'pachak', 'puririy', 'mapa mama', "k'uskiykuy", 'kinsa', 'sawnakuq', 'kunan pacha', 'simsiker', 'qurpachana wasi', 'chupa', "hamut'ay", 'abya-yala', 'illanchay', 'iñuwa', 'tullpuna', 'rakha', 'virreinato', 'kunka', 'machapu', 'de', 'hamlet', "sut'ichay", 'kurku kallpanchay', "lirq'u", 'achkha yupa', 'silulusa', 'ayllu', "t'ipana", 'allpa', 'wasi ukhu', 'hanchi', 'yupay yachay', 'hallpa', 'urin', 'chhulli', 'impuwistu', 'qhepajj raymi killa', 'suqta', 'saynata', 'shimi', 'qaraywa', 'karu kay', 'chaski', 'tara', "ch'askancha", 'raphi', 'maqanakuy', 'millma', "siq'iy", 'unquy', 'phawrika', 'wasa ruru', 'quri', 'casa', 'kuru qulluna', 'muru', 'rakiy', 'pawqar waray killa', 'kañina', 'irraminta', 'sallqa pacha', 'qatuylla', 'miraykuy', 'churana', 'ruray', 'juk', 'awqaq suyu', 'pachapanta', 'kawpay', 'pinchikilla pila', 'qam', 'kamachiy', 'alliyachachiy', 'asina', 'sunqu', "llamk'aykuna llika", 'apay', 'kawsaykuq', 'wiksayay', 'awki', 'kathidral', 'isanka', 'pirqaq', 'alli', 'ruway', 'partidu', 'willachikuy', 'kuska', 'llanthu', 'chaqallu', 'hayratachiy', 'chullusqa', 'pruphisyun', 'kusa', 'yachachiy', 'yuraj', 'jaqaypi', 'iskay', 'sindikatu', 'wallqanqa sanancha', 'asinda', 'sachakuna', 'sami', 'hunag', 'baryu', 'kancha', 'samay', "hillp'uchi", 'paray', 'kawsay', 'kaphiy', 'qhatuq', 'aysana', 'quyllurchaw', 'chiqaluwa', 'kawsaykuq tantalli', "llipt'a", 'achikay', 'kartulsuyu', "rimay t'ikray", "wirp'a", 'kamachina', 'wiñay kawsay', 'wañu', 'hatun kamachi', 'tisqu', 'kayma', 'yawri', "hunt'a rimay", "t'anta", 'pukyumanta willay', 'pacha mitʼa', 'kulunya', "k'aschina", 'khuchi runtuchi', "mit'a", 'sinca', 'kapchiy', 'tampu wasi', 'kutipakuy', 'shuc', 'sawna', 'sikundu', 'utqa kay', 'iniru', 'köln', 'puytu', "p'ulin", 'achala', 'punlla', 'ñaso', 'awaq', 'waricha', "siwk siq'i", 'sapaq yupa', 'ñuqa', 'ruraq atiy', 'micha', 'watʼa', 'miqu', 'suyu', 'uma', 'akllaspa mirachiy', "llank'ay", 'unancha', "mach'ay", 'maki', 'pʼunchay', 'mánan', 'phransya mama llaqtapi dipartamintukuna', 'kawsay saphi', "k'allampa", 'paca', 'mama llaqta', 'chakra runa', 'kajwi', "ch'usaq p'ulin", 'yachaqay', 'waylluy', 'ppacha', "rikch'a kapchiy", 'allana', 'qincha', 'tinti kaballu', "rikch'ana", 'qhatuna', 'intichaw', 'qalla iruru', 'qullqi wasi', 'yachay wasi', 'marucha', 'ruray rimanachay', 'paqarin', 'paqariy', 'wakcha', "rikch'aqyay", 'hatun qucha', 'hatun llaqta', 'akawara', "k'allma", "wichaykuna k'aspi", 'kawsaq', 'llasaq kay', 'panti', 'evitar', 'allwiya kamay', 'yupa huqariy', 'willa', 'saqru', 'chaki', 'mikhuchiy', 'hampi yachay', 'muna-', 'yuri', 'sacha', "sut'i", 'minutu', 'tullu', 'khipu', 'puncau', 'chaski qillqa', 'utku', 'sallqa', 'wisnu', 'uywariy', 'wata', 'wasichay', 'kiru', 'tiyana', 'kurku', "rikch'aq ayllu", 'willay kamayuq', 'kuyuchina', 'simi kapchiy', 'yaku qullqi', 'qhuya', 'macka', 'siwk patma', 'republika', 'quy', "ullu k'aspiyay", 'waqachina', "t'oqo", 'llimphiy', 'tantachisqa', "mit'apu", 'takiy', 'markedos', 'imayay', 'saqmanakuy', 'pachakwata', "samk'ay wasi", 'sonqo', "sach'a", 'yachay munaq', 'jugar', 'tapuy', 'nanay', 'hurkay', 'witi', 'awqaq', 'nuna', 'takarpucha', "ch'in pacha", 'rikchʼaq putu', 'paya', 'ruqyay', "p'unchaw", 'wiñay', 'atiyniyuq kay', 'arkhitiktura', 'uya', 'thak', 'ñasa', "k'ukti", 'upyana', 'phutuy', "yaqa wat'a", 'yura', 'simi', 'tantanakuy', 'china uywa', 'kuyuy', 'pampa suyu', "p'allta muyu", 'alimaniya', 'yupay saphi', "p'allta", "llut'ana", 'igu', "samana p'urucha", 'chakra yura', 'iñuku', "mit'awi", 'wanachay', 'arpay', 'pay', 'iruru muyu', "khipu q'aytu", 'ruru', 'runa llaqta', 'achulla', "p'acha", 'huasi', "llut'ariy", 'riy', 'llika', "t'aqa", 'awina', 'mikunamanta', "ch'usaq", 'waranqa', 'chukcha kʼutu', 'yugur', 'ura', 'kawsachikuy', 'tiksi muyu', 'chunka iskayniyuj', "p'aqchi", 'uywa', "p'uku", 'janajjpacha', 'órgano', 'kinraysuyu', "ch'usaq pacha", 'allin', 'waka', 'kamachi', 'sumaq wasichay kamay', 'ruraychaqa', 'kawallu', 'yapuy', "q'aytucha", 'qichuy', 'tunki', 'gata', "hap'iqay", 'mallés', 'uña', "allpa llamk'ay", 'qallawa', 'wasi qata', 'phapa', 'unquchiq', 'rikch’aq putu', 'llimphi', 'katiguriya', 'wasikuna', 'miray', 'qurpa', 'nina', 'yupay', "rikch'aq t'aqa", 'chawpi', 'parte', 'chhuka', 'iskaychunka', "rikch'aq suyu", 'diyosuun', 'wañuy', 'puywanku', 'tiksimuyu', 'kamay', "llamk'ay", 'makipura', 'chincha', 'pacha', 'phuru', 'chhukruna', 'p’unchaw', 'alimanya', 'mayllay', 'hanaq pacha', 'ñawi', 'qhaqya unquy', 'chikchi', 'illanchaykuy', 'pachanka', 'qhichwa', 'kay pacha', 'sinchiyasqa', 'aya', "rikch'aq", 'ñawiriy', 'qullqa', 'chakra', 'hatun', 'machuruku', 'sankhu', 'papil', "hallka k'iti k'anchar", 'musiku', 'añaki', 'chiqan chhuka', 'arininakuy', 'allin simi', 'tinda', 'apaykachay', 'tupu', 'pacha kawsay', 'wien', 'rima', 'pʼunchaw', 'munay', 'chimpa', 'toes', 'sullu', "mat'i", 'riwi', 'waqra', "rikch'aq sinri", 'qhulla puquy killa', 'chakakuq', 'pichana', 'yapay', "lunq'u", 'chiqa', 'kunan', 'chuki', 'kuskanachina tupu', 'ima', 'arí', 'ruruchina', 'wasi', 'paza', "pirqa llut'ana", 'allpa kawsay', 'yachay', 'sinqa', 'kurku yawri', 'tawa', "liwru ch'ipachina", 'qhapaq', 'ñan', 'ninri', 'yuyaychakuy', 'triyu', 'kuyu walltay', 'pampa', 'lima', 'huk', 'churay', 'wallpama', 'producir', "q'imiy", 'api', "rikch'aq ñiqi", 'waylla', 'llaqta', "ñaqch'a", "ch'amanaku", 'humu', "rikch'aq putu", "llamk'aq", 'wayusa', 'micuna', 'sasachakuy', 'tarpuy', 'rurana wakichi', 'collasuyu', 'pacha tupuq', 'yuraq', 'runa', 'hayñiq kay', 'tusuy', 'qurwara', 'kunkalla', 'mitma', "silq'uy", 'saywa', 'sinchi', 'illwa', 'karka', 'qhatu', 'ruray rimana', 'aminakoyim', 'atiy', "t'ipi", 'pukllay', 'ruruchiq', 'aqu', 'p’unchay', 'punku', 'kallpa'}, 'b0': {'warmi'}, 'b1': {'runa', 'sayaq runa', 'achkha yupa', 'warmi'}, 'b2': {'gari', 'runa', 'yuraq', 'qhusi', 'sutiy', 'taruka', 'sutiyki, sutiyqa', 'shimi', 'qhari', 'sayaq runa', 'achkha yupa', 'suti', 'taruca', "rikch'ana", 'warmi', 'yuraj', 'qharinchu', 'chinaku', 'yupay', 'killachaw', 'huti', 'runa llaqta', 'kawsaq', "rikch'aq", 'qari'},  'c0': {'qhari'}, 'c1': {'hatun', 'qari', 'runa', 'kawitu', 'ñuñu', 'suqta', 'khuyay', 'pacha', 'llanqha', 'rawray kuyuchina', 'qhari', "mit'awi", 'urin', 'warmi', 'alli', 'sinchiyasqa', "rikch'aq", 'awqaq', "q'uruta", 'laya', 'sinchi', "rikch'aq sinri", 'sojjta', 'sutirimana', 'sayaq runa', 'gari', 'urqu', 'yuquy', 'suti', 'arsiniku', 'munay', 'wayna', "rikch'ana", 'puka llanqa', 'sami', "hatun p'unchaw", 'pachanka', 'hatun qucha', "rikch'aq suyu", 'lichi', 'walla', 'mánan', 'awqaylli', 'wiraqocha', 'sallqa pacha', 'ullu', 'kusa'}, 'c2': {'mana', 'ulay', 'alkho', 'niy', 'kusikuy', 'simi kamachiy', 'yachachiq', 'atiyniyuq kay', 'shimi', 'dyus', 'orgo', 'rumi kaq', 'churay', 'chiqa', 'yaku', 'raphi', 'runa suti', "ch'usaq pacha", 'tapuy', 'chinaku', 'achachilla', "llut'ariy", 'llimphi', 'malta', "k'allma", 'rimana huñunakuy', 'miqu', "llamk'ay", 'maki', 'kawitu', 'khuyay', 'wayaw', 'chiqap', 'kuyuy', "rikch'aq", 'munai', 'killachaw', 'waricha', 'ananinami', 'gari', 'qatar', 'chaki', 'yuraj', 'wachuchasqa', "mach'ay", 'kawsaq', 'qhapaq', 'qaqa', "rikch'aqyay", 'wallpama', 'sinca', 'ñan', 'phuru', 'wanachay', "misk'i", 'dundee', 'pacha kawsay', 'montana suyu', 'yuyaychakuy', 'irpay', 'runa yupay', 'paca', 'qam', 'waillui', 'riqsisqa', 'onqoy', 'paray', 'pachamama', 'puma', 'agradiseyki', 'asina', 'chillki', 'pachak', 'uya', 'chango', 'ñañu', 'puka', 'rasa', 'arininakuy', 'chakra yura', 'tayta', "qullqi q'illay", 'wasa ruru', 'wanqara', 'qharinchu', 'pachanka', 'qulqi', 'hamchi', 'illwa', 'qanta munani', 'pichunku', 'musyay', 'uwiha', "qillqana p'anqa", "wach'i", 'kamachi quq atiy', 'ullu', 'quyllur', "yaqa wat'a", 'chakra', "k'anka", 'lani', 'allqu', 'chiqan chhuka', "samana p'urucha", 'micha', 'ayllu', 'wankar', "sut'i", 'yachachiy', 'kanada', "ch'iqtaku", 'hallpa', 'wayra', 'qusa', 'simi', 'puywanku', 'sawsi', 'kinraysuyu', 'lichi', 'sutiyki, sutiyqa', "wichaykuna k'aspi", "rikch'ayrimana", "p'ulin", "lunq'u", "k'aschina", 'kuskanachina tupu', 'mali', 'hatun', 'saywa', 'hucha', 'tullpuna', 'llanqha', 'simsiker', 'rawray', 'sañi', 'antakuru', 'intichaw', 'pharu', 'qillqay', 'qallu', 'wisina', 'yura qara', 'chaqrusqa', 'alli', 'hayñiq kay', 'aymuray', 'yuri', 'turri', 'sojjta', 'unu', 'siqana pata-pata', 'raqta', 'waska', 'walla', 'diyosuun', 'rumi', 'sutip rampaqnin', 'rima', 'waylluy', 'intillama', 'sumaq', 'wisnu', 'kañina', 'huti', 'rimaq pampa', 'rimay', 'jampiri', "wank'a", 'yayawky', "rikch'aq t'aqa", 'yunta', 'sinchiyasqa', 'aypay', "mit'apu", 'káho', 'karu kay', 'makiyuq', "ch'iqan", 'wasikuna', 'laya', 'rikch’aq putu', 'k’uychichaw', 'sallqa akllay', 'uma llaqta', 'sutiy', 'erqe', 'llika', 'aranwa', 'qurpa', 'qillqara', "sut'i musyay", "rikch'ana", 'puka llanqa', 'rikuchina', 'miraykuy', 'paza', 'canda munani', 'wawa', 'mánan', 'pacha mitʼa', 'suyu', 'rikra', 'chawpi', 'qhasqu', 'llakikuy', 'wakcha', 'puririy', 'atiy', "llamk'ana", 'parte', 'humu', 'mintasqa', 'masi', 'hañas', 'pikchu', 'pisqu', 'chapay', 'awqaq', 'tarpuy killa', 'kawsaykuq', "rikch'a kapchiy", 'sacha', 'yuquy', 'ñasa', 'yuyay', "p'allta muyu", "hap'iqay", 'kuska', 'punku', 'pampa suyu', 'hatun qucha', 'qhusi', 'muna-', 'wayaqa', "q'uchukuy", 'sanampa', 'kay pacha', 'maymanta', "ch'amanaku", 'raray', 'suqta', 'pillpintu', 'michiy', 'ñawi', 'paqariy', 'yawri', "marq'a", 'qurwara', "llinp'i", 'yanasu', 'mama llaqta', 'yupa huqariy', 'sikundu', 'ñutqu', 'sallqa', 'añaychay', 'phiñakuy', 'panti', "ch'añan", 'rakiy', 'awqaq suyu', "rikch'aq suyu", 'shuc', 'yuraq', 'cari huallpa', 'katiguriya', 'nuna', 'allpa kawsay', 'sanancha', 'arpay', 'ayñi', 'ruray', 'achkha yupa', 'salina', 'phuyu', 'yura pacha', 'sinchi', 'phawrika', 'jaqaypi', 'agra', 'witi', 'tullu', 'allpa', 'makipura', 'qachu-qachu', 'phaqsa', 'kurku yawri', 'unancha', 'ruray rimana', 'llawchʼinchu', 'wisu', 'qari', 'yachay', "ch'upu", 'kamachina', "p'inqa", 'qhari', "mit'awi", 'puñuy', 'rapa', 'bajo', 'pachamuyu', 'huahua', 'arí', 'pachakwata', 'taripay suntur', 'qhatu', 'daya', 'rantina qullqi', "k'isura", 'chita', 'mitru', "siwk siq'i", 'collasuyu', 'toes', 'arsiniku', 'tawa', 'kusi', 'qosa', 'ima', "hatun p'unchaw", 'pay', 'sullu', 'upyana', 'pampa', 'muyuriq pacha', 'huk', 'rikchʼaq putu', "t'aqanakuy", 'qhipa pacha', 'wata', 'turi', 'órgano', 'pukllay', 'wallata', 'kutipakuy', 'imakay', "rak'i", 'añaka', 'yura', "q'uruta", 'tupu', 'rawrana', 'muru', 'yapay', 'llawi', 'suti', 'ñawpa pacha', 'tiqsimuyu', 'paña', 'ruru', 'qhatuna', 'churi', 'yaku qullqi', 'asinda', 'kirusapa kuchuna', "q'umpuyasqa", 'kulli', 'iran', "sut'ichay", 'wiñay kawsay', "llut'ana", 'kurku kuyuchiq', "silq'uy", 'liyun', 'urin', 'wasi ukhu', 'warmi', 'qillqa', 'llasaq kay', "ch'away", 'kawllay', 'qhula', 'kawsay', 'tawantin iñu', 'sayaq runa', 'qhaway', 'tunu', 'kamachi', 'anqara', 'ruqyay', 'kuyuylla', 'warmo', 'wasi', 'hanchi', 'qachu', 'willachikuy', 'pinu', "p'aqchi", 'liwru', 'wiraqocha', 'killapura', "p'uku", "hunt'a rimay", 'runa', 'ñuñu', 'unquy', 'wallqanqa sanancha', 'kuru qulluna', 'ulatraw', 'iruru muyu', 'malliy', 'yupay', 'chupa', 'aminakoyim', 'chhukruna', 'sinqa', "challwa hap'iy", 'linsi', 'sutirimana', 'huasi', "rikch'aq ñiqi", 'misi', 'kʼuychichaw', 'kisma', 'riy', 'kinsa', "p'achallina", 'sami', 'kallpa', 'iskaychunka', 'sunqu', "hallka k'iti k'anchar", 'ispay', 'urapi', 'llimphiy', 'wayu', 'urquchillay', 'irraminta', "ch'iqta", 'sallqa pacha', 'machi', 'simana', 'klawil', 'tantachisqa', 'rawray kuyuchina', 'sasachakuy', 'mallés', "ch'illa sirk'a", 'kayma', 'chunka iskayniyuq', "p'allta", "q'uncha", "rikch'aq sinri", "siq'iy", 'apaykachay', 'siwk patma', 'sonqo', 'kawsaykuq tantalli', 'nina', 'wayna', u'ñuñuq', "jisq'un", 'khuya', "p'unchaw", 'ñuqa', 'qillakuq', 'qhali kay', 'awqaylli', 'kuyuchina', "rikch'aq putu", 'chaski qillqa', 'yachaq', 'pacha', 'ura', "p'uchqu", "k'aklla", 'wiñay', 'tiksi muyu', "yupa hap'ichiy", "mit'a", "ch'askancha", 'runa llaqta', 'iskay chunka', 'qhatuq', 'orqo', 'maqanakuy', 'ñaso', 'kathidral', 'imayay', 'qhaquy', 'yura kurku', 'munay', 'de', 'taruca', 'qalla iruru', 'tiksimuyu', 'qarati', 'reqsisqa', 'wiksa', 'juk', 'tullu muqu', 'kiru', 'rikui', 'ataw', "p'aki", 'tumpay', 'miray', 'rawta', 'qillqarajjpa', "k'uychichaw", 'rani', 'tullpu', 'hirka', 'aysana', 'kurku', 'puriqlla', 'urqu', 'mama', 'miyu', 'yana', 'samay', 'kuyu walltay', 'taruka', 'tantanakuy', 'michi', 'china uywa', 'urpu', 'palama', 'kaoko', 'rikai', 'waranqa', 'atiykuy', 'uma', 'kusa', 'chunka iskayniyuj', 'uywa'}}

	# cat-human vs cat-lion
	# input = ['michi', 'runa', 'liyun']
	# big_dicto = {'a0': {'michi'}, 'a1': {'misi', 'michi', "rikch'aq", 'mişi', 'misti hawar'}, 'a2': {'michi', "rikch'aq t'aqa", "rikch'ana", 'ñuñuq', "siwk siq'i", "rikch'aq ñiqi", 'awqaq suyu', 'mama llaqta', 'chupa', 'humu', 'turri', 'tupu', 'misti hawar', "rikch'aq sinri", 'iskaychunka', 'rakiy', 'waranqa', 'rikchʼaq putu', 'raqta', 'sallqa akllay', 'suyu', "rikch'aq putu", 'maki', 'rikch’aq putu', 'chunka iskayniyuj', 'mişi', 'iskay chunka', 'siqana pata-pata', "p'allta", 'punku', 'chunka iskayniyuq', 'misi', 'qillqarajjpa', 'sami', 'suqta', "rikch'aq", 'pampa', 'tunu', 'suti'}, 'b0': {'runa'}, 'b1': {'qhari', 'runa llaqta', 'yuraj', 'chinaku', 'suti', 'taruca', 'huti', 'sutiy', 'sutiyki, sutiyqa', "rikch'aq", "rikch'ana", 'yuraq', 'gari', 'qharinchu', 'runa', 'qhusi', 'taruka', 'qari'}, 'b2': {'reqsisqa', 'khuyay', 'turi', 'llanqha', 'chinaku', 'sonqo', 'juk', 'arininakuy', 'waska', 'llasaturaku', 'ima', 'tullpu', "q'uruta", 'yanasu', "siwk siq'i", 'ñuñu', 'warmo', "mit'a", "mit'awi", 'uqi', "hatun p'unchaw", 'kawallu', 'kusa', 'upyana', "p'uruña", 'lichi', 'qharinchu', 'huahua', 'arpay', 'qari', 'iskaychunka', 'mánan', 'jampiri', 'sallqa pacha', 'raqta', 'masi', 'ullu', 'sankhu', 'qam', 'sayaq runa', 'yayawky', 'mintasqa', 'pinchikilla pila', 'maki', 'inlish simi', "rikch'aq ayllu", "llut'ariy", 'qosa', 'rimay', 'churay', "suyk'u", 'qhari', 'qillqarajjpa', 'qillqara', 'runa llaqta', 'añaychay', 'china uywa', 'pachamuyu', 'awqaq', 'sami', 'cari huallpa', 'pay', 'pacha', 'qhusi', 'simi yachaq', 'laya', 'warmi', 'riqsisqa', 'wasi', 'hanaq pacha', 'urqu', 'wallata', 'achkha yupa', 'runa', 'mayllay', 'rikui', 'wasa ruru', 'alli', "rikch'aq ñiqi", 'churi', 'awqaq suyu', 'allqu', 'sutiy', 'wawa', 'arsiniku', 'llimphi', 'allin', 'allpa', 'humu', 'turri', 'tullpuna', 'liwru', 'ñawi', 'taruka', 'simi yachay', 'rakiy', "hunt'a rimay", 'waranqa', 'alkho', "k'anka", "ch'iqta", "rikch'aq suyu", 'niy', 'sikundu', 'shuc', 'sallqa akllay', 'rikai', "p'achallina", 'tiksimuyu', 'pillpintu', 'punku', 'walla', 'misi', 'ñañu', "jisq'un", 'anqas umiña', 'kuska', 'ayllu', 'wallqanqa', 'paza', 'kanada', 'yuquy', 'gari', 'pachamama', 'kawsaq', 'suti', 'shimi', 'tantachisqa', 'qusa', "ch'askancha", 'urin', 'saywa', 'wiñay kawsay', 'huti', "sach'a", 'maymanta', "challwa hap'iy", 'chango', 'qillqay', 'puma', 'qurpa', 'tullu muqu', 'kaoko', 'tullu', 'irraminta', 'witi', 'runa suti', 'phawrika', 'tiqsimuyu', 'yuraj', "qillqana p'anqa", 'taruca', 'wayra', 'mama llaqta', 'chupa', 'tupu', 'ruray rimana', 'sutiyki, sutiyqa', 'qillqa', 'chiqa', 'janajjpacha', 'pharu', 'uma', 'sinchiyasqa', 'rikchʼaq putu', 'antakuru', 'yupay', 'achik', "p'aqchi", 'chaki', 'suyu', 'dundee', 'tayta', 'chunka iskayniyuj', 'ispana ukhu', 'sojjta', 'chapaq', 'chunka iskayniyuq', 'hatun', 'luwichu', 'suqta', 'liyun', 'sacha', 'tunu', 'rima', 'wayna', 'uywa', 'chikchi', 'sanampa', 'rawray kuyuchina', "ch'amanaku", 'michi', 'tawa', "p'uku", 'kawitu', 'sutirimana', "lunq'u", "rikch'aq t'aqa", 'pachanka', "rikch'ana", 'puka llanqa', 'daya', 'sunqu', 'imayay', 'sasachakuy', 'chita', 'yura', 'qallu', 'pinu', 'rapa', 'paca', 'munay', 'kay pacha', "rikch'aq sinri", 'sinchi', 'wiraqocha', 'imakay', 'erqe', 'kallpa', 'yana', "sut'ichay", 'ruray', 'rasa', "rikch'aq putu", 'yuraq', 'rikch’aq putu', 'iskay chunka', 'dyus', 'kurku kuyuchiq', 'malta', 'siqana pata-pata', "p'allta", 'simi', 'awqaylli', 'hatun qucha', 'yachaq', 'chiqap', "rikch'aq", 'pampa', "ch'aqu", 'anqas', 'wasikuna', 'wisnu', "sut'i musyay"}, 'c0': {'liyun'}, 'c1': {'misi', 'michi', "rikch'aq", 'liyun', 'puma', 'mişi'}, 'c2': {'michi', "rikch'aq t'aqa", 'urqu', "rikch'ana", 'puma', "siwk siq'i", 'hirka', "rikch'aq ñiqi", 'awqaq suyu', 'awya yala', 'mama llaqta', 'chupa', 'humu', 'turri', 'tupu', "rikch'aq sinri", 'misti hawar', 'iskaychunka', 'rakiy', 'waranqa', 'rikchʼaq putu', 'raqta', 'pikchu', 'sallqa akllay', 'suyu', "rikch'aq putu", 'maki', 'rikch’aq putu', "rikch'aq ayllu", 'mişi', 'chunka iskayniyuj', 'iskay chunka', 'orgo', 'siqana pata-pata', "p'allta", 'punku', 'chunka iskayniyuq', 'misi', 'qillqarajjpa', 'ayllu', 'sami', 'suqta', "rikch'aq", 'liyun', 'pampa', 'sacha', 'tunu', 'suti'}}

	# sacred-flower sacred-mountain
	# input = ['willka', 'tuktu', 'pikchu']
	# big_dicto = {'a0': {'willka'}, 'a1': {'parte', 'iñiy', 'iñuku', 'salina', 'runa', 'sikundu', 'uya', 'dyus kay', 'juk', 'k’uychichaw', 'dyus', 'tarpuy killa', 'urin', 'wamra', 'shuc', 'qhari', 'willka', 'de', 'wawa', 'kʼuychichaw', 'intichaw', 'uma', 'apu', "wak'a", 'nuna', 'inti', 'pay', 'wawayki', 'huk', "k'uychichaw"}, 'a2': {"suqtawask'a", 'sikundu', "rikch'aq ñiqi", 'qhelli', 'uya', 'hatun llaqta', 'yura kurku', 'imayay', "wat'a", 'qharinchu', 'tantachisqa', 'ch’aska', 'achkha yupa', 'challaku', 'urqu', 'hanchi', "t'anta", 'wayrukuna', 'irraminta', 'manila', 'rawray kuyuchina', 'laya', 'ruru', 'inti', 'tiqsimuyu', 'pacha', 'tullpu', 'wayna', "mit'awi", 'sinchi', 'tapuy', 'ñ', 'runa', 'dyus', 'yachay', 'suyu', 'urin', 'paza', 'kawitu', 'misi', 'de', "t'aklla", 'pacha kawsay', 'hayway', 'llakikuy', 'sitimri', "llump'ay kamay", 'saqru', 'antakuyu', 'alli', "jamp'ara", 'khipu', 'yachaq', 'puncau', 'punku kirma', 'ankucha', 'qam', 'unu', 'sinchiyasqa', 'sumaq wasichay kamay', 'qelqay', "hunt'a rimay", 'tawantin iñu', 'kunka', 'uma llaqta', "q'illay kañina", 'pachakwata', 'ñan', 'iyun', 'runa sipiy', "siq'iy", 'quya raymi killa', 'bueno', 'pachamama', 'apuspi yuyay', 'asina', 'sacha', "sut'i", 'khuyay', 'tantanakuy', 'tahua', 'arí', 'ruruchina', 'kallpa', 'salina', 'hatun', 'sullu', 'juk', 'tarpuy killa', 'shimi', 'tupu', 'qhiti', 'qillqara', 'chiqa', 'chʼuspi', 'rakiy', 'puka llanqa', 'pukyu', 'tata', 'huasi', 'sunqu', "k'ullu", 'manchakuy', 'anti', 'iñuku', "llamk'ana", 'riqsisqa', 'pampa suyu', 'walla', 'linti', 'chaqllisinchi', 'wiñay kawsay', "wach'i", "sut'u", 'wasi', 'qhari', 'kusituy', "rikch'aq t'aqa", 'ima', 'b', 'llasaq kay', 'tihiras', 'sutirimana', 'minutu', 'willachikuy', 'dumingu', 'pachak', 'suti', 'wayra', 'wasikuna', 'chapaq', 'arpay', 'yachay wasi', 'wasichay', 'tarpuy', 'ususi', 'kusa', 'jawillu', "q'isa", 'miray', 'mayu', 'sasachakuy', 'chaski qillqa', "t'ipi", 'yupay yachay', "liwru ch'ipachina", "hatun p'unchaw", 'niy', 'tuktu', 'miraykuy', "willay p'anqa", 'kawllay', 'qhusi', 'kurku yawri', 'makipura', 'hunag', "chirawmit'a", 'wakta', "p'uku", 'kawsaykuq tantalli', "ch'iqta", "rikch'aq", 'llimphi', 'willa', 'apuchaw', 'wiñay', 'qhuya', 'wañu', 'yapay', 'akawara', "q'uruta", "k'uskiykuy", 'nanay', 'taski', 'qhepajj raymi killa', 'phutikuy', "q'aqcha", 'allpa', 'llanthu', 'llimphiy', 'willka', 'p’unchaw', 'china uywa', 'kapchiy', 'kawsay', 'qullqa', 'santu', "rikch'aqyay", 'pay', 'sojjta', 'centre', 'wiraqocha', 'kuchillu', "p'unchaw", 'allpapi puquq', "p'acha", 'surgu', 'maywiy kutinchiq', 'khilla', 'rikch’aq putu', 'usa', 'sapa', 'pʼunchaw', 'qiru', 'yuri', 'wallata', 'kʼuychichaw', 'qhatuq', 'yaku', 'hatun qucha', "wichq'ana", 'sintu', 'sutiyki, sutiyqa', 'llujllu', 'runa llaqta', 'ruray', 'sallqa pacha', 'puririy', 'hatun kamachi', 'casa', 'awqaylli', 'simana', 'lampa', 'sami', 'sutiranti', 'yoga', "hutk'una", 'allpa pacha', 'wachuchasqa', 'k’uychichaw', 'pampa', 'wamra', "t'inkisqa", "wank'a", 'rumi', 'umalliq', 'pikchu', 'wawa', 'hilli', 'pedo', 'uma', 'yachachiq', 'uywa', 'p’unchay', 'chimpa', 'malta', 'kawsaq', 'chumpi', 'warmi', 'nuna', 'ridusiy', 'raphi', 'mama', 'chʼaska', 'achulla', 'quyllur', 'ullu', 'gari', 'órgano', 'paykuna', 'kusasqa tika', "wirp'a", 'llanqha', 'sonqo', 'ñasa', "mat'i", 'suqta', 'awqaq', 'nina', "ch'askancha", "llipt'a", "hunk'a", 'tiksimuyu', 'machuruku', 'chaqna', 'ñuqa', 'kancha', 'unancha', 'muru', 'wata', 'kawsaykuq', 'suwa', 'iñiy', 'karka', 'yupa huqariy', 'iñuwa', 'machina', "ch'iqtaku", 'wayru', 'chinaku', 'machu', 'chango', 'ichhuna', 'qillqarajjpa', 'chuki', "rak'i", 'chita', 'willakuy', 'ayllu', 'atiyniyuq kay', "sach'a", 'qachu', 'titi', "rikch'aq sinri", "rikch'ana", 'intichaw', 'pinchikilla pila', 'collasuyu', 'ura', 'khillay', 'pʼunchay', 'ruqyay', 'utqa kay', "k'aklla", 'kiru', 'wawayki', 'tiksi muyu', 'kukupin', "q'imina", 'yupay', 'phawrika', 'witi', 'tullpuna', 'tajáo', 'taytakura', 'taruka', 'yura', 'waki', 'yuraj', "wichaykuna k'aspi", 'yura pacha', "hamp'ara", 'arsiniku', "k'iri", 'wisnu', 'auquish', 'sutiy', 'saynata', 'yuyaychakuy', 'goillur', 'aycha kanka', 'jilli', 'sapaq yupa', 'yuraq', 'paqariy', 'qallawa', 'pallpa', 'sipas', 'sapra', 'taruca', "t'uqyay", 'michij runa', "ch'aska", "rikch'aq suyu", 'wasi qata', 'ñuñu', 'sankhu', "rikch'aq ayllu", 'rikchʼaq putu', 'rumi kaq', 'uquti', 'pachaykamay', 'yuquy', "p'ulin", 'mánan', 'humu', 'qaqa', 'kuyuy', "k'iraw", "rikch'aq putu", 'chaska', 'raymikis', 'parte', 'mana', 'yupay saphi', 'puywanku', 'dyus kay', "tullup'aki", 'baryu', 'paca', "ch'iqtana", 'shuc', 'llullu', 'huti', 'ñawi', 'qhali kay', 'inti wayta', 'watuq', 'intichay', "q'umpuyasqa", 'llika', 'munay', "wak'a", 'allpa kawsay', 'huk', 'majá', 'unquy', 'costa', "rimay t'ikray", 'tayta', 'churi', 'uma raymi killa', 'kawra', 'musyay', 'phiruru', "ch'iraw mit'a", 'punlla', 'chawpi', 'sumaq', 'sayaq runa', 'chakra', 'uyariy', 'sutip rantin', 'pachanka', 'qhichwa', 'kurku', 'chiqap', "k'iti", "k'uychichaw", "mayu hark'a", 'pinchikilla pusaq', 'kuyu walltay', 'wañuy', 'urpu', "pawcarmit'a", 'runa suti', "t'aqa", 'qalla', 'pachyay', 'qari', 'rimay', 'qhasqu', 'siwk patma', 'rawta', 'apaykachay', 'apu', 'willay pukyu', 'yachachiy', 'lichi'}, 'b0': {'tuktu'}, 'b1': {'karka', 'rakiy', 'rikchʼaq putu', "p'acha", 'waita', 'tantanakuy', 'saqru', 'wasichay', 'qatasqa muruyuq', 'wasi', 'wayta', "t'ipi", 'kawsaykuq tantalli', 'yura', 'wasikuna', 'sumaq wasichay kamay', "rikch'aq t'aqa", 'tika', 'hatun kamachi', 'rikch’aq putu', 'tuktu', 'pampa suyu', 'wasi qata', "t'ika", 'miraykuy', "t'aqa", 'sisa'}, 'b2': {'punku', "wat'a", "mayu hark'a", 'irraminta', 'tantanakuy', 'wallqanqa sanancha', "q'illay kañina", 'pacha kawsay', "t'ikay", 'qincha', 'nina', 'wasichay', "p'achallina", 'llimphiy', 'suti', 'yura', 'wasikuna', 'tika', 'rikch’aq putu', 'yupay', 'pukyumanta willay', 'wallpari', "samk'ay wasi", "wirp'a", 'qatasqa muruyuq', "sach'a", "hak'u", "p'aqchi", 'kawsaq', 'thay simi', 'pʼunchay', 'awqaq suyu', 'pukyu', 'wara', 'qillqarajjpa', 'qañipu', 'wallqa', 'sisa', 'inti wayllay', 'pirqaq', 'tara', 'hatun llaqta', 'aya', 'llaqta', 'ñawiriy', 'sami', 'kusituy', 'paqariy', 'yapay', 'nuna', "p'uchqu", 'yaku qullqi', 'tihiras', 'pampa', 'kawsachikuy', 'waqay', "hallka k'iti k'anchar", 'kusikuy', 'sinchiyasqa', "k'aspi", 'iskaychunka', 'hatun kamachi', 'yachay', 'akawara', 'chincha', 'sanurya', 'ñawi', 'ninri', "rikch'aq ayllu", "siq'iy", 'tajáo', 'uchuy llaqta', 'ruruchina', 'yoga', 'suyu', "siwk siq'i", 'kinraysuyu', 'urqu', 'alli', 'ayllu', 'waki', 'sillu', "tullup'aki", "khipu q'aytu", 'tawna', 'kawsaykuq tantalli', 'gata', 'pampa suyu', 'tinti kaballu', 'miqu', 'ñasa', 'sapra', 'ruru', 'mikhuna', 'uywa', 'kuska', "p'unchaw", "q'imi", "suqtawask'a", 'runa llaqta', 'chunka iskayniyuq', 'wakcha', 'takarpucha', 'chawpi', 'mayllay', 'chillki', "hunt'a rimay", 'saca', 'wisina', 'millma', 'ñuqa', 'churiyaqe', 'qhatuna', 'uwiha', "wach'i", 'uya', 'aminakoyim', 'kuyuy', 'khuchi runtuchi', 'humu', 'kawsay', 'paray', 'yura kurku', "rikch'aq sinri", 'thansa', 'siwk patma', 'kancha', 'yachay munaq', 'saywa', 'miraykuy', 'bonn', 'churay', 'chuqi', 'shimi', 'rakiy', 'wasi ukhu', 'chakra yura', 'waranqa', 'haca', 'kuskanachina tupu', 'uqi', 'tarpuy', 'llika', 'runa', 'tata', 'órgano', 'allpa kawsay', 'sutirimana', 'hanchi', 'chakakuq', "rikch'aq putu", "t'uqyaylla", 'ratata allpa', 'saphi', 'rakha', 'api', 'kiru', 'yuraq', 'waita', 'kuru qulluna', 'qiru', 'tayta', "k'aschina", 'yapa', 'wiksa', "yupa hap'ichiy", "ch'amanaku", 'kurkumanta yachay', 'wiksayay', 'phawrika', 'runa kuchuy', 'isanka', 'k', 'qhuya', 'huacra', 'wincha', 'chiqa', 'achikay', 'waqra', "p'uku", "llamk'ana", 'wanqhana', 'pachapanta', 'kurku yawri', 'sullu', 'micha', 'allpa', "jak'u", 'willa', 'yachachiy', 'awarmatu', 'ruray rimana', 'kuyuylla', 'qurpa', 'achala', "sut'i", 'tullpuy', "t'ipi", 'asinda', 'pruphisyun', 'kuyu walltay', 'kaphiy', 'rikchʼaq putu', 'yugur', 'sacha', 'chaqui', 'pachanka', 'kutipakuy', 'quyllur', "llank'ay", 'tisqu', "rikch'ana", 'muru', "rikch'aq suyu", 'millay qura', 'chupa', "p'allta", "rikch'aq t'aqa", 'sumaq wasichay kamay', "rikch'aq", 'ruway', 'wasi qata', "t'ika", 'minutu', 'kulunya', 'tupu', 'waysallpu', "mit'awi", 'miray', 'tantachisqa', 'silulusa', 'chunka iskayniyuj', "ñaqch'a", "llipt'a", 'muna-', 'watʼa', 'turri', "k'allma", 'rit’i', "ch'askancha", 'ruray', 'munay', 'tiqsimuyu', 'churana', 'casa', 'punchu', "rak'i", 'waylluy', 'kulli', 'qhatuq', "rikch'aqyay", "ich'ikapuru", 'unancha', 'chaki', 'makipura', 'tunu', 'millwa', 'p’unchay', 'kallpa', 'taripay suntur', 'para', 'iskay', 'ruraychaqa', 'mallki', 'arkhitiktura', 'puka llanqa', 'ñuñu', 'kusasqa tika', 'bronquiolo', 'wayu', "t'aklla", 'kay pacha', 'puka', 'rurana wakichi', 'sallqa akllay', 'llanqha', "q'illay", 'tuktu-tuktu', 'chakana', 'ppacha', 'wayta pata', "t'aqa", "q'imiy", "rit'i", 'ima', 'aysana', 'rimay', 'wapsichana iñu', 'karka', 'aranwa', "hamut'ay", 'imayay', 'aqu', 'wiru', 'parte', 'puywanku', "q'aytucha", "husk'ay", "ch'usaq pacha", "rikch'aq ñiqi", 'pichana', 'qullqi wasi', 'waytay', "ch'akiy", 'qichuy', "wichaykuna k'aspi", 'wisnu', 'riy', 'kawsay yachay', 'arpay', 'pacha', 'mama llaqta', "t'ipki", 'partes', "ch'iqtaku", 'wasi', 'simi', 'tiksimuyu', 'siqana pata-pata', 'sachakuna', 'kapchiy', 'chukcha kʼutu', 'yachay wayllukuy', 'allpa pacha', 'lichi', 'raphi', 'kintu', 'kunka', 'allwiya kamay', 'kañina', 'raqta', 'flur', 'mama', 'yuraj', 'maki', 'iskay chunka', 'suqta', 'kawsaykuq', 'diyosuun', "ullu k'aspiyay", 'majá', 'puririy', 'shuc', 'yupay saphi', "p'acha", 'ñan', 'aymuray', '+', 'taki', "t'anta", 'samay', 'saqru', "llamk'ay", 'tullpuna', 'wayta', 'kunan pacha', 'yachay wasi', 'huasi', 'awaq', 'saynata', 'kalindaryu', 'lima', 'tuktu', 'iruru muyu', 'pinus', 'kurku'}, 'c0': {'pikchu'}, 'c1': {"ch'usaq pacha", 'sacha', 'lichi', 'maymanta', "hallka k'iti k'anchar", 'pachamama', 'pampa', 'alli', 'chuntu', 'runa llaqta', 'qhatu', 'paza', 'chuqu', 'chuntu wasi', 'tiksimuyu', "llipt'a", 'chawpi', 'hirka', 'rumi kaq', 'tiqsimuyu', 'tiyarina', 'puririy', 'qaqa', 'pacha', 'hatun llaqta', 'parte', 'uma', 'pikchu', 'orgo', 'tiksi muyu', 'paca', 'uchuy llaqta', 'wisnu', 'allpa', 'rumi', 'urqu', 'suyu'}, 'c2': {'chiqap', 'shimi', 'ichhuna', 'taki', 'tunqori', 'tarpuy killa', "hallka k'iti k'anchar", 'sinqa', "hamp'ara", 'siwk patma', 'rikchʼaq putu', 'wayru', 'chaqrusqa', 'ayllu', 'titi', 'chiqaluwa', 'kuchillu', 'bern', 'nanay', 'ñasa', 'phutikuy', 'uywa', "p'allta", 'purun', 'b', 'kusasqa tika', 'paca', 'ura', "wat'a", 'qullqi wasi', 'wallata', 'paña', 'willay pukyu', 'haca', 'saywa', "k'ullu", 'hijo', 'sachakuna', 'wañuy', 'illwa', "mayu hark'a", 'qiqlla', 'paza', 'llimphiy', 'kañina', 'cupa', 'rantina qullqi', 'tantachisqa', "t'aqa", "t'aklla", 'lampa', 'ñuñuq', 'willachikuy', 'pacha mitʼa', 'sallqa', 'pirqa', 'wasi ukhu', 'yuraj', 'puririy', 'intichaw', 'waricha', 'hanaq pacha', "t'uqyay", "q'asa", 'hatun llaqta', 'uchuy llaqta', "ch'usaq pacha", 'paqariy', 'qincha', 'kʼuychichaw', 'niy', 'khillay', 'wasi', 'orqo', 'kawsay', 'llasaq kay', "rikch'aq", 'sinchiyasqa', 'khuyay', 'chikchi', 'yura', 'qillqara', 'machuruku', "rikch'aq ayllu", 'sachʼaqa', "p'achallina", "ch'aqiy", 'órgano', 'uma', 'kayma', "k'iri", 'wakta', 'allpa', "mit'a", 'yachachiq', 'kratir', 'qalla iruru', 'muru', 'panti', 'sika', 'iñuku', 'centre', 'akawara', 'wiñay kawsay', "mach'aqway", 'pinchikilla pila', 'partidu', "k'allma", 'qhatu', 'llanthu', 'muna-', "mit'apu", 'sami', 'takana', 'qhaway', 'ñuñu', 'arininakuy', 'salina', 'thuñi', 'partes', 'wasichay', 'yuma kurucha', 'sikundu', 'kallpa', 'iyun', 'kuyuy', "p'acha", 'aqu', 'yuyaychakuy', 'nuna', 'pinchikilla pusaq', 'yoga', 'hallpa', "jamp'ara", 'kaoko', 'phawrika', "k'ukti", "llut'ariy", 'llawchʼinchu', "ch'amanaku", 'suni', 'republika', "wamink'a", 'karu kay', 'kurku yawri', 'ñan', 'chʼuspi', 'tullu muqu', 'chaski qillqa', 'parte', "q'imina", 'tantanakuy', 'kunkalla', 'kulunya', 'chaqna', 'allpay', "rikch'aq putu", "jisq'un", 'mallki', 'huahua', "ch'iqta", 'aycha kanka', 'ruru', 'tahua', 'irraminta', 'paray', 'mama', 'samay', 'mama llaqta', "rimay t'ikray", 'wayaqa', 'yuri', 'ankalli', 'tullu', 'wasi qata', 'kay pacha', 'ñuqa', 'diyosuun', 'yunka', 'minutu', 'machu', 'wallpama', 'tiyana', 'quyllur', 'kuyuchina', "k'iraw", 'ima', 'asinda', 'waki', 'ruruchina', "rikch'aq t'aqa", "t'inki", 'kapchiy', 'de', 'chumpi', 'rantiy', 'machapu', 'pacha kawsay', 'illanchay', 'qhatuq', 'llullu', 'quyllurchaw', 'chullusqa', 'thansa', 'tihiras', 'chakra', 'punku kirma', 'sumaq', 'tiksi muyu', 'qillakuq', "k'uychichaw", 'qam', "ch'usaq p'ulin", "t'ipi", 'witi', 'rawta', "sut'u", "p'allta muyu", 'kawitu', 'köln', 'tawa', 'sankhu', 'tigri', 'wasa ruru', "ch'uspa", "rak'i", 'sutip rampaqnin', 'wien', 'sasachakuy', 'utku suni', 'chimpa', 'idruhinu', 'phiruru', 'allpa pacha', 'ñaso', 'huasi', 'allin simi', 'willa', 'tiqsimuyu', 'umalliq', 'qurwara', 'wasikuna', 'tuyur', 'hanchi', 'tunki', 'chaka', 'evitar', "sut'i", 'suti', 'suwa', 'chanqiyay', "ch'in pacha", 'nina', 'kuskanachina tupu', "mach'ay", 'humu', 'rikch’aq putu', "p'aqchi", 'aqochay', 'k’uychichaw', "ch'askancha", 'allpachay', 'pampa', 'kusa', 'tiksimuyu', 'simi', "llipt'a", 'churi', 'urin', 'chupa', 'raymikis', "k'isura", 'kinsa', 'achkha yupa', 'pachanka', 'tiksi', 'juk', 'yapay', 'qullqa', 'utqa kay', 'khipu', 'kuska', 'ruqyay', 'pukyu', "q'aqcha", "willay p'anqa", 'hatun kamachi', 'karka', 'qhichwa', 'wisnu', "ch'iqtaku", 'ankucha', "t'anta", 'qallawa', "sach'a-sach'a", "rikch'ay", 'hatun', 'erqe', 'valencia', 'mapa mama', 'qhari', 'siquta', "yaqa wat'a", 'chuqu', "tullup'aki", 'sumaq wasichay kamay', 'hirka', 'wasa', 'ismuy', 'qaqa', 'tuncuri', 'qhepajj raymi killa', 'sach’ara', 'machina', 'tarpuy', 'qiru', 'urqu', 'awqaq suyu', 'arí', 'rumi', 'chiqa', 'ago', "wichaykuna k'aspi", 'paya', 'rimay', 'musyay', 'yura pacha', 'maymanta', 'thak', 'yuyu', 'pachapanta', "ch'away", 'chuntu wasi', 'toes', 'riy', 'shuc', 'chuki', 'chaki', 'asiru', "samana p'urucha", 'pallpa', "llamk'ana", 'muyuriq pacha', 'janajjpacha', 'qhelli', 'wañu', 'qalla', 'aminakoyim', 'awaq', 'ridusiy', "k'uskiykuy", 'wanay', "sut'ichay", 'chaski', "hunt'a rimay", 'wiksa', 'yupay saphi', 'lichi', "q'illay kañina", 'huk', 'puywanku', 'pachamama', 'yakuchaq', 'qachu', "rikch'a kapchiy", 'puriq quyllur', "ullu k'aspiyay", 'chhukruna', 'qelqay', "ch'iqtana", "p'unchaw", 'imayay', 'chawpi', 'rumi kaq', 'hatun illapa', "wichq'ana", 'wawa', 'pichana', 'orgo', 'allpanay', 'pay', 'yachaq', 'suyu', 'kamachi', 'saca', 'simana', 'sallqa pacha', 'runa suti', 'ñawi', 'sonqo', 'chuntu', 'hayway', 'yupa huqariy', 'tapuy', 'yura kurku', 'runa sipiy', 'achulla', 'llaqta', 'uyariy', 'yachay suntur', 'makipura', 'asina', 'intillama', 'kawsaykuq tantalli', 'sallu rumi', "mit'awi", 'kancha', 'yananara', 'apaykachay', "suqtawask'a", 'wata', 'allpa kawsay', 'puriqlla', "hatun p'unchaw", 'jaqaypi', "lunq'u", 'munay', 'awki', 'pachak', 'sacha', "rikch'aq sinri", 'waylluy', 'uma llaqta', 'sunqu', 'allin', 'pachyay', "hap'iqay", 'kamachina', 'runa', 'alli', 'manchakuy', "rikch'aq ñiqi", 'willakuy', 'kurku', 'usa', 'yuraq', "rikch'aq suyu", 'chhuka', 'yawri', 'wira', 'inti', 'qhula', 'saqru', 'pacha tupuy', 'yupay', 'sapra', 'khilla', 'mánan', "p'uku", 'hatun qucha', 'mallés', 'sinca', 'tawantin iñu', 'rakiy', "sach'a", 'tara', 'llakikuy', 'atiyniyuq kay', 'kinraysuyu', 'baryu', 'rima', 'sipas', "t'oqo", 'kunka', 'yachay munaq', "ch'usaq", 'pachakwata', 'sinchi', 'tisqu', 'chiqan chhuka', "qillqana p'anqa", 'sutirimana', 'uña', 'linti', 'pupu', 'kutipakuy', 'hampi yachay', "wamp'urani", 'runa llaqta', 'ruray', 'iñuwa', 'arpay', 'pedo', "hutk'una", 'wapsi kuyuchina', 'wayrayuq', 'sachʼa-sachʼa', "wach'i", 'churay', 'simsiker', 'iruru muyu', 'pampa suyu', 'tiyarina', "llamk'ay", 'pacha', 'watʼa', 'pikchu', 'kiru', 'sach’a-sach’a', 'chapaq'}}

	# ^^ if using one of these preloaded dictionaries, comment out the chunk of code below
	input = input_exists()
	build_data(input[0], 3, 'a')  # this is 2 levels deep, dont surpass it or else the dictionary will think we're a bot
	print(big_dicto)
	build_data(input[1], 3, 'b')
	print(big_dicto)
	build_data(input[2], 3, 'c')
	print(big_dicto)

	scores['algoScore0'] = get_score('b')
	scores['algoScore1'] = get_score('c')

	scores['word2VecScore0'] = check_word2vec_similarities(input[0], input[1])
	scores['word2VecScore1'] = check_word2vec_similarities(input[0], input[2])

	print(scores)

	print('percent change in similarity scores between first word pair (' + input[0] + ', ' + input[1] + ') and second word pair (' + input[0] + ', ' + input[2] + ')')
	print('for dictionary algorithm: ' + get_pch(scores['algoScore0'], scores['algoScore1']))
	print('for word2vec algorithm: ' + get_pch(scores['word2VecScore0'], scores['word2VecScore1']))

main()
