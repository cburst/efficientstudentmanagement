# Function to handle errors gracefully and exit the script
function Handle-Error {
    param([string]$ErrorMessage)
    Write-Host "ERROR: $ErrorMessage" -ForegroundColor Red
    exit 1
}

# Function to install individual pip packages after checking if they are installed and at the correct version
function Install-PipPackage {
    param(
        [string]$package,
        [string]$version
    )
    try {
        # Check if the package is already installed and matches the version
        $pipShowOutput = & python -m pip show $package 2>&1
        if ($pipShowOutput -match "Version: $version") {
            Write-Host "$package is already installed with the correct version ($version). Skipping installation."
        } else {
            Write-Host "Installing $package version $version..."
            $pipInstallOutput = & python -m pip install $package==$version --force-reinstall --no-cache-dir 2>&1
            Write-Host $pipInstallOutput

            if ($pipInstallOutput -match "Successfully installed") {
                Write-Host "$package installed successfully."
            } else {
                Write-Host "$package installation failed. See logs above."
            }
        }
    } catch {
        Handle-Error "Failed to install $package."
    }
}

# Function to ensure the environment variable is properly set
function Set-EnvironmentVariableAndRefresh {
    param(
        [string]$variableName,
        [string]$value
    )

    try {
        [System.Environment]::SetEnvironmentVariable($variableName, $value, [System.EnvironmentVariableTarget]::Machine)
        Write-Host "$variableName set as a global environment variable."

        # Refresh environment variables
        & powershell -ExecutionPolicy Bypass -Command "[System.Environment]::SetEnvironmentVariable('$variableName', '$value', [System.EnvironmentVariableTarget]::Process);"
    } catch {
        Handle-Error "Failed to set $variableName as an environment variable."
    }
}

