#!/usr/bin/env bash

# Checks if running on MSYS2.
check_msys2() {
    if [ "${MSYSTEM:-}" != "MINGW64" ]; then
        echo "MSYS2 MINGW64 environment is required to run this script."
        exit 1
    fi
}

# Cleans up a temp dir.
cleanup() {
    echo "Cleaning up..."
    cd / || return 1	# Avoid "device or resource busy" error.
    rm -rf "$1"
}

# Checks if packages or groups are present. Returns `exit 1` with a message in case some are missing. 
check_packages() {
    local required_packages=("$@")
    local installed_packages installed_groups
    local missing_packages=()
    
    installed_packages=$(pacman -Q 2>/dev/null)
    installed_groups=$(pacman -Qg 2>/dev/null)

    for pkg in "${required_packages[@]}"; do
        if ! echo "${installed_packages}" | grep -q "^${pkg}" && \
            ! echo "${installed_groups}" | grep -q "^${pkg}"; then
            missing_packages+=("${pkg}")
        fi
    done

    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        echo -e "Missing packages.\nInstall them with: pacman -S ${missing_packages[*]}"
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

# Scans a dir for EXEs and includes necessary DLLs. 
bundle_dlls() {
    find "$1" -type f -name "*.exe" | while read -r exe; do  # Iterate through EXEs
        ldd "${exe}" | awk '/\/mingw64\// {print $3}' | while read -r dll; do   # Find a DLL (omits system32)
            if [ ! -f "$1/$(basename "${dll}")" ]; then      # Check if a DLL already exists
                cp "${dll}" "$1"
            fi
        done
    done
}

