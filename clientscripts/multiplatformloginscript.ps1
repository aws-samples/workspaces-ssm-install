<# 
.Synopsis 
   Add the workspace as a managed instance 
.DESCRIPTION 
   This is a script that is used to install SSM on windows and Linux. This scripts detects the platform
   and then downloads the right SSM installer for the platform, registers the instance as a manged instance
   by calling API gateway. This  script is expected to run on regular intervals


#> 

# Function to write log files

function logrotate 
    {
    Get-ChildItem $logbase | Where-Object LastWriteTime -LT (Get-Date).AddDays(-2)| Remove-Item -Force
    }

function Write-Log 
{ 
    [CmdletBinding()] 
    Param 
    ( 
        [Parameter(Mandatory=$true, 
                   ValueFromPipelineByPropertyName=$true)] 
        [ValidateNotNullOrEmpty()] 
        [Alias("LogContent")] 
        [string]$Message, 
 
        [Parameter(Mandatory=$false)] 
        [Alias('LogPath')] 
        [string]$Path='C:\Logs\PowerShellLog.log', 
         
        [Parameter(Mandatory=$false)] 
        [ValidateSet("Error","Warn","Info")] 
        [string]$Level="Info", 
         
        [Parameter(Mandatory=$false)] 
        [switch]$NoClobber 
    ) 
 
    Begin 
    { 
        # Set VerbosePreference to Continue so that verbose messages are displayed. 
        $VerbosePreference = 'Continue' 
    } 
    Process 
    {        
        # If the file already exists and NoClobber was specified, do not write to the log. 
        if ((Test-Path $Path) -AND $NoClobber) { 
            Write-Error "Log file $Path already exists, and you specified NoClobber. Either delete the file or specify a different name." 
            Return 
            } 
 
        # If attempting to write to a log file in a folder/path that doesn't exist create the file including the path. 
        elseif (!(Test-Path $Path)) { 
            Write-Verbose "Creating $Path." 
            $NewLogFile = New-Item $Path -Force -ItemType File 
            } 
 
        else { 
            # Nothing to see here yet. 
            } 
 
        # Format Date for our Log File 
        $FormattedDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss" 
 
        # Write message to error, warning, or verbose pipeline and specify $LevelText 
        switch ($Level) { 
            'Error' { 
                Write-Error $Message 
                $LevelText = 'ERROR:' 
                } 
            'Warn' { 
                Write-Warning $Message 
                $LevelText = 'WARNING:' 
                } 
            'Info' { 
                Write-Verbose $Message 
                $LevelText = 'INFO:' 
                } 
            } 
         
        # Write log entry to $Path 
        "$FormattedDate $LevelText $Message" | Out-File -FilePath $Path -Append 
    } 
    End 
    { 
    } 
}
function checkssmservice
{
    Param(
        [parameter(Mandatory=$true)]
        [String]
        $BaseOS
        )
    switch ($BaseOS)
    {
        linux{
            $serivicestatus= systemctl show -p SubState amazon-ssm-agent | cut -d “=” -f2
        }
        Windows{
            $servicenameout= Get-Service amazonssmagent -ErrorAction SilentlyContinue
            $serivicestatus= $servicenameout.Status 
        }
    }
    return $serivicestatus
}

function addadgrouptags
    {
        Param(
            [parameter(Mandatory=$true)]
            [String]
            $miid
            )
        Write-Log -Message " starting addadgrouptag function " -path $logfile -level INFO
        $wstagstringurladd= "wsmiaddtag/?wsid=" + $workspaceID + "&miid=" + $miid + "&hostname=" +
                             $hostname + "&username=" + $username + "&directoryid=" +$DirectoryID +"&wsregion="+ $wsregion 
        $finaladdtaguri = $wsfbaseurl +$wstagstringurladd
        write-log -Message "final add ws tag url is $finaladdtaguri " -path $logfile -level INFO
        write-log -Message "adding tag to instance " -path $logfile -level INFO
        $addingtagtomi = Invoke-WebRequest -Uri $finaladdtaguri -UseBasicParsing | ConvertFrom-Json
        write-log -Message "add AD tags API got response $addingtagtomi " -path $logfile -level INFO
        $wsaddgrouptag= "ad/?miid=" + $miid + "&username=" +$username
        $finaladdadtaguri = $wsfbaseurl +$wsaddgrouptag
        write-log -Message "final add AD group tag to ws url is $finaladdadtaguri " -path $logfile -level INFO
        write-log -Message "adding AD group tag to instance " -path $logfile -level INFO
        $addingadtagtomi = Invoke-WebRequest -Uri $finaladdadtaguri -UseBasicParsing | ConvertFrom-Json
        write-log -Message "add AD tags API got response $addingadtagtomi " -path $logfile -level INFO
    }

