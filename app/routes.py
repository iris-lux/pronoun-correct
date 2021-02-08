from app.pronoun import Pronoun
from flask import Flask,render_template,url_for,request
from app import app 
import re
import spacy
from spacy.matcher import Matcher 
from spacy import displacy
import en_core_web_sm
import neuralcoref 
from simplenlg.lexicon import Lexicon 
from simplenlg.realiser.english import Realiser  
from simplenlg.framework import NLGFactory 
from simplenlg.phrasespec import SPhraseSpec
from simplenlg.features import Feature 
import re 





#have a switch for updating they/them pronouns: neuralcoref.add_to_pipe(nlp, greedyness=0.6)

def find_cluster(target_name, doc):
    for cluster in doc._.coref_clusters:
        print(cluster)
        if(cluster.main.text == target_name):
            return cluster 
    return None 

def pronoun_case(pronoun_text):
    pronoun_case_switch = {
        'she': 'SUBJ',
        'he': 'SUBJ',
        'they' : 'SUBJ',
        'her': 'OBJ',
        'him': 'OBJ',
        'them' : 'OBJ',
        'their' : 'POSS_WK',
        'his': 'POSS_STRG',
        'hers' : 'POSS_STRG',
        'theirs' : 'POSS_STRG',
        'herself' : 'REFLX', 
        'himself' : 'REFLX',
        'themself' : 'REFLX',
        'themselves' : 'REFLX'
    }
    #find better default case?
    return pronoun_case_switch.get(pronoun_text, 'SUBJ')
    
def token_index(altered_token):
    return altered_token['token'].i

def pronoun_replacement_text(pronoun, pronoun_replacement):
    #replacement = pronoun.text
    if pronoun.pos_ == 'DET': 
        replacement = pronoun_replacement.equivalent_pronoun('POSS_WK') 
    else: 
        replacement = pronoun_replacement.equivalent_pronoun(pronoun_case(pronoun.text.lower()))

    if(pronoun.text == pronoun.text.capitalize()):
        replacement = replacement.capitalize()
        
    return replacement 

def head_replacement(head): 
    if head.text == 'is':
        return 'are' 
    elif head.text == "'s":
        return "'re" 
    else:
        return head.lemma_ 
#if the pronoun being corrected is they/them, and is the subject then the verb will be plural 
# if pronoun_replacement is not gramatically plural, and if pronoun.text is they/them/theirs/themselves/themself
# then append hash of head token and method call to replace_plural_head(head)
def replace_plural_head(head): 
    regex = re.compile('[a-z]+')
    lex = Lexicon.getDefaultLexicon()
    realiser = Realiser(lex)
    nlgFactory = NLGFactory(lex)
    p = nlgFactory.createClause()
    p.setVerb(head.text)
    p.setSubject("she")
    return regex.match(realiser.realiseSentence(p).split(" ")[1]).group()

def list_pronouns(mentions, pronoun_replacement):
    #make this list a list of tuples? or a hash? hash two keys, altered_token, replacement 
    pronouns = []
    it_its = ['it', 'its']
    for mention in mentions:
        if len(mention) == 1 and (mention[0].tag_ == 'PRP' or mention[0].tag_ == 'PRP$') and not(mention[0].text.lower() in it_its):
            print(mention.text, 'tag', mention[0].tag_, spacy.explain(mention[0].tag_))
            print(len(mention))
            pronouns.append({'token': mention[0], 'replacement_text': pronoun_replacement_text(mention[0], pronoun_replacement)})
    return pronouns 

def list_present_tense_heads(pronouns, pronoun_replacement):
    present_tense_heads = []
    they_them = ['they', 'them', 'their', 'theirs', 'themselves', 'themself']
    for pronoun in pronouns:
        print(pronoun['token'].text, pronoun['token'].head, pronoun['token'].head.tag_, spacy.explain(pronoun['token'].head.tag_))
        if(pronoun_replacement.gramatically_plural and pronoun['token'].dep_ == 'nsubj' and pronoun['token'].head.tag_ == 'VBZ'):
            print(spacy.explain(pronoun['token'].head.tag_))
            present_tense_heads.append({'token': pronoun['token'].head, 'replacement_text': head_replacement(pronoun['token'].head)})
        elif((pronoun['token'].text in they_them ) and pronoun['token'].dep_ == 'nsubj' and pronoun['token'].head.tag_ == 'VBP'):
            present_tense_heads.append({'token': pronoun['token'].head, 'replacement_text': replace_plural_head(pronoun['token'].head)})

    return present_tense_heads

# have an another field 
def replace_pronouns(orig_text, name, pronoun_replacement, nlp, correcting_they_pronouns = False):

    #for singular they transformation
    #text, indexes to revert. 
    #cache? 

    if(correcting_they_pronouns):
        nlp.remove_pipe("neuralcoref")  # This remove the current neuralcoref instance from SpaCy pipe
        neuralcoref.add_to_pipe(nlp, greedyness=0.6)

    doc = nlp(orig_text)
    text = []
    buffer_start = 0
    name_cluster = find_cluster(name, doc)
    if name_cluster == None:
        return 'No Match'
    #need to check if mention is pronoun
    print(name_cluster.mentions)
    
    pronouns = list_pronouns(name_cluster.mentions, pronoun_replacement)
    present_tense_heads = list_present_tense_heads(pronouns, pronoun_replacement)

    altered_tokens = pronouns + present_tense_heads 
    altered_tokens.sort(key=lambda altered_token: altered_token['token'].i)
    print('altered_tokens', altered_tokens)
    for altered_token in altered_tokens:

        if altered_token['token'].i > buffer_start:  # If we've skxipped over some tokens, let's add those in (with trailing whitespace if available)
            text += [{'text': doc[buffer_start: altered_token['token'].i].text + doc[altered_token['token'].i- 1].whitespace_, 'is_pronoun': False, 'index': altered_token['token'].i, 'orig_text': altered_token['token'].text}]
        text += [{'text': altered_token['replacement_text'], 'is_pronoun': True, 'index': altered_token['token'].i, 'orig_text': altered_token['token'].text}] 
        text += [{'text': doc[altered_token['token'].i].whitespace_, 'is_pronoun': False, 'index': altered_token['token'].i, 'orig_text': altered_token['token'].text}]  # Replace token, with trailing whitespace if available
        buffer_start = altered_token['token'].i + 1

    text +=  [{'text': doc[buffer_start:].text, 'is_pronoun': False}]

    text = [altered_token for altered_token in text if altered_token["text"] != '']

    return text

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/process', methods = ["POST"])
def process():
    results =[]
    num_of_results = 0
    nlp = spacy.load('en_core_web_sm')
    neuralcoref.add_to_pipe(nlp)
    # if request.method == 'POST':

    rawtext = request.form['rawtext']
    name = request.form['name']
    pronoun_option = request.form['pronoun_replacement']
    correcting_they = request.form.get('correcting_they', False)
    print(correcting_they)
    pronoun_replacements = {
        'she' : Pronoun('she', 'her', 'her', 'hers', 'herself'),
        'he' : Pronoun('he', 'him', 'his', 'his', 'himself'),
        'they' : Pronoun('they', 'them', 'their', 'theirs', 'themself', True)
    }

    output = replace_pronouns(rawtext, name, pronoun_replacements[pronoun_option], nlp, correcting_they)


    return render_template("index.html", translated = output, orig_text = rawtext)
@app.route('/revert', methods = ["POST"])
def revert():
    return None

if __name__ == '__main__':
	app.run(debug=True)