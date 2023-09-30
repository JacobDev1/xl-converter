#!/usr/bin/bash

VERSION="0.9"

echo "XL Converter $VERSION installer"
echo "----------------------------"
if [ -d "/opt/xl-converter" ]; then
    echo "1. Update (/opt/xl-converter)"
else
    echo "1. Install (/opt/xl-converter)"
fi

echo "2. Exit"

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
    sudo cp -r xl-converter /opt/xl-converter
    sudo chmod -R +x /opt/xl-converter
    
    echo "Desktop shortcut added"
    echo "Start menu entry added"
    echo "Installation completed"
fi
