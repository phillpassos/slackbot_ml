import time
from slackclient import SlackClient

# constants
BOT_ID = 'id'
SLACK_BOT_TOKEN = 'token'


AT_BOT = "<@" + BOT_ID + ">"
COMMAND = "faz"

slack_client = SlackClient(SLACK_BOT_TOKEN)


def handle_command(command, channel):
    response = "Não tenho ideia do que é isso. Tenta começar com o comando *" + COMMAND + \
               "*."
    if command.startswith(COMMAND):
        response = "Claro...Mas agora não. Em breve quando eu tiver essa funcionalidade eu faço!"
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        print(output_list)
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 
    if slack_client.rtm_connect():
        print("Bot conectado!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("A conexão falhou. Verificar id do bot ou chave de aut.")
