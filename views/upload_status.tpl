<html>
<head>
    <title>ACRL :: Assetto Corsa Racing League :: Upload Results</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <!-- <link rel="stylesheet" type="text/css" href=".css"> -->
</head>
<body>
    %if server_cfg_written:
        Server configuration <span style="color:green;">written to disk</span>.<br />
    %else:
        Server configuration <span style="color:red;">write unsuccessful</span>.<br />
    %end
    %if entry_list_generated:
        Entry list <span style="color:green;">created successfully</span>.<br />
    %else:
        Entry list <span style="color:green;">generation failed</span>.
    %end
</body>
</html>