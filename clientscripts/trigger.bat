del c:\programdata\ssm_script\finalmultiplatformloginscript.ps1 
set myDIR=c:\programdata\ssm_script
IF not exist %myDIR% (mkdir %myDIR%)
xcopy "\\Domainname\SysVol\domainname\scripts\SSM_install\finalmultiplatformloginscript.ps1" C:\ProgramData\ssm_script\  /z /y
pause