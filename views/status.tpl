<html>
<head>
    <title>ACRL :: Assetto Corsa Racing League :: Server Status</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <!-- <link rel="stylesheet" type="text/css" href=".css"> -->
</head>
<body>
    You're seeing this, so the Amazon EC2 Instance is on!<br />
    <!-- Game server status -->
    %if server_running:
        The server is <span style="color:green;">running</span>.<br />
    %else:
        The server is <span style="color:red;">not running</span>.<br />
    %end
    <br />
    <span style="font-weight:bold;">Server Actions:</span><br />
    <!-- start/stop/restart game server-->
    %if not server_running:
        <form action="/control" method="post">
            <button type="submit" name="action" value="start">Start server</button>
        </form>
    %else:
        <form action="/control" method="post">
            <button type="submit" name="action" value="stop">Stop server</button>
            <button type="submit" name="action" value="restart">Restart server</button>
        </form>
    %end
    <!-- upload configurations -->
    <br />
    <form action="/upload" method="post" enctype="multipart/form-data">
        <!-- Check-in sheet url: <input type="text" name="check_in_sheet_url" /><br /> -->
        Entry List: <input type="file" name="entry_list" /><br />
        Server Configuration: <input type="file" name="server_cfg" /><br />
        <input type="submit" value="Submit" />
    </form>
</body>
</html>