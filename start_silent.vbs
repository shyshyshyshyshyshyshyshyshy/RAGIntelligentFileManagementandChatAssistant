' start_silent.vbs
Set WshShell = CreateObject("WScript.Shell")

' 切换到脚本所在目录
Set fso = CreateObject("Scripting.FileSystemObject")
currentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDirectory

' 静默启动文件打开服务
WshShell.Run "pythonw file_opener_api.py", 0, False

' 等待2秒确保服务启动
WScript.Sleep 2000

' 打开浏览器访问页面
WshShell.Run "http://localhost:5002/", 1, False

WScript.Echo "Service started. Please check browser window."