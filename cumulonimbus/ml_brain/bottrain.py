import nltk

import numpy as np
import tflearn
import tensorflow as tf
import random
import json
import os
import unidecode

class MonitorCallback(tflearn.callbacks.Callback):

    minimum_loss = 0.1
    model = None
    max_acc_val = 0
    saved_step = 0

    def __init__(self, api, model=None):
        self.api = api
        if (model):
            self.model = model

    def on_train_end(self, training_state):
        os.system('cls')
        print('\n===========================================')
        print('step: ' + str(training_state.step))
        print('global loss: ' + str(training_state.global_loss))
        print('loss: ' + str(training_state.val_loss))
        print('acc: ' + str(training_state.val_acc))
        print('best acc: ' + str(training_state.best_accuracy))
        print('global acc: ' + str(training_state.global_acc))
        print('step time: ' + str(training_state.step_time_total))
        print('|')
        print('loss val: ' + str(training_state.loss_value))
        print('minimum loss val: ' + str(self.minimum_loss))
        print('acc val: ' + str(training_state.acc_value))
        print('max acc val: ' + str(self.max_acc_val))
        print('last saved step: ' + str(self.saved_step))
        print('|')
        print('===========================================\n')

    def on_batch_end(self, training_state, snap):
        if (training_state.step % 100 == 0):
            self.on_train_end(training_state)
            if (self.model and training_state.loss_value < self.minimum_loss and training_state.step > 15000):
                self.minimum_loss = training_state.loss_value
                self.max_acc_val = training_state.acc_value
                self.saved_step = training_state.step
                self.model.save('brain_models_data/model.tflearn')
                print("*---Model saved.---*")

class BotTrain:
    INTENTS_PATH = os.path.join(os.path.dirname(__file__), 'intents.json')

    @staticmethod
    def get_model(size_x, size_y):
        # construcao da rede neural
        net = tflearn.input_data(shape=[None, size_x])
        net = tflearn.fully_connected(net, size_x*2)
        net = tflearn.fully_connected(net, size_x*3)
        net = tflearn.fully_connected(net, size_x*2)
        net = tflearn.fully_connected(net, size_y, activation='softmax')
        net = tflearn.regression(net)
        model = tflearn.DNN(net, tensorboard_dir='brain_models_data/tflearn_logs')

        return model


    def train(self):
        with open(self.INTENTS_PATH, mode='r', buffering=-1, encoding="UTF-8") as json_data:
            intents = json.load(json_data)

        words = []
        classes = []
        documents = []
        ignore_words = ['?', '!']
        # loop das sentencas do arquivo e padroes
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                # gerando os tokens dos padroes
                w = nltk.word_tokenize(pattern)
                # adicionando a nossa lista de palavras
                words.extend(w)
                # adicionando os docs
                documents.append((w, intent['tag']))
                # add pra lista de classes
                if intent['tag'] not in classes:
                    classes.append(intent['tag'])

        # filtrando as palavras
        words = [unidecode.unidecode(w.lower()) for w in words if w not in ignore_words and len(w) > 2]
        words = sorted(list(set(words)))

        # remocao de duplicatas
        classes = sorted(list(set(classes)))

        print (len(documents), "documents")
        print (len(classes), "classes", classes)
        print (len(words), "unique words", words)






        # criando dados de treinamento
        training = []
        # criando array vazio pra entrada
        output_empty = [0] * len(classes)

        # conjunto de trainamento, pack de palavras pra cada sentenca
        for doc in documents:
            # inicializa o pack de palavras
            bag = []
            # lista de palavras tokenizadas para os padroes
            pattern_words = doc[0]
            # filtrando palavras
            pattern_words = [word.lower() for word in pattern_words]
            # array do pack de palavras
            for w in words:
                bag.append(1) if w in pattern_words else bag.append(0)

            # 0 para cada tag e '1' para a tag atual
            output_row = list(output_empty)
            output_row[classes.index(doc[1])] = 1

            training.append([bag, output_row])

        # misturando os recursos e passando para o np.array
        random.shuffle(training)
        training = np.array(training)

        # criacao da lista de trainemanto e testes
        train_x = list(training[:,0])
        train_y = list(training[:,1])

        # reset dos dados do grafico
        tf.reset_default_graph()

        # modelo e config do tensorboard
        model = BotTrain.get_model(len(train_x[0]), len(train_y[0]))
        # iniciar treinamento (GD alg)
        monitorCallback = MonitorCallback(None, model)
    #                                                   int(len(train_x[0])/10)
        # print("Treinando em BEST BACTH TRAIN MODE")
        print("Treinando em FULL TRAIN MODE")
        model.fit(train_x, train_y, n_epoch=10000, batch_size=1, show_metric=False, snapshot_epoch=False, callbacks=monitorCallback)
        #model.save('brain_models_data/model.tflearn')



        # salvar estruturas de dados
        import pickle
        pickle.dump( {'words':words, 'classes':classes, 'train_x':train_x, 'train_y':train_y}, open( "brain_models_data/training_data", "wb" ) )