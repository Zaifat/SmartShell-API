<?php
$login = "79525554445"; // логин smartshell
$password = "password"; // пароль smartshell
$id = "1620"; // узнать свой ид клуба http://АДРЕС/SmartShell_Tasmota.php?d=clubs

// пример, названия должны совпадать с названиями в smartshell
//$Tasmota["PC 1"] =["192.168.2.10"];
//$Tasmota["PC 2"] = ["192.168.2.11"];
//$Tasmota["PC 3"] = ["192.168.2.13:3232"];

$Tasmota[""] = [""];





if(isset($_GET['d']) AND $_GET['d'] == "clubs") {

    $clubs = GetClubs($login,$password);

    echo '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>Список ваших клубов</title></head><body>';
    echo "<h1>Список ваших клубов</h1><br><br>";
    foreach($clubs['data']['userClubs'] as $club) {
		echo "<h3>id клуба: ".$club['id']." Название клуба: ".$club['name']."</h3>";
    }
    echo '</body></html>';

}




if(isset($_GET['d']) AND $_GET['d'] == "check") {

	ini_set('max_execution_time', 900);
	TokenUP($login,$password,$id);
	require 'token.php';
			
    for ($cycle = 1; $cycle <= 4; $cycle++) {
        GetCheck($token,$Tasmota);
        sleep(15);
    }
}




function GetCheck($token,$Tasmota) {
    $pclist = GetBox($token);
    foreach($pclist['data']['hostGroups'] as $hostGroups) {
        foreach($hostGroups['hosts'] as $pc) {
            if(isset($Tasmota[$pc['alias']])) {
				$TasmotaS = GetTasmota($Tasmota[$pc['alias']][0], "Power%20TOGGLE");
                if(isset($pc['client_sessions'][0]) AND $TasmotaS["power"] == "off") {
                    GetTasmota($Tasmota[$pc['alias']][0], "Power%20On");
                    Logs("Получена команда для ".$pc['alias']." на включение");
                } elseif(!isset($pc['client_sessions'][0]) AND $TasmotaS["power"] == "on") {
                    GetTasmota($Tasmota[$pc['alias']][0], "Power%20off");
                    Logs("Получена команда для ".$pc['alias']." на отключение");
                }
				
            }
        }
    }
}



function GetTasmota($url,$tip) {

    $url = "http://".$url."/cm?cmnd=".$tip;
    $headers = [
        'Content-Type: application/json',
    ];

    $Tasmota = GetCurl($url,$headers,,"Переключение");

    return $Tasmota;
}


function Logs($log, $die = 0) {
    $data = date('Y-m-d H:i:s')." ";
    $data .= $log;
    $data .= "\r\n";

    file_put_contents('log.txt', $data, FILE_APPEND);
    if($die == 1) die($log);
}



function GetUsers($token) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":"clients","variables":{"input":{"q":"","sort":{"field":"last_client_activity","direction":"ASC"}},"first":999,"page":1},"query":"query clients($input: ClientsInput, $first: Int, $page: Int) {\n  clients(input: $input, first: $first, page: $page) {\n    paginatorInfo {\n      count\n      currentPage\n      lastPage\n    }\n    data {\n      id\n      login\n      phone\n      deposit\n      last_client_activity\n      dob\n      first_name\n      last_name\n      middle_name\n      roles {\n        id\n        alias\n        title\n      }\n      last_comment {\n        text\n      }\n      total_hours\n      created_at\n      banned_at\n      disabled_at\n      user_discount\n    }\n  }\n}\n"}';
        
    $users = GetCurl($url,$headers,$post_fields,"Получение юзеров");

    if(!isset($users['data']['clients']['data'][0])) {
        Logs("проблемы с получением cписка юзеров SmartShell", 1);
    }

    return $users;
}


function GetBox($token) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":"hostGroups","variables":{},"query":"query hostGroups {\n  hostGroups {\n    id\n    title\n    hosts {\n      id\n      group_id\n      position\n      alias\n      last_online\n      in_service\n      coord_x\n      coord_y\n      info {\n        processor\n        ram\n        video\n        disc\n        shell_version\n      }\n      counters {\n        active_window\n        disk_status {\n          letter\n          total\n          used\n        }\n      }\n      sessions {\n        user {\n          id\n          login\n          deposit\n        }\n      }\n      client_sessions {\n        id\n        client {\n          id\n          login\n          deposit\n        }\n        started_at\n        finished_at\n        duration\n        elapsed\n        seances {\n          id\n          status\n          tariff {\n            id\n            title\n            per_minute\n            has_fixed_finish_time\n          }\n        }\n      }\n      comment\n    }\n  }\n}\n"}';
        
    $box = GetCurl($url,$headers,$post_fields,"Получение компов");
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
        
    $clubs = GetCurl($url,$headers,$post_fields,"Получение клубов");
    if(!isset($clubs['data']['userClubs']['0'])) {
        Logs("проблемы с получением списка клубов SmartShell", 1);
    }

    return $clubs;

}


function TokenUP($login,$password,$id) {
  
	if (file_exists("token.php")) {
		$ftime = (time() - filectime("token.php"));
	} 
	
	if($ftime > 85000 OR !file_exists("token.php")) {	
		$url = "https://billing.smartshell.gg/api/graphql";
		$headers = [
			'Content-Type: application/json',
		];
		$post_fields = '{"operationName":"login","variables":{"input":{"login":"'.$login.'","password":"'.$password.'","company_id":'.$id.'}},"query":"mutation login($input: LoginInput!) {\n  login(input: $input) {\n    access_token\n  }\n}\n"}';
				
		$token = GetCurl($url,$headers,$post_fields,"Получение токена");
		if(!isset($token['data']['login']['access_token']) OR $token['data']['login']['access_token'] == '') {
			Logs("проблемы с получением Токена SmartShell", 1);
		}
			
		file_put_contents('token.php', '<?php $token = "'.$token['data']['login']['access_token'].'";');

		if (file_exists("token.php")) {
			Logs("Токен обновлен!"); 
		} else {  
			Logs("Проблемы с созданием файла token.php",1); 
		}
	}

}



function GetCurl($url,$headers,$post_fields = null,$tip = null) {

    $ch = curl_init();
    $timeout = 15;
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
        Logs("Проблемы с curl на этапе ".$tip." Ошибка:".curl_error($ch), 1);
    }

    curl_close($ch);
  

    $data = json_decode($data, true);
    return  $data;
}
