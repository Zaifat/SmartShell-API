# SmartShell_Alisa
Интеграция SmartShell и "Умный дом с Алисой"

Скрипт интеграции программы для управления компьютерным клубом smartshell.gg и yandex.ru/alice/smart-home (умный дом от яндекс)<br><br>

Все что вам нужно для подключения:<br><br>

1. Купить умную розетку, умеющую работать с умным домом от яндекса (почти любая)<br>
Пример таких розеток:<br>
https://aliexpress.ru/item/1005003640070178.html

2. В приложении "Умный дом" от яндекса, названия розеток должно совпадать с названием игровой приставки в SmartShell (в приложении названия можно выставлять только на кириллице!)<br>
Пример:<br>
ПС4 1<br>
ХВОХ4 2 (набрано на кириллице)

3. Создать приложение яндекса, и получить токен на управление оборудованием "яндекс умный дом".<br>
Как это сделать смотрите тут: https://www.youtube.com/watch?v=zHcx-TD4ZPU

4. Настроить конфиг в файле

```PHP
$login = "7956665557"; // логин smartshell
$password = "password"; // пароль smartshell
$id = "9999"; // узнать свой ид клуба http://ССЫЛКА/SmartShell_Alisa.php?d=clubs
$ya_token = "токен"; // как получить токен умного дома от яндекса смотрите http://www.youtube.com/watch?v=zHcx-TD4ZPU
```
<br><br>
5. Закинуть файл на веб хостинг, либо понять сервер на компьютере администратора с помощью того же openserver (https://ospanel.io/)

6. Создать задания в планировщике задач

на обновление токена на доступ к SmartShell<br>

``
раз в сутки / пример cron - 00 00 * * *<br>
wget http://адрес/SmartShell_Alisa.php?d=token
``
<br><br>
на опрос состояния розеток (яндекс умный дом) и приставок (в SmartShell)<br>

``
раз в минуту / пример cron - * * * * *<br>
wget http://адрес/SmartShell_Alisa.php?d=check
``

7. Получить токен для работы сейчас - http://адрес/SmartShell_Alisa.php?d=token<br>
Проверить нет ли ошибок в логе, файл log.txt<br><br>

Радуемся! Теперь работа ваших приставкой полностью автоматизирована!<br><br>


Если вопросы, пишем сюда - https://t.me/zaifat
