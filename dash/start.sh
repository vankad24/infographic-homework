#!/bin/sh

set -e


VENV_DIR="venv"

# Создаём виртуальное окружение, если его нет
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Устанавливаем зависимости
echo "Installing dependencies..."
$VENV_DIR/bin/python -m pip install -r requirements.txt

$VENV_DIR/bin/python app.py
