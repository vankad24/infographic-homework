#!/bin/sh

set -e


# make visible for child processes

SERVER_NAME="vibe-code-homework.24-7.ro"
export SERVER_NAME

CONFIG_NAME="$SERVER_NAME.conf"

VENV_DIR=".venv"

# Создаём виртуальное окружение, если его нет
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Устанавливаем зависимости
echo "Installing dependencies..."
$VENV_DIR/bin/python -m pip install -r requirements.txt


if command -v apt >/dev/null 2>&1; then
    echo "Detected apt. Installing packages..."
    
    sudo apt update
    sudo apt install -y nginx certbot python3-certbot-nginx nodejs npm
	sudo systemctl enable --now docker nginx
	
	sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template | sudo tee "/etc/nginx/sites-available/$CONFIG_NAME" > /dev/null
	sudo ln -sfn /etc/nginx/sites-available/$CONFIG_NAME /etc/nginx/sites-enabled/$CONFIG_NAME
	
elif command -v apk >/dev/null 2>&1; then
    echo "Detected apk. Installing packages..."
    
    sudo apk update
    sudo apk add nginx nginx-systemd certbot certbot-nginx nodejs npm
	# sudo systemctl enable --now docker nginx
	sudo rm -f /etc/nginx/http.d/default.conf

	
	sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template | sudo tee "/etc/nginx/http.d/$CONFIG_NAME" > /dev/null

else
    echo "Error: neither apt nor apk was found."
    exit 1
fi

sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx --reinstall -d "$SERVER_NAME"
sudo certbot renew --dry-run

echo "To check https try visit: https://$SERVER_NAME"

