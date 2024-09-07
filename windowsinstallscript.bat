@echo off
:: Check if the script is running with administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Check if PowerShell is available
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo PowerShell is not available on your system. Please install PowerShell.
    pause
    exit /b
)

:: Run PowerShell commands inline
powershell -ExecutionPolicy Bypass -Command "

# Function to handle errors gracefully and exit the script
function Handle-Error {
    param([string]`$ErrorMessage)
    Write-Host 'ERROR: ' `$ErrorMessage -ForegroundColor Red
    exit 1
}

try {
    # 1. Detect Windows Version and Architecture
    try {
        `$windowsVersion = (Get-WmiObject -Class Win32_OperatingSystem).Version
        Write-Host 'Detected Windows Version: ' `$windowsVersion

        # Determine if the system is 32-bit or 64-bit
        `$architecture = (Get-WmiObject Win32_OperatingSystem).OSArchitecture
        Write-Host 'Detected Architecture: ' `$architecture
    } catch {
        Handle-Error 'Failed to detect Windows version or architecture.'
    }

    # 2. Download and Install Python 3.11.9 based on Architecture
    try {
        if (`$architecture -like '*64*') {
            # Download Python 64-bit version
            `$pythonInstaller = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
        } elseif (`$architecture -like '*32*') {
            # Download Python 32-bit version
            `$pythonInstaller = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe'
        } else {
            Handle-Error 'Unsupported system architecture detected.'
        }

        # Proceed with downloading the appropriate installer
        `$pythonInstallerPath = `"$env:TEMP\python-installer.exe`"
        Invoke-WebRequest -Uri `$pythonInstaller -OutFile `$pythonInstallerPath
        Start-Process -FilePath `$pythonInstallerPath -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait

        # Verify installation
        `$pythonPath = (Get-Command python).Source
        if (-not `$pythonPath) {
            Handle-Error 'Python installation failed or not found in PATH.'
        }
        Write-Host 'Python installed at: ' `$pythonPath
    } catch {
        Handle-Error 'Failed to download or install Python.'
    }

    # 3. Download Zip from GitHub
    try {
        `$githubRepoZip = 'https://github.com/cburst/efficientstudentmanagement/archive/refs/heads/main.zip'
        `$zipPath = `"$env:TEMP\efficientstudentmanagement.zip`"
        Invoke-WebRequest -Uri `$githubRepoZip -OutFile `$zipPath
        Write-Host 'GitHub repository downloaded.'
    } catch {
        Handle-Error 'Failed to download the GitHub repository.'
    }

    # 4. Unzip the downloaded file and copy content to target location
    try {
        `$targetDir = 'C:\efficientstudentmanagement-main'
        Expand-Archive -Path `$zipPath -DestinationPath `$targetDir -Force
        Write-Host 'Files extracted to ' `$targetDir
    } catch {
        Handle-Error 'Failed to unzip or copy the content to the target location.'
    }

    # 5. Run terminal command to install dependencies from the correct requirements file
    try {
        `$requirementsFile = 'C:\efficientstudentmanagement-main\folders\gpt-cli\requirements.txt'
        Start-Process -NoNewWindow -Wait -FilePath 'python' -ArgumentList '-m pip install -r `$requirementsFile'
        Write-Host 'Dependencies installed successfully.'
    } catch {
        Handle-Error 'Failed to install Python dependencies.'
    }

    # 6. Create a PowerShell link on the desktop
    try {
        `$desktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Open Project Folder.lnk')
        `$target = `"$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe`"
        `$workingDir = `$targetDir
        `$wScriptShell = New-Object -ComObject WScript.Shell
        `$shortcut = `$wScriptShell.CreateShortcut(`$desktopPath)
        `$shortcut.TargetPath = `$target
        `$shortcut.WorkingDirectory = `$workingDir
        `$shortcut.Save()
        Write-Host 'Shortcut created on the desktop.'
    } catch {
        Handle-Error 'Failed to create a desktop shortcut.'
    }

    # 7. Ask user for API Key
    try {
        `$apiKey = Read-Host -Prompt 'Enter your OPENAI_API_KEY'
        if ([string]::IsNullOrEmpty(`$apiKey)) {
            Handle-Error 'No API key provided.'
        } else {
            Write-Host 'API key entered.'
        }
    } catch {
        Handle-Error 'Failed to read API key from user.'
    }

    # 8. Set API key as a global, permanent environment variable
    try {
        [System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', `$apiKey, [System.EnvironmentVariableTarget]::Machine)
        Write-Host 'OPENAI_API_KEY set as a global environment variable.'
    } catch {
        Handle-Error 'Failed to set OPENAI_API_KEY as an environment variable.'
    }

    # 9. Test Python Installation
    try {
        Write-Host 'Testing Python installation...'
        Start-Process -NoNewWindow -Wait -FilePath 'python' -ArgumentList '-c ""print(''Python installation successful!'')"'
        Write-Host 'Python test completed successfully.'
    } catch {
        Handle-Error 'Failed to test Python installation.'
    }

    # 10. Test GPT-CLI Command
    try {
        Write-Host 'Testing GPT-CLI...'
        Set-Location 'C:\efficientstudentmanagement-main\folders\gpt-cli'
        Start-Process -NoNewWindow -Wait -FilePath 'python' -ArgumentList 'gpt.py'
        Write-Host 'GPT-CLI test completed successfully.'
    } catch {
        Handle-Error 'Failed to run GPT-CLI test.'
    }

} finally {
    Write-Host 'Script execution completed. Exiting...'
}

"
pause