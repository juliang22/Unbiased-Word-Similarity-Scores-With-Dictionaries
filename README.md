</p align="center"># Unbiased-Word-Similarity-Scores-With-Dictionaries</p>
Final Project for Computational Linguistics, Dartmouth College 20S


**Unbiased Word-Similarity Algorithm**

*****

Julian Grunauer (Julian.A.Grunauer.21@Dartmouth.edu)
Faustino Cortina (Faustino.Cortina.21@Dartmouth.edu)
Dartmouth College - Computational Linguistics

**ABSTRACT.** Word-Similarity algorithms are used to determine word meanings through comparison and are used both in research settings (psychology, cognitive science, linguistics, etc...) and in practical affairs (law, consumer-analysis, technology, etc…). Despite their widespread use, the results of these algorithms are often biased by their data-source and require vast data-sets to train the similarity models. Thus, our idea for this project was two-fold: (1) create an algorithm that is comparable to word2vec’s  similarity scores, but without the bias that word2vec often displays and (2) find a way to mine data that isn't dependent on large swaths of transcribed text so that our algorithm could be implemented for low-resource languages. At the onset of this project, we viewed dictionaries as the perfect data source because of their existence within low-resource languages and we viewed dictionaries as an unbiased source of semantic information. Our hypothesis did not prove true and our results were mixed. Our algorithm often performed better than word2vec for words that are intuitively similar and sometimes managed to remove some contextually biased word-pairings. However, in the course of this project we realized that dictionaries themselves are often biased and these biases carried over into our results. Thus, in many instances, biases in word2vec were also found in our algorithm.





**Introduction**
One important aspect of Natural Language Processing is the capacity for algorithms to capture the meaning of words—their semantics, how they are used, and how they are related. From search engines, to legal matters, to language learning, to corporate customer service, the ability to compare word meanings is an important and useful tool. Unfortunately, the corpuses of data powering machine learning models for various languages are extremely biased, and these biases are clearly shown in the relationships between words. For example, when comparing the words “man” and “home” in French, the top word paired with this relationship was “aristocrat.” For “woman” and “home,” the top word is “servant.” While these types of biases are important in understanding our culture, values, and how we use language, they are also extremely dangerous. Biases that aren’t caught or that are caught but aren’t removed will continue to be perpetuated in whatever the machine learning is being used for. From a judicial model dealing out racist sentences to sexist twitter bots, the need for a method of capturing meaning from data while removing bias is an essential piece of improving machine learning and AI. Similarity algorithms that already exist, like word2vec, GloVe, and fasttext, are not inherently biased themselves, it’s the data they use and their reliance on contextually-related  analysis (i.e. looking at how related a word is to words around it) which we believe is causing biasing issues. 
In this project, we hypothesize that similarity scores produced from a novel word-similarity algorithm (created with non-contextual, dictionary-based data) would be able to capture and compare the true meaning of words, without perpetuating cultural biases often found in other algorithms. While we would lose the contextual relationship between words, and thus lose the various flavors for how words are used pragmatically, we believe that our algorithm would retain much of the word’s inherent meaning and its comparisons would be on par with unbiased word-to-vec relationships.  

**Methodology**
The main algorithm being used is our own novel similarity algorithm which uses an online Quechua-to-English and an English-to-Quechua dictionary [1]. To gather our data we used the BeautifulSoup api to web scrape a Quechua to English and English to Quechua dictionary. The user inputs 2 Quechua words, our algorithm searches them in the Quechua to English dictionary, gathers the English words in each definition, normalizes the text, filters the words to include only nouns, removes any repeat words, translates them back to Quechua (which could have multiple Quechua synonyms for that English word), and then all of those Quechua words are searched for their definitions. This continues for two layers and amasses a huge set of Quechua words and their respective levels.  
The similarity score is calculated through the following procedure: our algorithm takes the definition of each Quechua word and looks at the words in each definition. It tracks any matches between the two definitions. Our algorithm next goes another layer deeper by getting the definitions of each word of our initial definitions. It again looks for word matches between the two sets of definitions. Our final score is calculated by summing up these matches and giving more weight to matches between words that are the most relevant to the definition of our target word. If a definition word directly matches with the target word, then that is given a very high weight. We normalize these cumulative scores by the size of the wordlists; this is done to ensure words with longer definitions aren’t getting higher scores simply by having more more words to compare.  

