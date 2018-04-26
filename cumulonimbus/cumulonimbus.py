import time
import datetime
import io
from slackclient import SlackClient
from threading import Thread
from threading import Lock
import os
import unidecode

from reqs.build_koopon import BuildKoopon
from ml_brain.boteval import BotEval
import math_eval
import commands
import api_keys
"""
@todo listar e fornecer logs disponiveis

"""

# constants
BOT_ID = api_keys.BOT_ID
SLACK_BOT_TOKEN = api_keys.SLACK_BOT_TOKEN
CHANNEL_GERAL = api_keys.CHANNEL_GERAL
CHANNEL_FRONTEND = api_keys.CHANNEL_FRONTEND
ID_PH = api_keys.ID_PH
#CHANNEL_FRONTEND = api_keys.CHANNEL_BOT


#CHANNEL_GERAL = 'D94TSUU0Z' #canal de teste
READ_WEBSOCKET_DELAY = 1 
RETRY_DELAY = 20

DELAY_DEPLOY_MINUTOS = 0.5# 0.1

UM_MINUTO_EM_SEGUNDOS = 60

AT_BOT = "<@" + BOT_ID + ">"
COMMAND = ""
LOGS_PATH = r"C:\_slackbot__\cumulonimbus\logs"

slack_client = SlackClient(SLACK_BOT_TOKEN)
lock = Lock()

request_model = {"msg": "", "channel": "", "user":"", "mension":""}
response_queue = []
request_queue = []

scheduled_job = []
scheduled_job_model = {"command": "", "channel": "", "user":"", "state": 0, "resolve_at": 0}

def queue_scheduled_job(command, channel, user):
    request = scheduled_job_model.copy()
    request["command"] = command
    request["channel"] = channel
    request["user"] = user
    request["resolve_at"] = time.time() + (UM_MINUTO_EM_SEGUNDOS * DELAY_DEPLOY_MINUTOS)

    lock.acquire()
    scheduled_job.append(request)
    lock.release()

def queue_request_msg(msg, channel, user):
    request = request_model.copy()
    request["msg"] = msg
    request["channel"] = channel
    request["user"] = user

    lock.acquire()
    request_queue.append(request)
    lock.release()

def queue_response_msg(msg, channel, user, mension=None):
    request = request_model.copy()
    request["msg"] = msg
    request["channel"] = channel
    request["user"] = user
    if (not mension):
        request["mension"] = "<@%s>"%(user)
    else:
        request["mension"] = mension

    lock.acquire()
    response_queue.append(request)
    lock.release()

def dequeue_response():
    lock.acquire()
    if len(response_queue) == 0:
        lock.release()
        return None
    resp = response_queue.pop(0)
    lock.release()
    return resp

def dequeue_request():
    lock.acquire()
    if len(request_queue) == 0:
        lock.release()
        return None
    resp = request_queue.pop(0)
    lock.release()
    return resp

def respond():
    while True:
        resp = dequeue_response()
        if resp:
            try:
                path = resp['msg'].split("||")# formato: file.upload||arquivo.txt||caminho\do\arquivo.txt
                if (len(path) > 1 and path[0] == 'file.upload'):
                    try:
                        arq = open(path[2])
                        data = arq.read()
                        arq.close()
                        slack_client.api_call("files.upload", filename=path[1], filetype="txt", channels=resp['channel'], content=data, as_user=True)
                    except Exception as e:
                        print("Erro ao enviar arquivo. %s"%(str(e)))
                else:
                    slack_client.api_call("chat.postMessage", channel=resp['channel'], text="%s: %s"%(resp['mension'], resp['msg']), as_user=True)
                    print("Resposta: %s  || no canal: %s || para: %s\n"%(resp['msg'], resp['channel'], resp['user']))
            except Exception as e:
                print("Deu Erro ao enviar mensagem pela api. %s" % str(e))

        time.sleep(READ_WEBSOCKET_DELAY)

