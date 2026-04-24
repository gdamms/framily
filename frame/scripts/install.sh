# Framily installation script. This script is meant to be piped to sh, and will install Framily on the system.
# Usage: curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/framily.sh | sh
# or maybe this one?
# Usage: curl -sL https://raw.githubusercontent.com/gdamms/framily/refs/heads/main/frame/framily.sh | sh

SCRIPT_URL="https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh"
RELEASE_URL="https://github.com/you/repo/releases/latest/download/frame.tar.gz"
FRAMILY_OPT="/opt/framily"
SETUP_PATH="$FRAMILY_OPT/scripts/setup.sh"

log() {
    # Simple logging function to prefix messages with [framily]
    echo "[framily] $*"
}

# Check if the script is being run as root
if [ "$(id -u)" -ne 0 ]; then
    log "This script must be run as root. Please run with sudo or as root user."
    exit 1
fi

# Check if framily is already installed
if [ -d "$FRAMILY_OPT" ]; then
    log "Framily is already installed. Please uninstall using `framily uninstall` before running this script again."
    read -p "Do you want to uninstall Framily now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Uninstalling Framily..."
        framily uninstall
    else
        log "Aborting installation."
        exit 1
    fi
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    log "curl is not installed. Please install curl and try again."
    exit 1
fi

# Check if tar is installed
if ! command -v tar &> /dev/null; then
    log "tar is not installed. Please install tar and try again."
    exit 1
fi

# Download and extract the latest release of Framily
mkdir -p "$FRAMILY_OPT"
curl -L "$RELEASE_URL" | tar -xz -C "$FRAMILY_OPT"
if [ $? -ne 0 ]; then
    log "Failed to download and extract Framily. Please check your internet connection and try again."
    exit 1
fi

# Run the setup script
sh "$SETUP_PATH"
if [ $? -ne 0 ]; then
    log "Framily setup failed. Please check the output above for details."
    exit 1
fi
log "Framily installation completed successfully!"
