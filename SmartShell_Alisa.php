<?php
$login = "799999999"; // логин smartshell
$password = "pass"; // пароль smartshell
$id = "9999"; // как узнать свой ид клуба смотри скриншот https://ibb.co/fC2m0gD
$ya_token = "token"; // как получить токен смотрите https://www.youtube.com/watch?v=zHcx-TD4ZPU




if(isset($_GET['d']) AND $_GET['d'] == "check") {

	ini_set('max_execution_time', 120);

    if (file_exists("token.php")) {
        require 'token.php';
    } else {
        TokenUP($login,$password,$id);
    }

    for ($cycle = 1; $cycle <= 4; $cycle++) {
        GetCheck($token, $ya_token, $login, $password, $id, $cycle);
        sleep(15);
    }

}


if(isset($_GET['d']) AND $_GET['d'] == "debug") {

	ini_set('max_execution_time', 120);

    if (file_exists("token.php")) {
        require 'token.php';
    } else {
        TokenUP($login,$password,$id);
    }

    $url = "https://api.iot.yandex.net/v1.0/user/info";
    $headers = [
        'authorization: Bearer '.$ya_token,
    ];

    $ya = GetCurl($url,$headers);

    print_r($ya);


}



function GetCheck($token, $ya_token, $login, $password, $id, $cycle) {

    // Парсим хосты с карты смартшелла
    $pclist = GetBox($token, $login, $password, $id);
    // Парсим хосты из яндекс алисы
    $yas = YaApiDev($ya_token);


    foreach($yas as $alias => $ya) {
        
        // Проверка, есть ли хосты из Алисы в смартшелле, если нет - создаем их
        if(isset($pclist[$alias])) {

            // Проверка, создан ли сайт с токеном доступа к хосту, если нет - выводим сообщение
            if(file_exists($ya['external_id'])) {
                if($cycle%2 != 0) {
                    $tokenPc = file_get_contents($ya['external_id']);
                    BoxStatus($alias, $tokenPc);
                }
            } else {
                Logs("Для хоста ".$alias." не создан файл с токеном доступа, удалите хост с карты клуба, чтоб он был создан автоматически скриптом");
            }

            // Сравниваем статусы розеток и статус хоста в смартшелл, если есть несовпадение - исправляем это
            if($pclist[$alias]['status'] == 1 AND $ya['status'] != 1) {
                YaApiDevEdit($ya_token, $ya['id'], "true");
                Logs("Получена команда для ".$alias." на включение");
            } elseif($pclist[$alias]['status'] == 0 AND $ya['status'] == 1) {
                YaApiDevEdit($ya_token, $ya['id'], "false");
                Logs("Получена команда для ".$alias." на отключение");
            }

        } else {
        
            BoxAdd($token, $alias, $ya['external_id']);

        }
    }
    
}



function YaApiDevEdit($token, $id, $v) {

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

        $d['external_id'] = preg_replace("/[^a-zA-Z0-9]/", "", $d['external_id']);
        $ar[$d['name']]['external_id'] = $d['external_id'];
    }
    return  $ar;

}



function GetBox($token, $login, $password, $id) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":"hostGroups","variables":{},"query":"query hostGroups {hostGroups {hosts {id group_id alias client_sessions {id}}}}"}';
        
    $box = GetCurl($url,$headers,$post_fields);
    $pc = null;

    if(!isset($box['data']['hostGroups'][0])) {
		if(isset($box['errors'][0])) {
			TokenUP($login,$password,$id);
		} else {
			Logs("проблемы с получением cписка компьютеров в SmartShell", 1);
		}
    } else {
        foreach($box['data']['hostGroups'] as $hostGroups) {
            foreach($hostGroups['hosts'] as $pcs) {

                $pc[$pcs['alias']]['id'] = $pcs['id'];
                $pc[$pcs['alias']]['group_id'] = $pcs['group_id'];

                if(!isset($pcs['client_sessions'][0])) {
                    $pc[$pcs['alias']]['status'] = 0;
                } else {
                    $pc[$pcs['alias']]['status'] = 1;
                }

            }
        }
    }


    return $pc;
}


function GetClubs($login,$password) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'Content-Type: application/json',
    ];
    
    $post_fields = '{"operationName":"userClubs","variables":{"input":{"login":"'.$login.'","password":"'.$password.'"}},"query":"query userClubs($input: UserClubsInput) {userClubs(input: $input) {id name}}"}';
        
    $clubs = GetCurl($url,$headers,$post_fields);
    if(!isset($clubs['data']['userClubs']['0'])) {
        Logs("проблемы с получением списка клубов SmartShell", 1);
    }

    return $clubs;

}


