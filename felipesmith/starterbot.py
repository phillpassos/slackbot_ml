"""
# @TODO'S!! 
Fazer calculos simples
Adicionar 
"""
import time
import datetime
from slackclient import SlackClient
from threading import Thread
import random

import math_eval
import constants
import api_keys

# constants
BOT_ID = api_keys.BOT_ID
SLACK_BOT_TOKEN = api_keys.SLACK_BOT_TOKEN
CHANNEL_GERAL = api_keys.CHANNEL_GERAL
#CHANNEL_GERAL = 'D94TSUU0Z' #canal de teste
READ_WEBSOCKET_DELAY = 1 
RANDOM_MESSAGE_DELAY_MINUTES = 180
RETRY_DELAY = 20

UM_MINUTO_EM_SEGUNDOS = 60


AT_BOT = "<@" + BOT_ID + ">"
COMMAND = ""

slack_client = SlackClient(SLACK_BOT_TOKEN)

def msg_responder():
    loop_error = 0
    while True:
        try:
            rtm_message = slack_client.rtm_read()
            print(rtm_message)
            command, channel = parse_slack_output(rtm_message)
            if command and channel:
                send_mension_message(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
            loop_error = 0
        except Exception as e:
            print("Deu Erro ao responder... Reiniciando. %s" % str(e))
            if loop_error > 10:
                print("Muitos erros em msg_responder, saindo")
                return
            time.sleep(RETRY_DELAY)
            loop_error = loop_error +1

def random_message_sender():
    loop_error = 0
    while True:
        #delay = int(random.random() * 10 * 6)
        delay = int(random.random() * 10 * 6 * RANDOM_MESSAGE_DELAY_MINUTES)
        try:
            send_message("send_mension_message", CHANNEL_GERAL)
            loop_error = 0
        except Exception as e:
            print("Deu Erro na mensagem aleatoria. Reiniciando. %s" % str(e))
            if loop_error > 10:
                print("Muitos erros em random_message_sender, saindo")
                return
            time.sleep(RETRY_DELAY)
            loop_error = loop_error +1
        print("proxima mensagem: %s" % (str(delay)))
        time.sleep(delay)

def mensagem_almoco():
    loop_error = 0
    while True:
        try:
            now = datetime.datetime.now()
            print("Hora atual: %s:%s" % (now.hour, now.minute))
            if now.hour == 13 and now.minute == 0:
                slack_client.api_call("chat.postMessage", channel=CHANNEL_GERAL, text="<!everyone> | partiu almoco! |", as_user=True)
                print("@everyone | partiu almoco! |")
                return
            else:
                time.sleep(UM_MINUTO_EM_SEGUNDOS)
            loop_error = 0
        except Exception as e:
            print("Deu mensagem almoco... Reiniciando. %s" % str(e))
            if loop_error > 10:
                print("Muitos erros em mensagem_almoco, saindo")
                return
            time.sleep(RETRY_DELAY)
            loop_error = loop_error +1
        
def send_random_message_to_random_user():
    loop_error = 0
    slack_users = get_users()
    last_user = ""
    while True:
        retryes = 0
        try:
            if (len(slack_users) > 0):
                i = 0
                user = random.choice(slack_users)
                while ((user == last_user) or (i < 2 * len(slack_users))):
                    user = random.choice(slack_users)
                    i = i + 1

                last_user = user
                api_call = slack_client.api_call("users.getPresence", user=user["id"]) #U85DMPMUG eu
                if api_call.get('ok') and api_call.get('presence') == 'active':
                    retryes = 0
                    send_message("random", user["id"])
                    delay = int(random.random() * UM_MINUTO_EM_SEGUNDOS * (RANDOM_MESSAGE_DELAY_MINUTES / 2))
                    print("Enviada mensagem para: %s. Proxima mensagem em %s"%(user["user"], str(delay)))
                    time.sleep(delay)#por o delay
                else:
                    time.sleep(UM_MINUTO_EM_SEGUNDOS / 6)
                    retryes = retryes + 1
            else:
                slack_users = get_users()
                time.sleep(UM_MINUTO_EM_SEGUNDOS * RETRY_DELAY)
            loop_error = 0
        except Exception as e:
            print("Deu Erro ao enviar mensagem aleatoria para %s... Reiniciando. %s" % user["user"], (str(e)))
            if loop_error > 10:
                print("Muitos erros em send_random_message_to_random_user, saindo")
                return
            time.sleep(RETRY_DELAY)
            loop_error = loop_error +1


def send_message(command, channel):
    #if (command == 'random')
    response = random.choice(constants.BOT_MESSAGES)
    print("Mensagem: %s  || no canal: %s\n"%(response, str(channel)))
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

def send_mension_message(command, channel):
	if math_eval.has_expression(command):
		response = str(math_eval.exec_expression(command))
		temp = response.split(".")
		if (len(temp) > 1 and len(temp[1]) == 1 and temp[1] == '0'):
			response = temp[0]
	else:
		response = random.choice(constants.BOT_MESSAGES_RESPONSE)
		
	if not len(response) > 0: #@todo ajustar isso aqui
		response = random.choice(constants.BOT_MESSAGES_RESPONSE)
		
	print("Resposta: %s  || no canal: %s\n"%(response, str(channel)))
	slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        # print(output_list)
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
			
            if output and 'text' in output and 'felipe' in output['text'].lower():
                return output['text'].lower(), \
                       output['channel']
			
    return None, None

def get_users():
    print("Recuperando usuarios.")
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        slack_users = []
        for user in users:
            if (not user.get('is_bot') and user['name'] != 'slackbot'):
                slack_users.append({"user": user['name'], "id": user.get('id')})
        return slack_users


def start_bot():
    if slack_client.rtm_connect():
        print("Bot conectado!")
        threadpool = {
            "responder": Thread(target=msg_responder), 
            "ramdom": Thread(target=random_message_sender),
            "almoco": Thread(target=mensagem_almoco),
            "usuario_aleatorio": Thread(target=send_random_message_to_random_user)
        }
        #while True:
        try:
            for thread in threadpool:
                threadpool[thread].start()

            for thread in threadpool:
                threadpool[thread].join()
        except Exception as e:
            print("Deu Erro ao criar threads... Reiniciando. %s" % str(e))
    else:
        print("A conexão falhou. Verificar id do bot ou chave de aut.")
	
if __name__ == "__main__":
    try:
        start_bot()
    except Exception as e:
        print("Deu Erro... Reiniciando. %s" % str(e))
    #start_bot()