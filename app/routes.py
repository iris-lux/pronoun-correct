from flask import Flask,render_template,url_for,request
from app import app 
import re
import pandas as pd
import spacy
from spacy.matcher import Matcher 
from spacy import displacy
import en_core_web_sm
import neuralcoref 

nlp = spacy.load('en_core_web_sm')
neuralcoref.add_to_pipe(nlp)

def replace_word(orig_text, replaced, replacement):
    matcher = Matcher(nlp.vocab)
    matcher.add(replaced, None, [{"LOWER": replaced}])
    doc = nlp(orig_text)
    text = ''
    buffer_start = 0
    matches = matcher(doc)
    for _, match_start, _ in matches:
        if match_start > buffer_start:  # If we've skipped over some tokens, let's add those in (with trailing whitespace if available)
            text += doc[buffer_start: match_start].text + doc[match_start - 1].whitespace_
        text += replacement + doc[match_start].whitespace_  # Replace token, with trailing whitespace if available
        buffer_start = match_start + 1
    text += doc[buffer_start:].text
    print(text)
    return text
    
def find_cluster(target_name, doc):
    for cluster in doc._.coref_clusters:
        print(cluster)
        if(cluster.main.text == target_name):
            return cluster 
    return None 

def replace_pronouns(orig_text, name, pronoun_replacement):
    doc = nlp(orig_text)
    text = ''
    buffer_start = 0
    name_cluster = find_cluster(name, doc)
    if name_cluster == None:
        return 'No Match'
    #need to check if mention is pronoun
    for mention in name_cluster.mentions:
        if mention[0].pos_ == 'PRON' or mention[0].pos_ == 'DET':
            if mention.start > buffer_start:  # If we've skipped over some tokens, let's add those in (with trailing whitespace if available)
                text += doc[buffer_start: mention.start].text + doc[mention.start - 1].whitespace_
            text += pronoun_replacement + doc[mention.start].whitespace_  # Replace token, with trailing whitespace if available
            buffer_start = mention.start + 1
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
    pronoun_replacement = request.form['pronoun_replacement']

    output = replace_pronouns(rawtext, name, pronoun_replacement)

    return render_template("index.html", translated = output)


if __name__ == '__main__':
	app.run(debug=True)