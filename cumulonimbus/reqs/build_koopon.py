import subprocess as sp
import os, stat
import re
import time

class BuildKoopon:

    LOGS_PATH = r"C:\_slackbot__\cumulonimbus\logs"
    LOG_TAG = "file.upload||"
    PATH_KOOPON = r"C:\_slackbot__\cumulonimbus\_Koopon_repo"
    message_cb = {}
    job = {}

    def inform(self, msg):
        self.message_cb(msg, self.job["channel"], self.job["user"], ">")

    def build_and_deploy(self, job, message_cb):
        job["time_to_end"] = 0
        time_path = self.LOGS_PATH + r"\time.txt"
        total_time = ""
        if os.path.exists(time_path):
            fh = open(time_path, "r+")
            total_time = fh.read()
        else:
            fh = open(time_path, "w")

        rt = 0
        self.message_cb = message_cb
        self.job = job

        if (len(total_time) > 0):
            self.inform("Tempo estimado de execução: %s segundos"%(total_time))
            self.job["time_to_end"] = total_time

        # SVN
        self.inform("Revertendo modificações locais...")
        rt = self.revert_modifications()
        if rt: 
            self.inform("Erro ao reverter modificações com o SVN")
            return rt

        self.inform("Sincronizando projeto com o SVN...")
        rt = self.update_repo()
        if rt: 
            self.inform("Erro ao sincronizar com o SVN")
            return rt

        # PERM
        self.inform("Removendo propriedade de readonly dos arquivos")
        rt = self.remove_readonly() #o retorno do attrib eh 1 para sucesso. deixxamos sem isso por enquanto
        # if rt: 
        #     self.inform("Erro ao remover a propriedade de readonly")
        #     return rt

        # NODE
        self.inform("Atualizando o node_modules")
        rt = self.update_node_modules()
        if rt: 
            self.inform("Erro ao atualizar o node_modules")
            return rt
            
        # BOWER - removido pois o bower ja vem no projeto
        # self.inform("Atualizando o bower_modules")
        # rt = self.update_bower_modules()
        # if rt: 
        #     self.inform("Erro ao atualizar o bower_modules")
        #     return rt

        # BUILD
        self.inform("Gerando build do projeto")
        rt = self.build_project()
        if rt: 
            self.inform("Erro ao gerar build")
            return rt

        # DEPLOY
        self.inform("Efetuando deploy")
        self.inform("Limpando pasta remota...")
        rt = self.clear_ftp()
        if rt: 
            self.inform("Erro ao excluir pasta remota")
            return rt

        self.inform("Enviando arquivos")
        rt = self.fill_ftp()
        if rt: 
            self.inform("Erro ao excluir enviar arquivos ao ftp")
            return rt
        
        self.inform("Arquivos enviados.")

        now = time.time()
        secs = ((self.job["resolve_at"] - now)*-1)
        try:
            if (len(total_time) > 0):
                secs = (secs + float(total_time)) / 2
                fh.seek(0)
                fh.truncate(0)
                fh.write(str(secs))
            else:
                fh.write(str(secs))
        except Exception as e:
            print(str(e))

        fh.close()

        return rt

    def revert_modifications(self):
        try:
            return self.do("svn revert *.*")
        except:
            return 1

    def remove_readonly(self):
        try:
            return self.do("attrib -R /S")
        except:
            return 1

    def fill_ftp(self):
        try:
            return self.do("gulp deploy__private")
        except:
            return 1

    def clear_ftp(self):
        try:
            return self.do("gulp clear-ftp")
        except:
            return 1

    def update_repo(self):
        try:
            return self.do("svn update")
        except:
            return 1

    def update_node_modules(self):
        try:
            return self.do("npm i")
        except:
            return 1
    
    def update_bower_modules(self):
        try:
            return self.do("bower i")
        except:
            return 1

    def build_project(self):
        try:
            return self.do("npm run build")
        except:
            return 1

    def deploy_project(self):
        try:
            return self.do("npm run deploy")
        except:
            return 1

    def do(self, command):
        current_dir = os.getcwd()
        os.chdir(self.PATH_KOOPON)

        child = sp.Popen(command, stdout=sp.PIPE, shell=True)
        streamdata = child.communicate()[0]
        rc = child.returncode # se rc > 0, ocorreu um erro

        filename = "log-%s.txt"%(re.sub('[^a-zA-Z ]+', '', command))
        fullpath = "%s\%s"%(self.LOGS_PATH, filename)

        os.chdir(current_dir)
        file = open(fullpath,"wb")
        file.write(streamdata)
        file.close()

        if (rc):
            self.inform(self.LOG_TAG+filename+"||"+fullpath)

        return rc