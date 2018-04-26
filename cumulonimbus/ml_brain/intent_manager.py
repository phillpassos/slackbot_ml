import json
import os
import time
from shutil import copyfile

BASE_PATH = os.path.realpath(__package__)
INTENTS_PATH = os.path.join(os.path.realpath(__package__), 'intents.json')
intents = {}
modified = {'modified': False}

with open(INTENTS_PATH, mode='r+', buffering=-1, encoding="UTF-8") as json_data:
    intents = json.load(json_data)
    json_data.close()

def backup():
    strnow = str(int(time.time()))
    dest = BASE_PATH + r"\backups\intents-backup-"+strnow+".json"
    copyfile(INTENTS_PATH, dest)
    return {'path': dest}

def save():
    _ = backup()
    filestr = json.dumps(intents, ensure_ascii=False)
    filestr = filestr.encode("utf-8").decode("utf-8")
    with open(INTENTS_PATH, mode='w', buffering=-1, encoding="UTF-8") as json_data:
        json_data.write(filestr)
    json_data.close()
    return {"ok":"ok"}




def set_context(tag, resp):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            intent["context_set"] = resp or ""
            modified['modified'] = True
            return intent['context_set']
                    
    return {"error":"erro ao setar context"}

"""
 -----ADD
"""
def add_response(tag, resp):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            intent['responses'].append(resp)
            modified['modified'] = True
            return intent['responses']
                    
    return {"error":"erro ao add pattern"}

def add_pattern(tag, patt):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            intent['patterns'].append(patt)
            modified['modified'] = True
            return intent['patterns']
                    
    return {"error":"erro ao add pattern"}

def add_tag(tag):
    intents['intents'].append({
        "tag": tag,
        "patterns": [],
        "responses": [],
        "context_set": ""
    })
    modified['modified'] = True
    return list_tags()




"""
 -----REMOVES
"""
def rem_response(tag, resp):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            for index, response in enumerate(intent['responses']):
                if response == resp:
                    intent['responses'].pop(index)
                    modified['modified'] = True
                    return intent['responses']
                    
    return {"error":"erro ao remover response"}

def rem_pattern(tag, patt):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            for index, pattern in enumerate(intent['patterns']):
                if pattern == patt:
                    intent['patterns'].pop(index)
                    modified['modified'] = True
                    return intent['patterns']
                    
    return {"error":"erro ao remover pattern"}

def rem_tag(tag):
    for index, intent in enumerate(intents['intents']):
        if intent['tag'] == tag:
            intent['responses'].pop(index)
            modified['modified'] = True
            return list_tags()
    return {"error":"erro ao remover tag"}


"""
 -----GETS
"""
def get_responses(tag):
    ret = []
    for intent in intents['intents']:
        if intent['tag'] == tag:
            ret = intent['responses']
    return ret

def get_patterns(tag):
    ret = []
    for intent in intents['intents']:
        if intent['tag'] == tag:
            ret = intent['patterns']
    return ret

def list_tags():
    ret = []
    for intent in intents['intents']:
        ret.append(intent['tag'])
    return ret

def handle_request(msg):
    ret = {}
    commands = msg.split(" ")
    if commands[0] == "list":
        if commands[1] == 'tags':# list tags
            ret = list_tags()
        elif commands[1] == 'patterns': # list patterns <tag>
            ret = get_patterns(commands[2])
        elif commands[1] == 'responses':
            ret = get_responses(commands[2]) # list responses <tag>

    elif commands[0] == "remove":
        if commands[1] == 'tag':# remove tag
            ret = rem_tag(commands[2])
        elif commands[1] == 'pattern': # remove pattern <tag> <pattern>
            ret = rem_pattern(commands[2], " ".join(commands[3:]))
        elif commands[1] == 'response':
            ret = rem_response(commands[2], " ".join(commands[3:])) # remove response <tag> <response>

    elif commands[0] == "add":
        if commands[1] == 'tag':# add tag
            ret = add_tag(commands[2])
        elif commands[1] == 'pattern': # add pattern <tag> <pattern>
            ret = add_pattern(commands[2], " ".join(commands[3:]))
        elif commands[1] == 'response':
            ret = add_response(commands[2], " ".join(commands[3:])) # add responses <tag> <response>

    elif commands[0] == "backup":
        ret = backup()

    elif commands[0] == "save":
        ret = save()
        modified['modified'] = False

    elif commands[0] == "status":
        ret = {"status": modified['modified']}
    
    elif commands[0] == "help" or commands[0] == "ajuda" or commands[0] == "comandos":
        ret = ["list tags", "list patterns <tag>", "list responses <tag>", "remove tag", "remove pattern <tag> <pattern>", "remove response <tag> <response>", "add tag"," add pattern <tag> <pattern>", "add responses <tag> <response>"]
    else:
        ret = intents

    return json.dumps(ret)

from flask import Flask
from flask import request
import json
app = Flask(__name__, static_url_path='/static')

# criacao da rota principal (no nosso caso é a unica)
@app.route("/", methods=['POST'])
def respond():
    msg = json.loads(request.data.decode("UTF-8"))
    # respondo com o resultado do bot
    return handle_request(msg['msg'])
    #return json.dumps(msg), 200, {'Content-Type': 'application/json; charset=utf-8'};

# rodo o servidor
app.run(host="pat1498", port=9191)
