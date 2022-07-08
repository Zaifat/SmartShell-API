<?php
$login = "79525554445"; // логин smartshell
$password = "password"; // пароль smartshell
$id = "1620"; // узнать свой ид клуба http://АДРЕС/SmartShell_Alisa.php?d=clubs
$ya_token = "токен"; // как получить токен смотрите https://www.youtube.com/watch?v=zHcx-TD4ZPU





if (!file_exists("token.php")) {
    file_put_contents('token.php', '');
}

require 'token.php';

if(isset($_GET['d'])) {

    if($_GET['d'] == "check") {
            
        for ($cycle = 1; $cycle <= 4; $cycle++) {
            GetCheck($token,$ya_token);
            sleep(15);
        }

    }

    if($_GET['d'] == "token") {

        UpToken($login,$password,$id);

    }

    if($_GET['d'] == "clubs") {
        
        UpToken($login,$password,$id);
        require 'token.php';

        $clubs = GetClubs($login,$password);

        echo '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>Список ваших клубов</title></head><body>';
        echo "<h1>Список ваших клубов</h1><br><br>";
        foreach($clubs['data']['userClubs'] as $club) {
            echo "<h3>id клуба: ".$club['id']." Название клуба: ".$club['name']."</h3>";
        }
        echo '</body></html>';

    }

}




function UpToken($login,$password,$id) {

    $token = GetToken($login,$password,$id);
    file_put_contents('token.php', '<?php $token = "'.$token['data']['login']['access_token'].'";');
    
}


function GetCheck($token,$ya_token) {

    $pclist = GetBox($token);
    $ya = YaApiDev($ya_token);

    foreach($pclist['data']['hostGroups'] as $hostGroups) {
        foreach($hostGroups['hosts'] as $pc) {
            if(isset($ya[$pc['alias']])) {
                if(isset($pc['client_sessions'][0]) AND $ya[$pc['alias']]['status'] != 1) {
                    YaApiDevEdd($ya_token, $ya[$pc['alias']]['id'], "true");
                    Logs("Получена команда для ".$pc['alias']." на включение");
                } elseif(!isset($pc['client_sessions'][0]) AND $ya[$pc['alias']]['status'] != "") {
                    YaApiDevEdd($ya_token, $ya[$pc['alias']]['id'], "false");
                    Logs("Получена команда для ".$pc['alias']." на отключение");
                }
            }
        }
    }
    
}


function Logs($log, $die = 0) {
    $data = date('Y-m-d H:i:s')." ";
    $data .= $log;
    $data .= "\r\n";

    file_put_contents('log.txt', $data, FILE_APPEND);
    if($die == 1) die($log);
}

function YaApiDevEdd($token, $id, $v) {

    $url = "https://api.iot.yandex.net/v1.0/devices/actions";

    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];

    $post_fields = '{
    "devices": [
        {
            "id": "'.$id.'",
            "actions": [
                {
                    "type": "devices.capabilities.on_off",
                    "state": {
                        "instance": "on",
                        "value": '.$v.'
                    }
                }
            ]
        }
    ]
}';

    $add = GetCurl($url,$headers,$post_fields);
    if(!isset($add['status']) OR $add['status'] != 'ok') {
        Logs("проблемы с включением / отключением устройства", 1);
    }

    return $add;

}



function YaApiDev($token) {
  
    $url = "https://api.iot.yandex.net/v1.0/user/info";
    $headers = [
        'authorization: Bearer '.$token,
    ];

    $ya = GetCurl($url,$headers);

    if(!isset($ya['status']) OR $ya['status'] != 'ok') {
        Logs("проблемы с получением списка устройства Яндекс умный дом", 1);
    }

    foreach($ya['devices'] as $d) {
        $ar[$d['name']]['id'] = $d['id'];
        $ar[$d['name']]['type'] = $d['capabilities']['0']['type'];
        $ar[$d['name']]['status'] = $d['capabilities']['0']['state']['value'];
    }

    return  $ar;

}


function GetBox($token) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":"hostGroups","variables":{},"query":"query hostGroups {\n  hostGroups {\n    id\n    title\n    hosts {\n      id\n      group_id\n      position\n      alias\n      last_online\n      in_service\n      coord_x\n      coord_y\n      info {\n        processor\n        ram\n        video\n        disc\n        shell_version\n      }\n      counters {\n        active_window\n        disk_status {\n          letter\n          total\n          used\n        }\n      }\n      sessions {\n        user {\n          id\n          login\n          deposit\n        }\n      }\n      client_sessions {\n        id\n        client {\n          id\n          login\n          deposit\n        }\n        started_at\n        finished_at\n        duration\n        elapsed\n        seances {\n          id\n          status\n          tariff {\n            id\n            title\n            per_minute\n            has_fixed_finish_time\n          }\n        }\n      }\n      comment\n    }\n  }\n}\n"}';
        
    $box = GetCurl($url,$headers,$post_fields);
    if(!isset($box['data']['hostGroups'][0])) {
        Logs("проблемы с получением cписка компьютеров в SmartShell", 1);
    }

    return $box;
}

function GetClubs($login,$password) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'Content-Type: application/json',
    ];
    
    $post_fields = '{"operationName":"userClubs","variables":{"input":{"login":"'.$login.'","password":"'.$password.'"}},"query":"query userClubs($input: UserClubsInput) {\n  userClubs(input: $input) {\n    id\n    name\n    address\n    workShiftStatus\n    permitted\n    operatorFirstName\n    operatorLastName\n  }\n}\n"}';
        
    $clubs = GetCurl($url,$headers,$post_fields);
    if(!isset($clubs['data']['userClubs']['0'])) {
        Logs("проблемы с получением списка клубов SmartShell", 1);
    }

    return $clubs;

}


function GetToken($login,$password,$id) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":"login","variables":{"input":{"login":"'.$login.'","password":"'.$password.'","company_id":'.$id.'}},"query":"mutation login($input: LoginInput!) {\n  login(input: $input) {\n    access_token\n  }\n}\n"}';
        
    $token = GetCurl($url,$headers,$post_fields);
    if(!isset($token['data']['login']['access_token']) OR $token['data']['login']['access_token'] == '') {
        Logs("проблемы с получением Токена SmartShell", 1);
    }

    return $token;

}



function GetCurl($url,$headers,$post_fields = null) {

    $ch = curl_init();
    $timeout = 5;
    curl_setopt($ch, CURLOPT_URL, $url);

    if (!empty($post_fields)) {

        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_fields);
    }

    if (!empty($headers))
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 1);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, $timeout);
    $data = curl_exec($ch);

    if (curl_errno($ch)) {
        Logs("Проблемы с curl ".curl_error($ch), 1);
    }

    curl_close($ch);
  

    $data = json_decode($data, true);
    return  $data;
}







