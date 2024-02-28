#!/bin/bash

VERSION="0.9"

install(){
    # Remove older version
    if [ -d "/opt/xl-converter" ]; then
        sudo rm -rf "/opt/xl-converter"
    fi

    # Desktop entries
    cp xl-converter.desktop ~/Desktop/
    cp xl-converter.desktop ~/.local/share/applications

    # Install
    echo "Installing..."
    sudo cp -r xl-converter /opt
    sudo chmod -R +x /opt/xl-converter
    
    echo "Installation complete"
    echo "You will find shortcuts in the start menu and on the desktop"
}

check_root_permissions(){
    # Check if sudo is installed
    if ! command -v sudo &> /dev/null; then
        echo "Install sudo and try again"
        exit 1
    fi

    # Get root privileges
    if [ $EUID -ne 0 ]; then
        sudo -v || { echo "Installation canceled, try again."; exit 1; }
    fi
}

main(){
    echo -e "\nXL Converter $VERSION Installer\n"

    if [ -d "/opt/xl-converter" ]; then
        echo "[1] Update (/opt/xl-converter)"
    else
        echo "[1] Install (/opt/xl-converter)"
    fi

    echo -e "[2] Exit\n"

    read -p "Choice: " choice

    if [ $choice == "1" ]; then
        check_root_permissions
        install
        exit 0
    fi
}

main