try {
    # 1. Detect Windows Version and Architecture
    try {
        $windowsVersion = (Get-WmiObject -Class Win32_OperatingSystem).Version
        Write-Host "Detected Windows Version: $windowsVersion"

        # Determine if the system is ARM64, 32-bit, or 64-bit
        $architecture = (Get-WmiObject Win32_OperatingSystem).OSArchitecture
        Write-Host "Detected Architecture: $architecture"

        $processorArchitecture = (Get-WmiObject -Class Win32_Processor).Architecture
        Write-Host "Detected Processor Architecture: $processorArchitecture"

    } catch {
        Handle-Error "Failed to detect Windows version or architecture."
    }

    # 2. Download and Install Python 3.11.9 based on Architecture
    try {
        if ($architecture -like '*64*' -and $processorArchitecture -eq 5) {
            # ARM64 architecture
            $pythonInstaller = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-arm64.exe'
        } elseif ($architecture -like '*64*') {
            # x64 architecture
            $pythonInstaller = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
        } elseif ($architecture -like '*32*') {
            # x86 (32-bit) architecture
            $pythonInstaller = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe'
        } else {
            Handle-Error "Unsupported system architecture detected."
        }

        # Proceed with downloading the appropriate installer
        $pythonInstallerPath = "$env:TEMP\python-installer.exe"
        Invoke-WebRequest -Uri $pythonInstaller -OutFile $pythonInstallerPath
        Start-Process -FilePath $pythonInstallerPath -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait

        # Verify installation by checking the Python path directly
        $pythonPath = (Get-Command python).Source
        if (-not $pythonPath) {
            Handle-Error "Python installation failed or not found in PATH."
        }
        Write-Host "Python installed at: $pythonPath"
    } catch {
        Handle-Error "Failed to download or install Python."
    }

    # 3. Download Zip from GitHub
    try {
        $githubRepoZip = 'https://github.com/cburst/efficientstudentmanagement/archive/refs/heads/main.zip'
        $zipPath = "$env:TEMP\efficientstudentmanagement.zip"
        Invoke-WebRequest -Uri $githubRepoZip -OutFile $zipPath
        Write-Host "GitHub repository downloaded."
    } catch {
        Handle-Error "Failed to download the GitHub repository."
    }

    # 4. Unzip the downloaded file and copy content to target location
    try {
        $targetDir = 'C:\efficientstudentmanagement-main'
        Expand-Archive -Path $zipPath -DestinationPath $targetDir -Force
        Write-Host "Files extracted to $targetDir"
    } catch {
        Handle-Error "Failed to unzip or copy the content to the target location."
    }

    # 5. Install Dependencies (both from requirements and secondary requirements)
    try {
        $requirementsFile = 'C:\efficientstudentmanagement-main\folders\gpt-cli\requirements.txt'
        $secondaryRequirementsFile = 'C:\efficientstudentmanagement-main\folders\gpt-cli\secondary_requirements.txt'

        Write-Host "Installing Python dependencies from requirements.txt and secondary_requirements.txt..."

        # Install each package in the requirements file individually
        Get-Content $requirementsFile | ForEach-Object {
            if ($_ -and $_ -notmatch "^#") {
                $packageDetails = $_.Split("==")
                Install-PipPackage $packageDetails[0] $packageDetails[1]
            }
        }

        # Install each package in the secondary requirements file individually
        Get-Content $secondaryRequirementsFile | ForEach-Object {
            if ($_ -and $_ -notmatch "^#") {
                $packageDetails = $_.Split("==")
                Install-PipPackage $packageDetails[0] $packageDetails[1]
            }
        }

        Write-Host "Dependencies installed successfully."
    } catch {
        Handle-Error "Failed to install Python dependencies."
    }

    # 6. Create a PowerShell link on the desktop
    try {
        $desktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Open Project Folder.lnk')
        $target = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
        $workingDir = $targetDir
        $wScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $wScriptShell.CreateShortcut($desktopPath)
        $shortcut.TargetPath = $target
        $shortcut.WorkingDirectory = $workingDir
        $shortcut.Save()
        Write-Host "Shortcut created on the desktop."
    } catch {
        Handle-Error "Failed to create a desktop shortcut."
    }

    # 7. Ask user for API Key
    try {
        $apiKey = Read-Host -Prompt 'Enter your OPENAI_API_KEY'
        if ([string]::IsNullOrEmpty($apiKey)) {
            Handle-Error "No API key provided."
        } else {
            Write-Host "API key entered."
        }
    } catch {
        Handle-Error "Failed to read API key from user."
    }

    # 8. Set API key as a global, permanent environment variable and refresh
    try {
        Set-EnvironmentVariableAndRefresh 'OPENAI_API_KEY' $apiKey
    } catch {
        Handle-Error "Failed to set OPENAI_API_KEY as an environment variable."
    }

    # 9. Test Python Installation
    try {
        Write-Host "Testing Python installation..."

        # Directly call python and capture output to confirm installation works
        $pythonTest = & python -c "print('Python installation successful!')" 2>&1

        if ($pythonTest -match "Python installation successful!") {
            Write-Host "Python test completed successfully."

            # 10. Re-run requirements and secondary requirements individually
            try {
                Write-Host "Re-running individual pip installs for requirements.txt and secondary_requirements.txt..."
                $requirementsFile = 'C:\efficientstudentmanagement-main\folders\gpt-cli\requirements.txt'
                $secondaryRequirementsFile = 'C:\efficientstudentmanagement-main\folders\gpt-cli\secondary_requirements.txt'

                # Install each package individually again in case any were missed
                Get-Content $requirementsFile | ForEach-Object {
                    if ($_ -and $_ -notmatch "^#") {
                        $packageDetails = $_.Split("==")
                        Install-PipPackage $packageDetails[0] $packageDetails[1]
                    }
                }

                Get-Content $secondaryRequirementsFile | ForEach-Object {
                    if ($_ -and $_ -notmatch "^#") {
                        $packageDetails = $_.Split("==")
                        Install-PipPackage $packageDetails[0] $packageDetails[1]
                    }
                }

                Write-Host "All individual pip installs completed successfully."
            } catch {
                Handle-Error "Failed to re-run individual pip installs."
            }

        } else {
            Handle-Error "Python installation test failed. Output: $pythonTest"
        }
    } catch {
        Handle-Error "Failed to test Python installation."
    }

    # 11. Test GPT-CLI Command
    try {
        Write-Host "Testing GPT-CLI..."
        Set-Location 'C:\efficientstudentmanagement-main\folders\gpt-cli'
        Start-Process -NoNewWindow -Wait -FilePath 'python' -ArgumentList 'gpt.py'
        Write-Host "GPT-CLI test completed successfully."
    } catch {
        Handle-Error "Failed to run GPT-CLI test."
    }

} finally {
    Write-Host "Script execution completed. Exiting..."
}