**Results**
Since there is no single ‘correct’ quantitative answer for how ‘similar’ two words are, we can’t judge our algorithm using conventional metrics, such as precision or accuracy, that require knowledge of a correct answer to a given input. We decided that the best way to judge the efficacy of our algorithm is to compare it to a pre-existing word similarity model that has been proven to be effective. We chose a pretrained word2vec model [2] as this baseline algorithm, and calculated the word2vec similarity by getting the cosine similarity of the 2 word vectors being compared.
Another important consideration in our analysis is that our algorithm and word2vec have score ranges that do not align. Our algorithm has a similarity score in the range 0-2.25, while word2vec has a range of 0-1. Even if we were to normalize our algorithm to be in a 0-1 range, our algorithm may not scale in the same way word2vec does (for instance, it is very difficult to get a perfect score in our algorithm, so even a relatively lower score would still be considered ‘good’ for our algorithm, while for word2vec, this may not be the case). We got around this issue by focusing on the percent change in the similarity score of two different word pairs. For instance, if both our algorithm and word2vec were to give a 50% higher score to the word pair (dog, wolf) vs (dog, cat), then we can say that both algorithms are acting similarly. 
Since our algorithm is relatively slow and since our web scraper code cannot make too many queries without the online Quechua dictionary throwing an error, we did not have the time to do an analysis over a lot of word pairs. We instead decided to handpick some word pairs that we thought may produce some interesting results (see the tables below).
Overall, there seems to be a somewhat positive correlation between our algorithm’s similarity scores and that of word2vec. For instance, in the first three rows of Table 1, our algorithm gave a higher similarity score to the same word pair that word2vec did. In row 4, both algorithms gave similarity scores for (llama, alpaca) vs. (llama, spider) that were not that different from one another (see Table 2 for the exact scores) although, our algorithm and word2vec disagreed over which word pair was more similar. Intuitively, (llama, alpaca) should be more similar than (llama, spider), which is what our algorithm chose, so even though it disagreed with word2vec, it may have given a more accurate output. In the last row however, our algorithm significantly diverged from word2vec, likely due to some biases that will be explained below.
We decided to focus on gender biases for a couple of the rows in Table 1 to further explore the differences in biases between a dictionary and context-based approach. When comparing (house, woman) vs. (house, man), our algorithm found that (house, man) was almost three times more similar than the word pair (house, woman), which intuitively does not make sense. Word2vec also gave a much higher similarity score to (house, man), although not nearly as much as our algorithm did (78.6% higher for word2vec vs 182% for our algorithm). When comparing (warrior, woman) to (warrior, man), our algorithm found that (warrior, man) was over 10 times more similar (1153% more similar to be exact) than (warrior, woman). Interestingly, word2vec actually found (warrior, woman) to be slightly more similar than (warrior, man).
We used the (sacred, flower) vs (sacred, mountain) word pair comparison to explore context-based biases that are specific to the Quechua language. In many Andean religions, mountains were considered to be very sacred, and it was very common for offerings to be made to some of the largest, most sacred mountains. As a result, it is possible for (sacred, mountain) to have an unusually high similarity score in word2vec as a result of context-based associations between mountain and sacred that may not be as prevalent in dictionary definitions. Our results precisely showed this, with (sacred, mountain) being considered twice as similar to (sacred, flower) in word2vec. Our algorithm also found (sacred, mountain) to be more similar, but it had a much less extreme increase in similarity than word2vec (39% vs. 138%), implying that our algorithm may have reduced some contextual biases in this example.


