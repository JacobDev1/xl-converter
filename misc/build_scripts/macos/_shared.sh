#!/bin/bash

# Cleans up a temp dir.
cleanup() {
    echo "Cleaning up..."
    cd / || return 1	# Avoid "device or resource busy" error.
    rm -rf "$1"
}

check_env() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        echo "Error: This script can only be run on MacOS."
        exit 1
    fi
}

# Checks if packages are present.
check_packages() {
    local pkg missing=()

    for pkg in "$@"; do
        if ! port installed "$pkg" &>/dev/null; then
            missing+=("${pkg}")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        echo -e "Missing packages.\nInstall them with: sudo port install ${missing[*]}"
        exit 1
    fi
}

# Check if a set of commands is available.
check_commands() {
    local required_commands=("$@")
    local missing_commands=()

    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            missing_commands+=("${cmd}")
        fi
    done

    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        echo -e "Missing command-line tools: ${missing_commands[*]}\nInstall them and try again."
        exit 1
    fi
}

# Yellow text
warning() {
    printf '\033[33m%b\033[0m\n' "$*"
}
