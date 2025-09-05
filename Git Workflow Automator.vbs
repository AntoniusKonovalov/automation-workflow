Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory
WshShell.CurrentDirectory = strScriptPath

' Check if main.py exists
If Not objFSO.FileExists(strScriptPath & "\main.py") Then
    MsgBox "❌ Error: main.py not found!" & vbCrLf & "Make sure you're running this from the correct directory.", vbCritical, "Git Workflow Automator"
    WScript.Quit 1
End If

' Check if components folder exists
If Not objFSO.FolderExists(strScriptPath & "\components") Then
    MsgBox "❌ Error: components folder not found!" & vbCrLf & "The modular components are missing.", vbCritical, "Git Workflow Automator"
    WScript.Quit 1
End If

' Show startup message (commented out - no popup needed)
' MsgBox "🚀 Starting Git Workflow Automator..." & vbCrLf & "Modular Edition v2.0", vbInformation, "Git Workflow Automator"

' Run the Python application (0 = hidden console, 1 = visible console)
Dim result
result = WshShell.Run("python main.py", 0, True)

If result <> 0 Then
    MsgBox "❌ Error occurred while running the application!" & vbCrLf & vbCrLf & _
           "Possible issues:" & vbCrLf & _
           "• Python is not installed or not in PATH" & vbCrLf & _
           "• Missing required Python packages" & vbCrLf & _
           "• Import errors in components" & vbCrLf & vbCrLf & _
           "Try running 'python main.py' manually from command prompt.", vbCritical, "Git Workflow Automator"
End If