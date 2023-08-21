#!/bin/sh
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
CYAN="\e[36m"
ENDCOLOR="\e[0m"

print_text_installing(){
  echo ""
  print_text_red "$1"
}
print_text_done(){
  print_text_green "âœ“ Done!"
}
print_text_yellow(){
  echo -e "${YELLOW}$1${ENDCOLOR}"
}
print_text_cyan(){
  echo -e "${CYAN}$1${ENDCOLOR}"
}
print_text_red(){
  echo -e "${RED}$1${ENDCOLOR}"
}
print_text_green(){
  echo -e "${GREEN}$1${ENDCOLOR}"
}

print_text_hello() {
  echo ""
  print_text_yellow "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
  print_text_yellow "| AffiliateCMS Setup Utilities  |"
  print_text_yellow "| for Ubuntu 20.04 LTS          |"
  print_text_yellow "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
}


domain_name=""
port=""

# Loop through the arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain_name=*)
            domain_name="${1#*=}"
            shift
            ;;
        --port=*)
            port="${1#*=}"
            shift
            ;;
        *)
            # Skip any unrecognized arguments or flags
            shift
            ;;
    esac
done

# 
url=""
tagname=""
foldername=""

clear

download_installer(){
  print_text_installing "â†’ Downloading AffiliateCMS ($tagname)..."
  cd /tmp
  curl -sO $url
  print_text_done
}

##############################
# INSTALL NodeJS
install_nodejs(){
  print_text_installing "â†’ Installing: NodeJS..."
  sudo apt install curl
  curl -sL https://deb.nodesource.com/setup_16.x -o /tmp/nodesource_setup.sh && bash /tmp/nodesource_setup.sh
  sudo apt-get install -y nodejs 
  print_text_done
  
  print_text_installing "â†’ Installing: Yarn, pm2..."
  npm install yarn pm2 -g
  print_text_done
}

##############################
# zip, unzip, parallel, nginx, mongodb, neovim, set line number for vim
install_server_utils(){
  print_text_installing "â†’ Installing: zip, unzip, parallel, nginx, neovim..."
  apt-get update
  sudo apt install python zip unzip parallel nginx neovim python net-tools -y
  apt-get install build-essential
  systemctl start nginx
  systemctl enable nginx
  mkdir -p ~/.config/nvim/
  echo "set number" > ~/.config/nvim/init.vim
  print_text_done
  # mongodb
  print_text_installing "â†’ Installing: Mongodb server..."
  sudo apt-get install gnupg -y
  wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add - 
  echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
  sudo apt-get update -y
  sudo apt-get install -y mongodb-org
  systemctl start mongod
  systemctl enable mongod
  print_text_done 
  # certbot
  print_text_installing "â†’ Installing: Certbot..."
  sudo apt install certbot python3-certbot-nginx -y
  print_text_done
  # firewalld
  print_text_installing "â†’ Installing & config Firewalld..."
  sudo apt install firewalld -y
  systemctl start firewalld
  systemctl enable firewalld
  sudo firewall-cmd --zone=public --permanent --add-service=http
  sudo firewall-cmd --zone=public --permanent --add-service=https
  sudo firewall-cmd --zone=public --permanent --add-port=8000/tcp
  sudo firewall-cmd --zone=public --permanent --add-port=8000-8999/tcp
  sudo firewall-cmd --reload
  print_text_done
}

# go to /web/ folder
prepare_sourcecode(){
  print_text_installing "â†’ Preparing source code..."
  mkdir -p /web/
  cd /tmp
  unzip $tagname.zip
  rm $tagname.zip
  mv $foldername /web/affiliatecms
  cd /web/affiliatecms
  echo $tagname > /web/affiliatecms/.version
  print_text_done
}

restore_default_db(){
  print_text_installing "â†’ Restoring default database..."
  mongorestore --gzip --archive=/web/affiliatecms/mongodump/affiliatecms.agz --nsInclude="*"
  print_text_done
}

start_webserver(){
  print_text_installing "â†’ Starting webserver..."
  cd /web/affiliatecms
  yarn install
  pm2 start
  pm2 startup
  pm2 save
  print_text_done
}

show_done_message(){
  echo ""
  print_text_yellow "Setup is completed, you can now access your new website at: http://ip:8000";
  print_text_yellow "For more information, please visit: https://affiliatecms.com";
}

show_done_setup_message(){
  echo ""
  print_text_yellow "Your VPS is ready!"
}

##########################
# MAIN FUNCTION
##########################
setupServer(){
  install_server_utils
  install_nodejs
  show_done_setup_message
}

install(){
  download_installer
  prepare_sourcecode
  restore_default_db
  start_webserver
  show_done_message
}

main(){
  setupServer
}

main

exit
