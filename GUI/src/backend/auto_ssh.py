from PIL import Image
import paramiko
import json


class SSH:

    """ This class will automatically ssh into the host cluster. """

    def __init__(self, host=None):
        if host is None:
            try:
                json_str = open('src/backend/db.json').read() # TODO: Sibling files not recognizing each other when called from another file path.
                db_dict = json.loads(json_str)
                host = db_dict['ip']
            except FileNotFoundError as e:
                print(e.__traceback__, "'db.json' not found! Please run the installation first before running GUI.")
                raise e
        
        # The information that will allow for ssh
        self.host = host
        self.user = ""
        self.pwrd = ""
        self.ssh = None

    def command(self, command):
        # Check if there is a connection
        assert self.ssh is not None, "Connect before using a command"

        # Send the command
        stdin, stdout, stderr = self.ssh.exec_command(command)

        return stdout

    def connect(self, username, password):
        # Set the credentials
        self.user = username
        self.pwrd = password

        # Connect to ssh and set out ssh object
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, password=self.pwrd)
        self.ssh = ssh

    def download(self, remote_path, local_path):
        ftp_client = self.ssh.open_sftp()
        ftp_client.get(remote_path, local_path)
        ftp_client.close()

    def read(self, remote_path):
        return self.ssh.open_sftp().file(remote_path)

    def get_image(self, remote_path, transparent=False):
        im = Image.open(self.read(remote_path))
        if transparent:
            im = im.convert("RGBA")
            datas = im.getdata()
            new_data = []
            for item in datas:
                if item[0] == 255 and item[1] == 255 and item[2] == 255:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)

            im.putdata(new_data)
        return im

    def __repr__(self):
        message = self.user + "\n"
        message += self.host + "\n"