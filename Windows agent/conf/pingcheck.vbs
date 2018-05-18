'Use a remote computer to ping another remote computer

Option Explicit 
'Change the SourceServer and RemoteServer Strings below to servernames or IP addresses for you.
'wscript.Echo RemotePing("SourceComputer", "DestinationComputer")
'wscript.Echo RemotePing(".", WScript.Arguments(0))
Ping(WScript.Arguments(0))

Function Ping(strHost)
    Dim oPing, oRetStatus, bReturn
    Set oPing = GetObject("winmgmts:{impersonationLevel=impersonate}").ExecQuery("select * from Win32_PingStatus where address='" & strHost & "'")
 
    For Each oRetStatus In oPing
        If IsNull(oRetStatus.StatusCode) Or oRetStatus.StatusCode <> 0 Then
            bReturn = False
 
             'WScript.Echo "Status code is " & oRetStatus.StatusCode
             WScript.Echo -1
        Else
            bReturn = True
              
             ' UNCOMMENT BELOW WHAT RESPONSE YOU WANT RETURNED eg oRetStatus.ResponseTime
             'Wscript.Echo oRetStatus.BufferSize
             Wscript.Echo oRetStatus.ResponseTime
             'Wscript.Echo oRetStatus.ResponseTimeToLive
		 
		 
        End If
        Set oRetStatus = Nothing
    Next
    Set oPing = Nothing
 
    Ping = bReturn
End Function