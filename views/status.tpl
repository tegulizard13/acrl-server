<html>
<head>
    <title>ACRL :: Assetto Corsa Racing League :: Server Status</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <!-- <link rel="stylesheet" type="text/css" href=".css"> -->
</head>
<body>
    You're seeing this, so the Amazon EC2 Instance is on!<br />
    %if server_running:
        The server is <span style="color:green;">running</span>.<br />
    %else:
        The server is <span style="color:red;">not running</span>.<br />
    %end
</body>
</html>