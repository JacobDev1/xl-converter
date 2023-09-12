#!/usr/bin/bash

echo "XL Converter v0.9 installer"
echo "----------------------------"
if [ -d "/opt/xl-converter" ]; then
    echo "1. Replace older version (/opt/xl-converter)"
else
    echo "1. Install (/opt/xl-converter)"    
fi

echo "2. Exit"

read -p "Choice: " choice

if [ $choice == "1" ]; then
    # Icon
    cp xl-converter.desktop ~/Desktop/

    # Remove older version
    if [ -d "/opt/xl-converter" ]; then
        sudo rm -r "/opt/xl-converter"
    fi

    # Install
    sudo cp -r xl-converter /opt/xl-converter
    sudo chmod -R +x /opt/xl-converter
fi