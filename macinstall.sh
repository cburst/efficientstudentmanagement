#!/bin/bash

# Function to handle errors gracefully and exit the script
function handle_error {
    echo "ERROR: $1"
    exit 1
}

# 1. Install Homebrew if not already installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Failed to install Homebrew."
else
    echo "Homebrew is already installed."
fi

# 2. Install Python 3.11 using Homebrew
echo "Installing Python 3.11 via Homebrew..."
brew install python@3.11 || handle_error "Failed to install Python 3.11."

# 3. Download the GitHub repository to the target directory
echo "Downloading the GitHub repository..."
GITHUB_REPO_URL="https://github.com/cburst/efficientstudentmanagement/archive/refs/heads/main.zip"
TARGET_DIR="$HOME/efficientstudentmanagement-main"
ZIP_FILE="$HOME/efficientstudentmanagement.zip"

curl -L "$GITHUB_REPO_URL" -o "$ZIP_FILE" || handle_error "Failed to download the GitHub repository."

# 4. Unzip the downloaded file and move it to the target directory
echo "Extracting the repository..."
unzip -o "$ZIP_FILE" -d "$HOME" || handle_error "Failed to unzip the repository."
rm "$ZIP_FILE"

# 5. Install Python dependencies from requirements.txt
echo "Installing Python dependencies..."
REQUIREMENTS_FILE="$TARGET_DIR/folders/gpt-cli/requirements.txt"
pip3 install -r "$REQUIREMENTS_FILE" || handle_error "Failed to install Python dependencies."

# 6. Create a terminal shortcut on the desktop to open in the target directory
echo "Creating a Terminal shortcut on the Desktop..."
SHORTCUT_FILE="$HOME/Desktop/Open_EfficientStudentManagement.command"

cat <<EOL > "$SHORTCUT_FILE"
#!/bin/bash
cd "$TARGET_DIR"
exec /bin/bash
EOL

chmod +x "$SHORTCUT_FILE" || handle_error "Failed to create a terminal shortcut."

# 7. Ask the user for the API key
read -p "Enter your OPENAI_API_KEY: " API_KEY
if [ -z "$API_KEY" ]; then
    handle_error "No API key provided."
fi

# 8. Set API key as a global, permanent environment variable
echo "Setting the OPENAI_API_KEY environment variable..."
echo "export OPENAI_API_KEY=\"$API_KEY\"" >> ~/.bash_profile
source ~/.bash_profile || handle_error "Failed to set OPENAI_API_KEY environment variable."

# 9. Test Python installation
echo "Testing Python installation..."
python3 -c "print('Python installation successful!')" || handle_error "Failed to test Python installation."

# 10. Test GPT-CLI
echo "Testing GPT-CLI..."
cd "$TARGET_DIR/folders/gpt-cli"
python3 gpt.py || handle_error "Failed to run GPT-CLI test."

echo "Setup complete!"