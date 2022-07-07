<?php
$login = "79521231234"; // логин smartshell
$password = "password"; // пароль smartshell
$id = "9999"; // узнать свой ид клуба http://АДРЕС/SmartShellAlisa.php?d=clubs




if (file_exists("token.php")) {
    file_put_contents('token.php', '');
}

if(isset($_GET['d'])) {

    if($_GET['d'] == "users") {
            
        UpToken($login,$password,$id);
        require 'token.php';

        $users = GetUsers($token);

        $u = "Логин;Телефон;Депозит;Дата рождения;Имя;Фамилия;Отчество;Отсидел часов;Последний вход;Дата регистрации;Скидка %;;;;;;;;;\r\n";
        foreach($users['data']['clients']['data'] as $user) {
            $u .= $user['login'].";".$user['phone'].";".$user['deposit'].";".$user['dob'].";".$user['first_name'].";".$user['last_name'].";".$user['middle_name'].";".$user['total_hours'].";".$user['last_client_activity'].";".$user['created_at'].";".$user['user_discount'].";;;;;;;;;\r\n";
        }
        file_put_contents('users.csv', iconv('utf-8', 'windows-1251', $u));

    }

    if($_GET['d'] == "clubs") {

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
        
    $users = GetCurl($url,$headers,$post_fields);

    if(!isset($users['data']['clients']['data'][0])) {
        Logs("проблемы с получением cписка юзеров SmartShell", 1);
    }

    return $users;
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
