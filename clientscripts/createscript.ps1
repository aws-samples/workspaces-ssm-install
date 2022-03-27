
if ($IsLinux) {
    Set-Variable -Name "BaseOS" -Value ("Linux") -Scope global
                }
elseif ( (Get-ChildItem -Path Env:OS).Value -eq "WINDOWS_NT") {
    Set-Variable -Name "BaseOS" -Value ("Windows") -Scope global}
else { Write-Host "Unable to detect the OS, hence Quitting"}

$BaseURL = Read-Host "Enter the API endpoint URL Eg: https://xxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/ "

$insertstr= "Set-Variable -Name wsfbaseurl -Value ('" + $BaseURL + "') -Scope global"


$insertstr | Set-Content tempfile.txt
Get-Content multiplatformloginscript.ps1 |
Add-Content tempfile.txt
Rename-Item tempfile.txt -NewName finalmultiplatformloginscript.ps1

switch ($BaseOS)
        {
            Linux
            { 
            write-host "Detected the OS as Linux setting up the script sytemd service and timer"
            Copy-Item ./finalmultiplatformloginscript.ps1 /usr/local/bin/finalmultiplatformloginscript.ps1
            Copy-Item ./ssminstall.service /etc/systemd/system/
            Copy-Item ./ssminstall.timer /etc/systemd/system/
            Remove-Item ./finalmultiplatformloginscript.ps1
             systemctl enable --now ssminstall.timer
             systemctl enable --now ssminstall.service
             systemctl daemon-reload
            }

            Windows
            {
            write-host "Detected the OS as Windows setting up the script and enabling Scheduled tasks"
            $folderloc = "C:\programdata\ssm_script\"
            if (test-path $folderloc)
                {
                write-host "Destination folder already exists"
                }
            else{
                New-Item $folderloc -ItemType Directory
                Write-Host "destination folder created"
                }
             Copy-Item .\finalmultiplatformloginscript.ps1 $folderloc -force
             Copy-Item .\trigger.bat $folderloc
             Remove-Item .\finalmultiplatformloginscript.ps1
    
    schtasks /create /tn "ssm_Install_script" /xml "./schldtskwin.xml" 
            }
            
        }
                    