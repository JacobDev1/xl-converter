#!/bin/bash

VERSION="0.9"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

install(){
    # Remove older version
    if [ -d "/opt/xl-converter" ]; then
        sudo rm -rf "/opt/xl-converter/"
        sleep 0.5       # Stops menu entry from disappearing until restart
    fi

    # Desktop entries
    cp -f "$SCRIPT_DIR/xl-converter.desktop" ~/Desktop/
    sudo cp -f "$SCRIPT_DIR/xl-converter.desktop" /usr/share/applications/

    # Install
    echo "Installing..."
    sudo cp -rf "$SCRIPT_DIR/xl-converter" /opt/        # Copy program files
    sudo chmod -R +rx /opt/xl-converter                 # Add permissions
    
    echo "Installation complete"
}

check_root_permissions(){
    # Check if sudo is installed
    if ! command -v sudo &> /dev/null; then
        echo "Install sudo and try again"
        exit 1
    fi

    # Get root privileges (for copying files into /opt/)
    if [ $EUID -ne 0 ]; then
        sudo -v || { echo "Installation canceled, try again."; exit 1; }
    fi
}

pre_install(){
    # Check if fuse is installed
    if ! command -v fusermount &> /dev/null; then
        echo -e "\033[31mAppImage support is missing! Please install fuse and try again.\033[0m"
        echo "fuse is required by one of the dependencies."
        exit 1
    fi
}

post_install(){
    # Refresh start menu entries
    if command -v update-desktop-database &> /dev/null; then
        sudo update-desktop-database /usr/share/applications/ &> /dev/null
    fi
    
    echo "You will find shortcuts in the start menu and on the desktop"
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

    if [ "$choice" == "1" ]; then
        pre_install
        check_root_permissions
        install
        post_install
        exit 0
    fi
}

main