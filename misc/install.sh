#!/usr/bin/bash

VERSION="0.9"

echo -e "\nXL Converter $VERSION Installer\n"

if [ -d "/opt/xl-converter" ]; then
    echo "[1] Update (/opt/xl-converter)"
else
    echo "[1] Install (/opt/xl-converter)"
fi

echo -e "[2] Exit\n"

read -p "Choice: " choice

if [ $choice == "1" ]; then
    # Icon
    cp xl-converter.desktop ~/Desktop/
    cp xl-converter.desktop ~/.local/share/applications

    # Remove older version
    if [ -d "/opt/xl-converter" ]; then
        sudo rm -r "/opt/xl-converter"
    fi

    # Install
    echo "Installing..."
    sudo cp -r xl-converter /opt/xl-converter
    sudo chmod -R +x /opt/xl-converter
    
    echo "Installation completed"
    echo "You will find shortcuts in the start menu and the desktop"
fi
