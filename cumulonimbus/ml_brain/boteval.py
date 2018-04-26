import pickle
import nltk
import json
from .bottrain import BotTrain
import numpy as np
import random
import os

class BotEval:

    words = {}
    classes = {}
    train_x = {}
    train_y = {}
    intents = {}
    model = {}

    ML_PATH = "ml_brain/brain_models_data/"
    INTENTS_PATH = os.path.join(os.path.dirname(__file__), 'intents.json')

    def __init__(self):
        data = pickle.load( open(self.ML_PATH + "training_data", "rb" ) )
        self.words = data['words']
        self.classes = data['classes']
        self.train_x = data['train_x']
        self.train_y = data['train_y']

        # importar arquivos de intent do bot
        with open(self.INTENTS_PATH, mode='r', buffering=-1, encoding="UTF-8") as json_data:
            self.intents = json.load(json_data)

        self.model = BotTrain.get_model(len(self.train_x[0]), len(self.train_y[0]))
        # carregar modelo salvo
        self.model.load(self.ML_PATH + 'model.tflearn')


    def clean_up_sentence(self, sentence):
        # gerando token dos padroes
        sentence_words = nltk.word_tokenize(sentence)
        # normalizando palavras
        sentence_words = [word.lower() for word in sentence_words]
        return sentence_words

    # retornando um array do pack de palavras: 0 ou 1 pra cada palavra no pack que existe na sentenca
    def bow(self, sentence, words, show_details=False):
        # tokens dos padroes
        sentence_words = self.clean_up_sentence(sentence)
        # pack de palavras
        bag = [0]*len(words)  
        for s in sentence_words:
            for i,w in enumerate(words):
                if w == s: 
                    bag[i] = 1
                    if show_details:
                        print ("found in bag: %s" % w)

        return(np.array(bag))







    # processador de respostas
    # estrutura para carregar o contexto
    context = {}
    ERROR_THRESHOLD = 0.3

    def classify(self, sentence):
        # gerando probabilidades do modelo
        results = self.model.predict([self.bow(sentence, self.words)])[0]
        # preencher predicoes abaixo do threshold
        results = [[i,r] for i,r in enumerate(results) if r > self.ERROR_THRESHOLD]
        # ordenar por probabilidade
        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append((self.classes[r[0]], r[1]))
        # retornar a tupla do intent e probabilidade
        return return_list

    def response(self, sentence, userID='123', show_details=False):
        results = self.classify(sentence)
        # se temos classificacao, entao encontramos o pack de intencoes
        if results:
            print(results)
            # enqunto tiver macthes, procuro os dados
            while results:
                for i in self.intents['intents']:
                    # encontro a tag com o primeiro resultado
                    if i['tag'] == results[0][0]:
                        # seta o contexto se necessario
                        if 'context_set' in i:
                            if show_details: print ('context:', i['context_set'])
                            self.context[userID] = i['context_set']

                        # checa se o contexto se aplica a conversacao
                        if not 'context_filter' in i or \
                            (userID in self.context and 'context_filter' in i and i['context_filter'] == self.context[userID]):
                            if show_details: print ('tag:', i['tag'])
                            # responsta aleatoria para o intent
                            resp = random.choice(i['responses'])
                            return resp

                results.pop(0)