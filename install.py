import sys
import zipfile
import requests
import os
import shutil
import subprocess


ROOT_DIR = '/'

def run_command(command):
    try:
        output = subprocess.check_output(command, shell=True)
        return True, output.decode('utf-8')
    except Exception as e:
        return False, f"An error occurred: {str(e)}"
    
def restore_mongo_db(domain):
    print("Restoring MongoDB...")
    run_command(f"mongorestore --gzip --archive={ROOT_DIR}/web/{domain}/mongodump/affiliatecms.agz --nsFrom='affiliatecms.*' --nsTo='{domain}.*'")
    print("Done.")

def restart_nginx():
    print("Restarting Nginx...")
    run_command("service nginx restart")
    print("Done.")

def create_nginx_config(domain, port):
    print("Creating Nginx config...")
    nginx_config = f"""server {{
    listen 80;
    server_name www.{domain};
    location / {{
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;
        proxy_pass http://localhost:{port};
        proxy_read_timeout  90;     
    }}
}}"""
    with open(ROOT_DIR + '/etc/nginx/conf.d/'+domain+'.conf', 'w') as file:
        file.write(nginx_config)
    print("Done.")

def create_version_file(domain, version):
    os.makedirs(os.path.dirname(ROOT_DIR + 'web/'+domain+'/.version'), exist_ok=True)
    with open(ROOT_DIR + 'web/'+domain+'/.version', 'w') as file:
        file.write(version)

def move_folder(source_dir, destination_dir):
    try:
        shutil.move(source_dir, destination_dir)
        return True, f"Folder '{source_dir}' moved to '{destination_dir}'."
    except Exception as e:
        return False, f"An error occurred: {str(e)}"

def change_ecosystem_file(domain, port, cron_port):
    with open(ROOT_DIR + 'web/'+domain+'/ecosystem.config.js', 'r') as file :
        filedata = file.read()
    filedata = filedata.replace('affiliatecms-cronjobs', domain+'-cronjobs')
    filedata = filedata.replace('affiliatecms', domain)
    filedata = filedata.replace('8000', port)
    filedata = filedata.replace('8100', cron_port)
    with open(ROOT_DIR + 'web/'+domain+'/ecosystem.config.js', 'w') as file:
        file.write(filedata)

def download_file_from_url(url, destination):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            with open(destination, "wb") as f:
                f.write(response.content)
            return True, f"File '{destination}' downloaded successfully."
        else:
            return False, "Failed to download the file."
    except Exception as e:
        return False, f"An error occurred: {str(e)}"

def download_source_code(domain):
    print("Downloading source code...")
    # download_file = requests.get('https://app.affiliatecms.com/api/hooks/getupdatelink?source=curl').content.decode('utf-8')
    download_file = "https://api.puppyprinty.com/media/v2.57.zip"
    download_file_from_url(download_file, ROOT_DIR+'tmp/'+domain+'/source.zip')
    download_file_tag = 'v2-'+download_file.split('/')[-1].replace('.zip', '')
    print("Unzipping source code...")
    with zipfile.ZipFile(ROOT_DIR+'tmp/'+domain+'/source.zip', 'r') as zip_ref: 
        zip_ref.extractall(ROOT_DIR + 'tmp/'+domain)
    move_folder(ROOT_DIR+'tmp/'+domain+'/'+download_file_tag, ROOT_DIR+'web/'+domain)
    print("Done.")
    return download_file_tag
    
def start_server(domain):
    print("Starting server...")
    run_command(f"cd {ROOT_DIR}/web/{domain}/ && pm2 start")
    print("Done.")

# Check the number of arguments provided
if len(sys.argv) != 4:
    print("Usage: python script.py --domain_name=<domain> --port=<port> --cron_port=<cron_port>")
    sys.exit(1)

# Initialize variables to store domain_name and port
domain = None
port = None
cron_port = None

# Iterate through command-line arguments
for arg in sys.argv[1:]:
    if arg.startswith("--domain="):
        domain = arg.split("=")[1]
    elif arg.startswith("--port="):
        port = arg.split("=")[1]
    elif arg.startswith("--cron_port="):
        cron_port = arg.split("=")[1]

# Check if domain_name and port were provided
if domain:
    print(f"Domain name: {domain}")
else:
    print("Domain name not provided.")
if port:
    print(f"Port: {port}")
else:
    print("Port not provided.")

if cron_port:
    print(f"Cron Port: {cron_port}")
else:
    print("Cron port not provided.")
# Download source code
download_file_tag = download_source_code(domain)
# Change ecosystem file

domainPath = domain.split('.')[0]
# Restore MongoDB
move_folder(ROOT_DIR+'web/'+domain, ROOT_DIR+'web/'+domainPath)
restore_mongo_db(domainPath)
change_ecosystem_file(domainPath, port, cron_port)
run_command(f"cd {ROOT_DIR}/web/{domainPath}/ && yarn install")
create_version_file(domainPath, download_file_tag)
start_server(domainPath)

# Create Nginx config
create_nginx_config(domain, port)
# Restart Nginx
restart_nginx()


