from app.pronoun import Pronoun
from flask import Flask,render_template,url_for,request
from app import app 
import re
import spacy
from spacy.matcher import Matcher 
from spacy import displacy
import en_core_web_sm
import neuralcoref 

nlp = spacy.load('en_core_web_sm')
neuralcoref.add_to_pipe(nlp)
#have a switch for updating they/them pronouns: neuralcoref.add_to_pipe(nlp, greedyness=0.6)
she_her_hers = Pronoun('she', 'her', 'her', 'hers', 'herself')
he_him_his = Pronoun('he', 'him', 'his', 'his', 'himself')
they_them_theirs = Pronoun('they', 'them', 'their', 'theirs', 'themself')


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

def replace_pronouns(orig_text, name, pronoun_replacement):

    #for singular they transformation
    present_tense_heads = []
    pronouns = []
    doc = nlp(orig_text)
    text = ''
    buffer_start = 0
    name_cluster = find_cluster(name, doc)
    if name_cluster == None:
        return 'No Match'
    #need to check if mention is pronoun
    print(name_cluster.mentions)
    
    for mention in name_cluster.mentions:
        if len(mention) == 1 and (mention[0].tag_ == 'PRP' or mention[0].tag_ == 'PRP$'):
            print(mention.text, 'tag', mention[0].tag_, spacy.explain(mention[0].tag_))
            print(len(mention))
            pronouns.append(mention[0])

    for pronoun in pronouns:
        # print(mention.text, 'tag', mention[0].tag_, spacy.explain(mention[0].tag_))
        # print(len(mention))
        if pronoun.tag_ == 'PRP' or pronoun.tag_ == 'PRP$':
            if pronoun.pos_ == 'DET': 
                replacement = pronoun_replacement.equivalent_pronoun('POSS_WK') 
            else: 
                replacement = pronoun_replacement.equivalent_pronoun(pronoun_case(pronoun.text.lower()))
            
            if(pronoun.text == pronoun.text.capitalize()):
                replacement = replacement.capitalize()
            
            if(pronoun_replacement.gramatically_plural and pronoun.dep_ == 'nsubj' and pronoun.head.tag_ == 'VBZ'):
                present_tense_heads.append(pronoun.head)
            #special case for DET 
            #print(mention[0].text, 'dep', mention[0].dep_)
            #print(mention[0].text, 'tag', mention[0].tag_, spacy.explain(mention[0].tag_))
            
            #print('pos', mention[0].pos_)
            #print('head', mention[0].head.i)
            #print(mention[0].head.text, 'tag', mention[0].head.tag_, spacy.explain(mention[0].head.tag_))
            # if replacement pronoun is they/them AND pronoun is the subject, add token to an array 
            if pronoun.i > buffer_start:  # If we've skxipped over some tokens, let's add those in (with trailing whitespace if available)
                text += doc[buffer_start: pronoun.i].text + doc[pronoun.i- 1].whitespace_
            text += replacement + doc[pronoun.i].whitespace_  # Replace token, with trailing whitespace if available
            buffer_start = pronoun.i + 1

    text += doc[buffer_start:].text
    if(len(present_tense_heads) > 0): 
        text = pluralize_present_heads(text, present_tense_heads)
    return text

def pluralize_present_heads(orig_text, heads):
    doc = nlp(orig_text)
    text = ''
    buffer_start = 0

    print(heads)
    for head in heads:
        if head.i > buffer_start:
            text += doc[buffer_start:head.i].text + doc[head.i - 1].whitespace_ 

        if head.text == 'is':
             text += 'are' + doc[head.i].whitespace_
        elif head.text == "'s":
            text += "'re" + doc[head.i].whitespace_
        else:
            text += head.lemma_ + doc[head.i].whitespace_

        buffer_start = head.i + 1 

    text += doc[buffer_start:].text

    return text  

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/process', methods = ["POST"])
def process():
    results =[]
    num_of_results = 0
    # if request.method == 'POST':
    rawtext = request.form['rawtext']
    name = request.form['name']
    pronoun_option = request.form['pronoun_replacement']
    pronoun_replacements = {
        'she' : Pronoun('she', 'her', 'her', 'hers', 'herself'),
        'he' : Pronoun('he', 'him', 'his', 'his', 'himself'),
        'they' : Pronoun('they', 'them', 'their', 'theirs', 'themself', True)
    }

    output = replace_pronouns(rawtext, name, pronoun_replacements[pronoun_option])

    return render_template("index.html", translated = output)


if __name__ == '__main__':
	app.run(debug=True)