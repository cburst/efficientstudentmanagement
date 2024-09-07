#!/bin/bash

# Function to handle errors gracefully and exit the script
function handle_error {
    echo "ERROR: $1"
    exit 1
}

# Function to deactivate all Python versions between 3.0 and 3.20
function deactivate_python_versions {
    echo "Deactivating any existing Python versions from 3.0 to 3.20..."

    # Loop through all Python versions between 3.0 and 3.20
    for version in {0..20}; do
        if [[ $version -ge 10 ]]; then
            python_version="3.${version}"
        else
            python_version="3.0${version}"
        fi

        # Check if this version of Python is installed and unlink it if so
        if brew list --versions python@$python_version > /dev/null 2>&1; then
            echo "Unlinking Python $python_version..."
            brew unlink python@$python_version || handle_error "Failed to unlink Python $python_version."
        fi
    done

    echo "All Python versions between 3.0 and 3.20 have been deactivated."
}

# 1. Install Homebrew if not already installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    echo "You may be prompted for your password during the Homebrew installation."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Failed to install Homebrew."
else
    echo "Homebrew is already installed."
fi

# Deactivate any older versions of Python before installing Python 3.11
deactivate_python_versions

# 2. Install Python 3.11.9 using Homebrew
echo "Installing Python 3.11.9 via Homebrew..."
echo "You may be prompted for your password during the Python installation."
brew install python@3.11 || handle_error "Failed to install Python 3.11."

# 3. Ensure Python 3.11 is the default version
echo "Setting Python 3.11 as the default..."
brew link --overwrite python@3.11 || handle_error "Failed to link Python 3.11."

# 4. Update the PATH to ensure Python 3.11 is used globally
echo "Updating PATH to prioritize Python 3.11..."
export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
if [ -f "$HOME/.bash_profile" ]; then
    echo "export PATH=\"/opt/homebrew/opt/python@3.11/bin:\$PATH\"" >> "$HOME/.bash_profile"
    source "$HOME/.bash_profile"
fi
if [ -f "$HOME/.zshrc" ]; then
    echo "export PATH=\"/opt/homebrew/opt/python@3.11/bin:\$PATH\"" >> "$HOME/.zshrc"
    source "$HOME/.zshrc"
fi

# 5. Download the GitHub repository to the target directory
echo "Downloading the GitHub repository..."
GITHUB_REPO_URL="https://github.com/cburst/efficientstudentmanagement/archive/refs/heads/main.zip"
TARGET_DIR="$HOME/efficientstudentmanagement-main"
ZIP_FILE="$HOME/efficientstudentmanagement.zip"

curl -L "$GITHUB_REPO_URL" -o "$ZIP_FILE" || handle_error "Failed to download the GitHub repository."

# 6. Unzip the downloaded file and move it to the target directory
echo "Extracting the repository..."
unzip -o "$ZIP_FILE" -d "$HOME" || handle_error "Failed to unzip the repository."
rm "$ZIP_FILE"

# 7. Install Python dependencies from requirements.txt with --no-deps to prevent unnecessary upgrades
echo "Installing Python dependencies without unnecessary dependency resolution..."
REQUIREMENTS_FILE="$TARGET_DIR/folders/gpt-cli/requirements.txt"
pip3 install --no-deps -r "$REQUIREMENTS_FILE" || handle_error "Failed to install Python dependencies."

# 8. Ensure correct attrs version (23.2.0) is installed
echo "Installing the correct attrs version (23.2.0)..."
pip3 uninstall attrs -y || handle_error "Failed to uninstall conflicting attrs version."
pip3 install attrs==23.2.0 --no-deps || handle_error "Failed to install attrs==23.2.0."

# 9. Upgrade OpenSSL and link it to Python
echo "Upgrading OpenSSL to resolve SSL issues..."
brew install openssl || handle_error "Failed to install OpenSSL."
echo "Linking OpenSSL to Python..."
export PATH="/usr/local/opt/openssl/bin:$PATH"
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
brew link openssl --force || handle_error "Failed to link OpenSSL."

# 10. Reinstall urllib3 and requests to use the correct OpenSSL version
echo "Reinstalling urllib3 and requests with proper OpenSSL support..."
pip3 install --upgrade urllib3 requests || handle_error "Failed to upgrade urllib3 and requests."

# 11. Create a terminal shortcut on the desktop to open in the target directory with environment variables loaded
echo "Creating a Terminal shortcut on the Desktop..."

SHORTCUT_FILE="$HOME/Desktop/Open_EfficientStudentManagement.command"
DEFAULT_SHELL=$(basename $SHELL)

cat <<EOL > "$SHORTCUT_FILE"
#!/bin/$DEFAULT_SHELL

# Source your shell configuration to load all environment variables
if [ -f "\$HOME/.bash_profile" ]; then
    source "\$HOME/.bash_profile"
fi
if [ -f "\$HOME/.zshrc" ]; then
    source "\$HOME/.zshrc"
fi

# Change directory to the project directory
cd "$TARGET_DIR"

# Keep the terminal open after execution
exec /bin/$DEFAULT_SHELL
EOL

# 12. Apply chmod +x to make the .command file executable
echo "Making the .command file executable..."
chmod +x "$SHORTCUT_FILE" || handle_error "Failed to make .command file executable."

# 13. Ask the user for the API key and set it as a global environment variable
read -p "Enter your OPENAI_API_KEY: " API_KEY
if [ -z "$API_KEY" ]; then
    handle_error "No API key provided."
fi

echo "Setting the OPENAI_API_KEY environment variable..."
if [ -f "$HOME/.bash_profile" ]; then
    echo "export OPENAI_API_KEY=\"$API_KEY\"" >> "$HOME/.bash_profile"
fi
if [ -f "$HOME/.zshrc" ]; then
    echo "export OPENAI_API_KEY=\"$API_KEY\"" >> "$HOME/.zshrc"
fi

# 14. Test Python installation
echo "Testing Python installation..."
python3 -c "print('Python installation successful!')" || handle_error "Failed to test Python installation."

# 15. Launch a new terminal to test GPT-CLI with a refreshed environment
echo "Testing GPT-CLI in a new terminal session..."

osascript <<EOD
tell application "Terminal"
    do script "cd $TARGET_DIR/folders/gpt-cli && source ~/.zshrc && python3 gpt.py"
end tell
EOD

echo "Please restart your terminal to fully apply the changes in this session, or you can start a new session with the desktop shortcut."
echo "Setup complete! You can now double-click the .command file on your Desktop to open the project."
