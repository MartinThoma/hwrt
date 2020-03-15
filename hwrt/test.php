<?php
header("Access-Control-Allow-Origin: *");
// $output = shell_exec('python test.py');
// echo $output;

if(isset($_GET['heartbeat'])){
    echo $_GET['heartbeat'];
} elseif(isset($_POST['classify'])) {
    $postdata = http_build_query(
        array(
            'classify' => $_POST['classify'],
            'secret' => $_POST['secret']
        )
    );

    $opts = array('http' =>
        array(
            'method'  => 'POST',
            'header'  => 'Content-type: application/x-www-form-urlencoded',
            'content' => $postdata
        )
    );

    $context  = stream_context_create($opts);

    $homepage = file_get_contents('http://localhost:5000/worker', false, $context);
    echo $homepage;
} else {
    $opts = array('http' =>
        array(
            'method'  => 'GET'
        )
    );

    $context  = stream_context_create($opts);

    $homepage = file_get_contents('http://localhost:5000/worker', false, $context);
    echo $homepage;
}
?>
