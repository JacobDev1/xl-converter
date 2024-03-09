#!/bin/bash

VERSION="0.9"

install(){
    # Remove older version
    if [ -d "/opt/xl-converter" ]; then
        sudo rm -rf "/opt/xl-converter"
    fi

    # Desktop entries
    cp xl-converter.desktop ~/Desktop/
    cp xl-converter.desktop ~/.local/share/applications/

    # Install
    echo "Installing..."
    sudo cp -r xl-converter /opt/           # Copy program files
    sudo chmod -R +x /opt/xl-converter      # Add executable permissions
    
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

post_install(){
    # Refresh start menu entries
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database ~/.local/share/applications/
    fi

    # Check if fuse is installed
    if ! command -v fusermount &> /dev/null; then
        echo -e "\033[31mAppImage support is missing! Please install fuse.\033[0m"
        echo -e "    fuse is required by one of the dependencies."
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

    if [ $choice == "1" ]; then
        check_root_permissions
        install
        post_install
        exit 0
    fi
}

main