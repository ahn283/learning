# install library
# !pip install spacy
# download model from spacy
# !python -m spacy download en-core

import spacy

nlp = spacy.load('en_core_web_sm')

document = '''
Mark Zuckerberg laid out Meta's gameplan for "playing to win" against Alphabet and Microsoft in the high-stakes AI arms race. Meta's secret weapon: its walled garden of data.

"There are hundreds of billions of publicly shared images and tens of billions of public videos, which we estimate is greater than the common crawl data set,” Zuckerberg said on Meta’s earnings call on Thursday. It was a not-so-subtle jab at competitors Google, Microsoft and OpenAI, which are training their AI models on the public web data crawled by their search engines every day.
'''

doc = nlp(document)