def resolve():
    ml = BotEval()
    while True:
        response = ""
        request = dequeue_request()
        if (request):
            msg = request["msg"].lower()

            command = msg.split(" ")
            print(command)
            if (len(command[0]) > 0):
                # math
                if math_eval.has_expression(msg):
                    response = str(math_eval.exec_expression(msg))
                    temp = response.split(".")
                    if (len(temp) > 1 and len(temp[1]) == 1 and temp[1] == '0'):
                        response = temp[0]

                # ajuda
                elif command[0] == "ajuda" or command[0] == "help":
                    response = commands.get_formated_commands()
                
                # deploy de sistemas
                elif command[0] == "deploy" and (request["channel"] == CHANNEL_FRONTEND or request["user"] == ID_PH):
                    enqueue = True
                    for req in scheduled_job:
                        if request["msg"] == req["command"]:
                            enqueue = False
                    if enqueue:
                        if len(command)>1 and command[1].lower() == "koopon":
                            queue_scheduled_job(request["msg"], request["channel"], request["user"])
                            response = "Ok. Deploy marcado para ser feito em %s minutos. Origem: trunk"%(str(DELAY_DEPLOY_MINUTOS))
                            queue_response_msg(response, request["channel"], request["user"], "<!channel>")
                            response = None
                        else:
                            response = "Lamento... Não conheço esse projeto."
                    else:
                        response = "Lamento, mas existe um deploy com essas configurações na fila ou executando."

                elif command[0] == "deploy" and request["channel"] != CHANNEL_FRONTEND:
                    response = "Lamento. O pedido de deploy só pode ser feito pelo canal de frontend."

                # listagem da fila
                elif command[0] == "status":
                    lock.acquire()
                    if len(scheduled_job) > 0:
                        response = "Itens na fila:\n\n"
                        for req in scheduled_job:
                            sched = "```Nome: %s\n"%(req["command"])
                            if (req["state"] == 0):
                                sched = sched + "Status: Aguardando\n"
                            else:
                                sched = sched + "Status: Processando\n"

                            now = time.time()
                            secs = req["resolve_at"] - now
                            if (secs > 0):
                                sched = sched + "Execução em: %s segundos\n"%(str(int(secs)))
                            else:
                                sched = sched + "Executando a: %s segundos\n"%(str(int(secs*-1)))

                            response = response + sched + "\n\n```"
                        
                    else:
                        response = "Nada programado no momento."
                    lock.release()

                elif command[0] == "nenhum":
                    response = None

                elif command[0] == "logs":
                    response = ""
                    files = os.listdir(LOGS_PATH)
                    if (len(command) > 1):
                        for file in files:
                            if (file == " ".join(command[1:])):
                                response = r"file.upload||%s||%s\%s"%(file, LOGS_PATH, file)
                                break
                        if (len(response) == 0):
                            response = "Não encontrei o arquivo solicitado."
                    else:
                        response = "Lista de arquivos disponíveis:\n```"
                        for file in files:
                            response = response + file + "\n"
                        response = response + "```"

                elif command[0] == "cancelar" and len(command) > 2:
                    lock.acquire()
                    found = False
                    for idx, req in enumerate(scheduled_job):
                        cmd = req['command'].split(" ")
                        if ((command[1] == cmd[0] and command[2] == cmd[1]) and (req['state'] == 0)):
                            found = True
                            scheduled_job.pop(idx)
                            break
                    lock.release()
                    if (found):
                        response = "Beleza, cancelado."
                    else:
                        response = "Não encontrei esse agendamento na lista de espera. (Lamento mas não posso cancelar os que ja estão executando)"

                elif command[0] == "halt" and request["user"] == ID_PH:
                    time.sleep(10) # travo o resolver por 10 segundos e removo a fila
                    resp = dequeue_request()
                    while(resp):
                        resp = dequeue_request()
                    response = "Desculpe."
                
                elif command[0] == "shutdown" and request["user"] == ID_PH:
                    os.system("shutdown /s /f /t 300")
                    response = "Desligamento do meu host agendado para execução em 5 minutos.";

                elif command[0] == "dontshutdown" and request["user"] == ID_PH:
                    os.system("shutdown /a")
                    response = "Desligamento cancelado.";
                else:
                    if (ml):
                        response = ml.response(unidecode.unidecode(msg))
                    
                    if (not response or len(response) < 2):
                        with open(LOGS_PATH + r"\unknown_messages.txt", "a+", encoding='utf8') as patterns_file:
                            patterns_file.write("\n" + msg)
                            patterns_file.close()

                        if (msg.find('?')!=-1):
                            response = "Não faço ideia do que você quer. Pergunta lá no posto Ipiranga."
                        else:
                            response = "Não faço ideia do que você disse. Tente pedir 'ajuda'."
                        
                if (response):
                    queue_response_msg(response, request["channel"], request["user"])

        time.sleep(READ_WEBSOCKET_DELAY)

def sched_resolver():
    while True:
        if ((len(scheduled_job) > 0) and (scheduled_job[0]["resolve_at"] < time.time())):
            kpn = BuildKoopon()
            scheduled_job[0]["state"] = 1
            channel = scheduled_job[0]["channel"]
            user = scheduled_job[0]["user"]
            retorno = 0

            msg = "Processo de deploy iniciado..."
            queue_response_msg(msg, channel, user, "<!channel>")

            retorno = kpn.build_and_deploy(scheduled_job[0].copy(), queue_response_msg)

            if retorno == 0:
                now = time.time()
                secs = scheduled_job[0]["resolve_at"] - now
                msg = "Deploy concluido com sucesso em: %s segundos"%(str(int(secs*-1)))
                queue_response_msg(msg, channel, user, "<!channel>")
            else:
                msg = "Ocorreu um erro inesperado. Consulte meus logs localmente para maiores detalhes."
                queue_response_msg(msg, channel, user, "<!channel>")

            lock.acquire()
            scheduled_job.pop(0)
            lock.release()

        time.sleep(READ_WEBSOCKET_DELAY)

def listen():
    loop_error = 0
    while True:
        try:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                queue_request_msg(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
            loop_error = 0
        except Exception as e:
            print("Deu Erro ao enfileirar request... Reiniciando. %s" % str(e))
            slack_connect()
            if loop_error > 10:
                print("Muitos erros em listen, saindo")
                return
            time.sleep(RETRY_DELAY)
            loop_error = loop_error +1


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        #print(output_list)
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text'] and 'user' in output:
                msg = output['text'].replace(AT_BOT, "").strip().lower()
                print("Inc msg: %s"%(msg))
                return msg, output['channel'], output['user']
    return None, None, None

def slack_connect():
    try:
       slack_client.rtm_connect() 
    except Exception as e:
        print("Erro ao conectar com o slackapi:  %s" % str(e))

def start_bot():
    if slack_client.rtm_connect():
        print("Bot conectado!")
        threadpool = {
            "listen": Thread(target=listen),
            "resolve": Thread(target=resolve),
            "respond": Thread(target=respond),

            "sched_resolver": Thread(target=sched_resolver)
 
        }
        try:
            for thread in threadpool:
                threadpool[thread].start()

            for thread in threadpool:
                threadpool[thread].join()
        except Exception as e:
            print("Deu Erro ao criar threads... Reiniciando. %s" % str(e))
    else:
        print("A conexao falhou. Verificar id do bot ou chave de aut.")
	
if __name__ == "__main__":
    try:
        start_bot()
    except Exception as e:
        print("Deu Erro... Reiniciando. %s" % str(e))