![table 1](results/table1.jpg)

![table 2](results/table2.jpg)



**Discussion**
	Our paper had two primary goals: to create an effective dictionary-based word similarity algorithm that can be applied to low-resource languages and to reduce the biases of context-based algorithms by using dictionary definitions.
	I will first discuss the first goal of creating an effective word similarity algorithm for low resource languages. I would say that overall, our algorithm did a moderately good job determining similarities between words. For instance, our algorithm gave a relatively high score to the similar word pair (cat, lion) and a low score to the dissimilar word pair (llama, spider). Also, as mentioned in the results, our algorithm performed somewhat similarly to word2vec when we compared various combinations of word pairs.
	However, the biggest surprise from our results is that our algorithm did not do a good job removing context-based biases from word similarity scores. In fact, at times, it seems like our algorithm actually increases the biases from word2vec. A large reason why this occurred is because our Quechua-English dictionary had a lot more biases than we had initially anticipated. For instance, when looking at the definition of ‘man’ in the Quechua-English dictionary, one of the definitions was ‘courageous, brave, strong’, which we found surprisingly biased for a dictionary. It was actually this definition that encouraged us to examine the difference between the word pairs (warrior, woman) and (warrior, man) which sure enough exposed that our algorithm had a significant bias towards attributing objects related to bravery or courage to a man (warrior and man were over 10x more similar than warrior and woman). 
Despite our algorithm’s struggles removing some biases, there were times where biases that existed in word2vec were successfully removed by our algorithm. For instance, as described in the results section, our algorithms removed the context-based biases that may exist between sacred and mountain as a result of religious biases in Quechua-speaking cultures.
One interesting thought for why our Quechua-English dictionary was so biased is because perhaps lower-resource languages may not have time or resources to thoroughly proof-read dictionaries for human-induced biases. This may result in more biased or inaccurate dictionaries for lower-resource languages, which would be an issue we would need to take very seriously if we were to consider using our algorithm with other low-resource languages.
While our algorithm still has some biases, it is still a fairly accurate word similarity algorithm that does not require any machine learning on corpuses of data. This would make our algorithm very beneficial to any low-resource language that does not have enough written data to train context-based word similarity algorithms. Our algorithm will also contribute to the computational linguistics field by providing linguists with an baseline dictionary-based algorithm that can be used as a model for creating even better dictionary-based algorithms in the future.
The only ethical consideration with our algorithm is that it is scraping information from a Quechua-English dictionary that has safeguards to prevent excessive web scraping from computers. While our intents are not malicious (like cloning their dictionary for monetary gain), we are still attempting to make a large quantity of programmatic requests on a dictionary that does not like that.

**Conclusion**
To sum up, we succeeded in creating a lightweight word similarity algorithm that does not require machine learning or any data outside of a dictionary, and we did this in a fairly low resource language, Quechua. While our algorithm was moderately successful in finding similarities between words relative to word2vec, it struggles to remove context-based biases from word2vec, and actually contributed sizable biases from dictionary definitions.
In the future, our algorithm can be applied to other dictionaries in other languages. Theoretically, it is possible to use our algorithm in any language that has an online dictionary, however, our results have shown us that it is very important to ensure that the dictionary we choose is not too biased in its definitions. It is likely that lower-resource language dictionaries are more likely to exhibit biases, as curators of these dictionaries are more likely to have less time and resources at their disposal to thoroughly revise these dictionaries.
Another potentially interesting application of our algorithm is to try it on a higher-resource language and see whether its effectiveness increases as a result of a potentially more unbiased dictionary. It is possible that higher-resource languages, like English, with more meticulously curated online dictionaries may do a better job reducing biases than our Quechua-English dictionary did. 



References
The Quechua-English dictionary we used was https://glosbe.com/en/qu 
The pretrained word2vec model was taken from https://github.com/facebookresearch/fastText/