function ssmregcheck
    {
        Param(
        [parameter(Mandatory=$true)]
        [String]
        $BaseOS
        )
    switch ($BaseOS)
    {
        linux{
            $ssm_reg_stat= /usr/bin/ssm-cli  get-instance-information  | ConvertFrom-Json
        }
        Windows{
            $ssm_reg_stat= & "${env:programfiles}\Amazon\SSM\ssm-cli.exe" get-instance-information | ConvertFrom-Json
        }
    }
    
    return $ssm_reg_stat
    }


function getting_ssm_reg_code
    {
   
    $finalgetwsidandactivurl = $wsfbaseurl + "getactivation?hostname=" + $hostnamefqdn + "&username=" + $username + "&region=" + $wsregion + "&ipadd=" + $ipadd
    write-log -Message " final get ws and activation URL is $finalgetwsidandactivurl " -path $logfile -level INFO
    $ssmRegistration = Invoke-WebRequest -Uri "$finalgetwsidandactivurl" -UseBasicParsing -SkipHttpErrorCheck 
    write-log -Message " Got the registration code as $ssmRegistration " -path $logfile -level INFO
    if ($ssmRegistration.StatusCode -eq "200")
        {
            if ((ConvertFrom-Json $ssmRegistration).activationcode -eq "NULL")
                { write-log -Message " Got the registration code as $ssmRegistration " -path $logfile -level ERROR
                  exit
                 }
            return ConvertFrom-Json $ssmRegistration
        }
    else {
        write-log -Message " issue getting activation" -path $logfile -level Error
        exit}                       
    
    }
function ssmclean
{
    Param(
        [parameter(Mandatory=$true)]
        [String]
        $BaseOS
        )
    write-log -Message "starting old ssm cleanup " -path $logfile -level INFO
    switch ($BaseOS)
    {
        linux{
            yum erase amazon-ssm-agent -q -y
            rm -rf /var/lib/amazon/ssm
        }
        Windows{
            $software = "Amazon SSM Agent"
            $paths = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', 'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
            Get-ChildItem $paths |
                Where-Object{ $_.GetValue('DisplayName') -match "$software" } |
                ForEach-Object{
                    $uninstallString = $_.GetValue('UninstallString') + ' /quiet /norestart'
                    write-log -Message "$uninstallString " -path $logfile -level INFO
                    & "C:\Windows\SYSTEM32\cmd.exe" /c $uninstallString
                }
            Remove-Item -path C:\ProgramData\Amazon\SSM -Recurse -Force
            Remove-Item -path "C:\Program Files\Amazon\SSM" -Recurse -Force
        }
    }
    

}

