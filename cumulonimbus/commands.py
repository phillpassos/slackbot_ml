COMMANDS = [
    ["ajuda", r"Lista os comandos existentes"],
    ["help", r"O mesmo que 'ajuda', só que em inglês ¯\_(ツ)_/¯"],
    ["deploy <projeto>", r"Faz o deploy completo do projeto passado"],
    ["cancelar <comando agendado>", r"Cancela o comando da fila de execução"],
    ["status", r"Exibe o que está sendo processado ou está na fila de execução"],
    ["logs", r"Exibe a lista dos últimos logs disponiveis"],
    ["logs <nome do log>", r"Exibe o log pedido"],
    ["(expressão matemática)", r"Tenta resolver a expressão matemática enviada"],
    ["nenhum", r"Realmente não faz nada (assim como infinitos outros comandos que não estão nessa lista)"]
]

def get_formated_commands():
    ret = "\n"
    for command in COMMANDS:
        ret = ret + "`%s`: %s\n" % (command[0], command[1])
    return ret