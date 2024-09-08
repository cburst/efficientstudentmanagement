#!/bin/bash

# Function to handle errors gracefully and exit the script
function handle_error {
    echo "ERROR: $1"
    exit 1
}

# 1. Install Homebrew if not already installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    echo "You may be prompted for your password during the Homebrew installation."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Failed to install Homebrew."

    # 2. Add Homebrew to the PATH
    echo "Adding Homebrew to your PATH..."
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> "$HOME/.zprofile"
    eval "$(/opt/homebrew/bin/brew shellenv)" || handle_error "Failed to add Homebrew to the PATH."

    # 3. Reopen the terminal to refresh the environment
    echo "Closing the current terminal and reopening a new one..."
    
    osascript <<EOD
    tell application "Terminal"
        do script "
        if [ -f ~/.bash_profile ]; then
            source ~/.bash_profile
        fi
        source ~/.zshrc && cd ~ && ./macinstall.command"  -- Replace 'macinstall.command' with your script's filename
        delay 1
        close (every window whose name contains 'bash')
    end tell
EOD
    
    exit 0
else
    echo "Homebrew is already installed."
fi

# The script resumes from here when reopened

# 4. Install Python 3.11.9 using Homebrew
echo "Installing Python 3.11.9 via Homebrew..."
echo "You may be prompted for your password during the Python installation."
brew install python@3.11 || handle_error "Failed to install Python 3.11."

# 5. Ensure Python 3.11 is the default version
echo "Setting Python 3.11 as the default..."
brew link --overwrite python@3.11 || handle_error "Failed to link Python 3.11."

# 6. Update the PATH to ensure Python 3.11 is used globally and add aliases for both python3 and pip3
echo "Updating PATH to prioritize Python 3.11..."

# Function to update or create profile with aliases and Python path
write_to_profiles() {
    local profile="$1"
    if [ -f "$HOME/$profile" ]; then
        echo "Updating $profile with Python path and aliases..."
    else
        echo "Creating $profile and adding Python path and aliases..."
        touch "$HOME/$profile"
    fi

    # Add Python 3.11 path and aliases for python3 and pip3
    echo "export PATH=\"/opt/homebrew/opt/python@3.11/bin:\$PATH\"" >> "$HOME/$profile"
    echo "alias python3='/opt/homebrew/opt/python@3.11/bin/python3.11'" >> "$HOME/$profile"
    echo "alias pip3='/opt/homebrew/opt/python@3.11/bin/pip3.11'" >> "$HOME/$profile"
}

# Add Python aliases and path to .bash_profile and .zshrc
write_to_profiles ".bash_profile"
write_to_profiles ".zshrc"

# 7. Ask the user for the API key and set it as a global environment variable
read -p "Enter your OPENAI_API_KEY: " API_KEY
if [ -z "$API_KEY" ]; then
    handle_error "No API key provided."
fi

# Write the API key to both .bash_profile and .zshrc
add_api_key_to_profiles() {
    local profile="$1"
    echo "export OPENAI_API_KEY=\"$API_KEY\"" >> "$HOME/$profile"
}

add_api_key_to_profiles ".bash_profile"
add_api_key_to_profiles ".zshrc"

# Source both profiles to apply the changes
echo "Sourcing profiles to apply changes..."
if [ -f "$HOME/.bash_profile" ]; then
    source "$HOME/.bash_profile"
fi
source "$HOME/.zshrc"

# 8. Test Python 3.11 installation before proceeding
echo "Testing Python 3.11 installation..."
python3 -c "print('Python 3.11 installation successful!')" || handle_error "Failed to test Python 3.11 installation."

# 9. Download the GitHub repository to the target directory
echo "Downloading the GitHub repository..."
GITHUB_REPO_URL="https://github.com/cburst/efficientstudentmanagement/archive/refs/heads/main.zip"
TARGET_DIR="$HOME/efficientstudentmanagement-main"
ZIP_FILE="$HOME/efficientstudentmanagement.zip"

curl -L "$GITHUB_REPO_URL" -o "$ZIP_FILE" || handle_error "Failed to download the GitHub repository."

# 10. Unzip the downloaded file and move it to the target directory
echo "Extracting the repository..."
unzip -o "$ZIP_FILE" -d "$HOME" || handle_error "Failed to unzip the repository."
rm "$ZIP_FILE"

# Check if the target directory and requirements file exist before proceeding
if [ ! -f "$TARGET_DIR/folders/gpt-cli/requirements.txt" ]; then
    handle_error "Failed to find the requirements.txt file. Ensure the GitHub repo was downloaded and extracted correctly."
fi

# 11. Upgrade pip and install Python dependencies from requirements.txt after sourcing the profiles
echo "Upgrading pip and installing Python dependencies..."
pip3 install --upgrade pip || handle_error "Failed to upgrade pip."
REQUIREMENTS_FILE="$TARGET_DIR/folders/gpt-cli/requirements.txt"
pip3 install --no-deps -r "$REQUIREMENTS_FILE" || handle_error "Failed to install Python dependencies."

# 12. Ensure correct attrs version (23.2.0) is installed
echo "Installing the correct attrs version (23.2.0)..."
pip3 uninstall attrs -y || handle_error "Failed to uninstall conflicting attrs version."
pip3 install attrs==23.2.0 --no-deps || handle_error "Failed to install attrs==23.2.0."

# 13. Reinstall pydantic and pydantic_core with correct versions
echo "Reinstalling pydantic and pydantic_core with correct versions..."
pip3 install --force-reinstall pydantic==2.0.3 pydantic-core==2.3.0 || handle_error "Failed to reinstall pydantic or pydantic_core."

# 14. Upgrade OpenSSL and link it to Python
echo "Upgrading OpenSSL to resolve SSL issues..."
brew install openssl || handle_error "Failed to install OpenSSL."
echo "Linking OpenSSL to Python..."
export PATH="/usr/local/opt/openssl/bin:$PATH"
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
brew link openssl --force || handle_error "Failed to link OpenSSL."

# 15. Reinstall urllib3 and requests to use the correct OpenSSL version
echo "Reinstalling urllib3 and requests with proper OpenSSL support..."
pip3 install --upgrade urllib3 requests || handle_error "Failed to upgrade urllib3 and requests."

# 16. Create a terminal shortcut on the desktop to open in the target directory with environment variables loaded
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

# 17. Apply chmod +x to make the .command file executable
echo "Making the .command file executable..."
chmod +x "$SHORTCUT_FILE" || handle_error "Failed to make .command file executable."

# 18. Run secondary requirements installation after profiles are sourced
echo "Running secondary requirements installation..."
SECONDARY_REQUIREMENTS_FILE="$TARGET_DIR/folders/gpt-cli/secondary_requirements.txt"

cat <<EOL > "$SECONDARY_REQUIREMENTS_FILE"
google-generativeai==0.5.4
boto3==1.28.0
cohere==5.9.1
EOL

# Install the secondary dependencies
pip3 install --no-deps -r "$SECONDARY_REQUIREMENTS_FILE" || handle_error "Failed to install secondary dependencies."

# 19. Launch a new terminal to test GPT-CLI in a new environment
echo "Testing GPT-CLI in a new terminal session..."

osascript <<EOD
tell application "Terminal"
    do script "
    source ~/.zshrc && \
    cd $TARGET_DIR/folders/gpt-cli && \
    python3 gpt.py"
end tell
EOD

echo