function installssm 
    {
    Param(
    [parameter(Mandatory=$true)]
    $username
    )
    $ssmRegistration = ""
    write-log -Message "starting SSM install" -path $logfile -level INFO
    $ssmRegistration = getting_ssm_reg_code $username
    write-log -Message "registration code is $ssmRegistration" -path $logfile -level INFO
    $activationcode=$ssmRegistration.activationcode
    $activationid= $ssmRegistration.ActivationId
    $global:workspaceID = $ssmRegistration.wsid
    $global:DirectoryID = $ssmRegistration.directoryid
    write-log -Message " directory id is $DirectoryID " -path $logfile -level INFO
    write-log -Message "activationcode is $activationcode and activationID is $activationid" -path $logfile -level INFO
    switch ($BaseOS)
    {
        linux{
            $dir = "/tmp/ssm"
            New-Item -ItemType directory -Path $dir -Force
            $downloadfile = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm"
            Set-Location $dir
            yum install -y $downloadfile
            systemctl stop amazon-ssm-agent
            amazon-ssm-agent -register -code  $activationcode -id $activationid -region $baseregion
            systemctl start amazon-ssm-agent
            }
        Windows{
            if ((Get-CimInstance -ClassName win32_OperatingSystem | Select-Object osarchitecture).osarchitecture -eq "64-bit")
                {$downloadfile = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe"}
            else
                {$downloadfile = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_386/AmazonSSMAgentSetup.exe"}
                        
            $dir = $env:TEMP + "\ssm"
            New-Item -ItemType directory -Path $dir -Force
            Set-Location $dir
            (New-Object System.Net.WebClient).DownloadFile($downloadfile, $dir + "\AmazonSSMAgentSetup.exe")
            Start-Process .\AmazonSSMAgentSetup.exe -ArgumentList @("/quiet", "/log", "install.log","ALLOWEC2INSTALL=YES", "CODE=$activationcode", "ID=$activationid", "REGION=$baseregion") -Wait
            }

    }
    sleep(20)
    $managedinstid=ssmregcheck($BaseOS)
    $global:mid= $managedinstid.'instance-id'
    write-log -Message " Found the MI ID from SSM as $mid " -path $logfile -level INFO
    addadgrouptags
    }  
    
#Starting the main script
#Declaring starting variables
$baseregion = "us-east-1"
$WorkspaceID =""
$username=""
$ssmRegistration = ""
if ($IsLinux) {
    Set-Variable -Name "BaseOS" -Value ("Linux") -Scope global
                }
elseif ($IsMacOS) {
    Set-Variable -Name "BaseOS" -Value ("MacOS") -Scope global
                    }
elseif ( (Get-ChildItem -Path Env:OS).Value -eq "WINDOWS_NT") {
    Set-Variable -Name "BaseOS" -Value ("Windows") -Scope global
                    }
else {exit}
$LogDate = Get-Date -Format yyyy_MM_dd
switch ($BaseOS)
        {
            Linux
            {   
                $global:logbase = "/var/temp/ssm"
                $logfile=  $logbase + "/ssmcheckscript" + $LogDate + ".log"
                logrotate
                write-log -Message 'Starting the script to install SSM on the workspace as a managed instance' -path $logfile
                write-log -Message "The OS is identified as $BaseOS " -path $logfile
                $domainname= realm list -n
                write-log -Message "Domain name is $domainname" -path $logfile -level INFO
                Set-Variable -Name "domainname" -Value ($domainname) -Scope global
                $hostname=hostname
                Set-Variable -Name "hostname" -Value ($hostname) -Scope global
                write-log -Message "Computer host name is $hostname" -path $logfile -level INFO
                $username = ls -l /home | grep "drwxr-xr-x" |awk ‘{print $NF}’
                write-log -Message "username is $username" -path $logfile -level INFO
                Set-Variable -Name "username" -Value ($username) -Scope global
                $hostnamefqdn = hostname --fqdn 
                write-log -Message "hostnamefqdn is $hostnamefqdn" -path $logfile -level INFO
                Set-Variable -Name "hostnamefqdn" -Value ($hostnamefqdn) -Scope global
                $ipadd = hostname -i
                Set-Variable -Name "ipadd" -Value ($ipadd) -Scope global
            }
            Windows
            {   
                $global:logbase = "C:\windows\temp\ssmlog"
                $logfile=  $logbase + "\ssmcheckscript" + $LogDate + ".log"
                logrotate
                write-log -Message ' Starting the script to install SSM on the workspace as a managed instance' -path $logfile
                write-log -Message "The OS is identified as $BaseOS " -path $logfile
                $domainname=(Get-CimInstance -ClassName Win32_Computersystem).Domain 
                write-log -Message "Domain name is $domainname" -path $logfile -level INFO
                Set-Variable -Name "domainname" -Value ($domainname) -Scope global
                $hostname=hostname
                Set-Variable -Name "hostname" -Value ($hostname) -Scope global
                write-log -Message "Computer host name is $hostname" -path $logfile -level INFO
                $username = (Get-ChildItem -Path D:\users).name
                write-log -Message "username is $username" -path $logfile -level INFO
                Set-Variable -Name "username" -Value ($username) -Scope global
                $hostnamefqdn = ([System.Net.Dns]::GetHostByName($env:computerName)).HostName
                write-log -Message "hostnamefqdn is $hostnamefqdn" -path $logfile -level INFO
                Set-Variable -Name "hostnamefqdn" -Value ($hostnamefqdn) -Scope global
                $getint = get-netroute | where-object {$_.DestinationPrefix -eq "0.0.0.0/0" -and $_.RouteMetric -eq "0"} | Select-Object InterfaceIndex
                $ipadd = get-netipaddress -InterfaceIndex $getint.InterfaceIndex
                Set-Variable -Name "ipadd" -Value ($ipadd) -Scope global
            }
            MacOS
            {
                exit
            }
            Default
            { exit}
        }
$findregion = try {Invoke-WebRequest -Uri "http://169.254.169.254/latest/meta-data/placement/region"-UseBasicParsing -ErrorAction SilentlyContinue}
            catch [System.Net.WebException] 
            { 
            Write-log -Message "An exception was caught: $($_.Exception.Message) $($_.Exception.Response)" -path $logfile -Level ERROR
            exit
            }
write-log -Message "workspace region is $findregion.Content" -path $logfile -level INFO
Set-Variable -Name "wsregion" -Value ($findregion.Content) -Scope global
if (!$domainname)
   { 
    write-log -Message "Machine is not joined to domain, so exiting" -path $logfile -level INFO
    exit
    }
 else 
       {
        write-log -Message "Machine is joined to domain, so continuing" -path $logfile -level INFO
           if (!$username)
             {
                write-log -Message "username is empty, so exiting" -path $logfile -level INFO
                exit
             } 
            else 
                {
                 write-log -Message "username is not empty so continuing" -path $logfile -level INFO        
                 $servicesstatus=checkssmservice($BaseOS)
                  if ( $servicesstatus -eq "running")
                  {
                    write-log -Message "SSM service is running" -path $logfile -level INFO
                    if (!($managedinstid=ssmregcheck($BaseOS)))
                        {
                            write-log -Message "the instance is not a managed instance, but service is running" -path $logfile -level INFO
                            
                            ssmclean($BaseOS)
                            installssm($BaseOS,$username)
                        }
                    else
                        {
                            write-log -Message "the Managed instance ID returned is $managedinstid.instance-id" -path $logfile -level INFO
                            if ($managedinstid.'instance-id'.startswith("mi-"))
                            {
                            $finalmistatusurl=$wsfbaseurl + "checkmistat/?wsid=" + $managedinstid.'instance-id' + "&hostname=" + $hostnamefqdn 
                            write-log -Message "the final checkmistatus url is  $finalmistatusurl " -path $logfile -level INFO
                            write-log -Message "the instance is a managed instance  $managedinstid " -path $logfile -level INFO
                            $getmistatus= Invoke-WebRequest -Uri $finalmistatusurl -UseBasicParsing -SkipHttpErrorCheck | ConvertFrom-Json
                            write-log -Message " managed instance ping status $getmistatus" -path $logfile -level INFO 
                            switch ($getmistatus.pingstatus)
                            {
                                "connected" {
                                write-log -Message "The machine is online and managed. Northing to do " -path $logfile -level INFO
                                addadgrouptags($managedinstid.'instance-id')}
                                "not_found" {
                                write-log -Message "SSM is running locally but not present in found in SSM console" -path $logfile -level INFO
                                ssmclean($BaseOS)
                                installssm($username)}
                                "notconnected" {
                                
                                write-log -Message "The machine is not online in SSM, so going to reinstalling the service" -path $logfile -level INFO

                                ssmclean($BaseOS)
                                installssm($username) }
                                "error"{
                                    write-log -Message "Error calling the SSM API to check the managed instance" -path $logfile -level INFO
                                    exit
                                }
                                Default{write-log -Message "Issue getting Managed instance status from API" -path $logfile -level Error}
                            }
                            } 
                            else
                                {
                                    write-log -Message "SSM service is running and doesnt start with MI" -path $logfile -level INFO
                                    ssmclean($BaseOS)
                                    installssm($username)}
                                
                                }
                        }
                        else
                        {
                            ssmclean($BaseOS)
                            installssm $username
                        }
                    
                }

        }