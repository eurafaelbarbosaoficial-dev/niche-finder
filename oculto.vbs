' Roda um .bat do Niche Finder SEM abrir janela (as tarefas do Windows chamam este arquivo).
' Uso: wscript.exe oculto.vbs rodar.bat
Set sh = CreateObject("WScript.Shell")
pasta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = pasta
sh.Run "cmd.exe /c """ & pasta & "\" & WScript.Arguments(0) & """", 0, True