function GetCategory($token) {
  
    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    
    $post_fields = '{ "operationName": "hostGroups","variables": {},"query": "query hostGroups {hostGroups {id title}}"}';
        
    $category = GetCurl($url,$headers,$post_fields);
    if(!isset($category['data']['hostGroups']['0'])) {
        Logs("проблемы с получением категорий SmartShell", 1);
    }

    return $category;

}


function BoxAdd($token, $alias, $external_id) {

    $mac = "FF-FF-".mb_substr(time(), -8, 2)."-".mb_substr(time(), -6, 2)."-".mb_substr(time(), -4, 2)."-".mb_substr(time(), -2, 2);
  
    $cat = GetCategory($token);

    $url = "https://billing.smartshell.gg/api/graphql";
    $headers = [
        'authorization: Bearer '.$token,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":null,"variables":{},"query":"mutation{\n registerHost(input: {group_id: '.$cat['data']['hostGroups']['0']['id'].', mac_addr: \"'.$mac.'\", dns_name: \"aliska\", alias: \"'.$alias.'\"})}\n"}';
        
    $box = GetCurl($url,$headers,$post_fields);

    if(isset($box['data']['registerHost'])) {

		if(file_exists($external_id)){
			if(unlink($external_id)) {
				//..
			} else {
				Logs("проблемы с удалением файла с ключом доступа к хосту ".$external_id, 1);
			}
		}


	    file_put_contents($external_id, $box['data']['registerHost'], FILE_APPEND | LOCK_EX);
        Logs("На карту клуба добавлен новый хост ".$alias, 0);

    } else {
        Logs("проблемы с добавление хоста", 1);
    }

}



function BoxStatus($alias, $tokenPc) {

    $url = "https://host.smartshell.gg/api/graphql";
    $headers = [
        'X-Host:'.$tokenPc,
        'Content-Type: application/json',
    ];
    $post_fields = '{"operationName":null,"variables":{},"query":"mutation{ updateHostState(input: {cpu_temp: 0, disk_temp: 0, disk_status: {letter: \"NA\", total: 0, used:0}, active_window: \"NA\"}){client_session{id}}}"}';
    $box = GetCurl($url,$headers,$post_fields);

    // если не прошло положительного статуса, делаем startHostSession и повторяем
    if(!isset($box['data']['updateHostState'])) {
        if(isset($box['errors'][0]['message']) AND $box['errors'][0]['message'] == "active host session not found") {

            $post_fields = '{"operationName":null,"variables":{},"query":"mutation{ startHostSession(input: {processor: \"N/A\", ram: \"N/A\", video: \"N/A\", disc: \"N/A\", shell_version: \"Smart Socket v 0.1\"}){host_id}}"}';
            $box = GetCurl($url,$headers,$post_fields);

            if(isset($box['data']['startHostSession']['host_id'])) {
                BoxStatus($alias, $tokenPc);
            } else {
                Logs("Проблемы доступа к хосту ".$alias, 0);
            }

        } else {
                Logs("Проблемы обновления статуса хоста ".$alias, 0);
        }

    }

}



function TokenUP($login,$password,$id) {
  
		if(file_exists('token.php')){
			if(unlink('token.php')) {
				//..
			} else {
				Logs("проблемы с удалением файла token.php", 1);
			}
		}
		
		$url = "https://billing.smartshell.gg/api/graphql";
		$headers = [
			'Content-Type: application/json',
		];
		$post_fields = '{"operationName":"login","variables":{"input":{"login":"'.$login.'","password":"'.$password.'","company_id":'.$id.'}},"query":"mutation login($input: LoginInput!) {\n  login(input: $input) {\n    access_token\n  }\n}\n"}';
				
		$token = GetCurl($url,$headers,$post_fields);
		if(!isset($token['data']['login']['access_token']) OR $token['data']['login']['access_token'] == '') {
			Logs("проблемы с получением Токена SmartShell", 1);
		}
			
		file_put_contents('token.php', '<?php $token = "'.$token['data']['login']['access_token'].'"; ');

		if (file_exists("token.php")) {
			Logs("Токен обновлен!",1); 
		} else {  
			Logs("Проблемы с созданием файла token.php",1); 
		}

}


function Logs($log, $die = 0) {
    $data = date('Y-m-d H:i:s')." ";
    $data .= $log;
    $data .= "\r\n";

    file_put_contents('log.txt', $data, FILE_APPEND);
    if($die == 1) die($log);
}


function GetCurl($url,$headers,$post_fields = null) {

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
        Logs("Проблемы с curl ".curl_error($ch), 1);
    }

    curl_close($ch);
  

    $data = json_decode($data, true);
    return  $data;
}


