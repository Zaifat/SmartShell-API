# SmartShell_Alisa
Интеграция SmartShell и "Умный дом с Алисой"

Скрипт интеграции программы для управления компьютерным клубом smartshell.gg и yandex.ru/alice/smart-home (умный дом от яндекс)<br><br>

Все что вам нужно для подключения:<br><br>

1. <b>Купить умную розетку, умеющую работать с умным домом от яндекса (почти любая)</b><br>
Пример таких розеток:<br>
https://aliexpress.ru/item/1005003640070178.html<br>

2. <b>В приложении "Умный дом" от яндекса, названия розеток должно совпадать с названием игровой приставки в SmartShell (в приложении названия можно выставлять только на кириллице!)</b><br>
Пример:<br>
ПС4<br>
ХВОХ4(набрано на кириллице)<br>

3. <b>Создать приложение яндекса, и получить токен на управление оборудованием "яндекс умный дом".</b><br>
Как это сделать смотрите тут: https://www.youtube.com/watch?v=zHcx-TD4ZPU<br>

4. <b>Скачать файл SmartShell_Alisa.php </b>

Настроить конфиг в файле (у кого проблема с кодировкой, открывайте через notepad++)

```PHP
$login = "7956665557"; // логин smartshell
$password = "password"; // пароль smartshell
$id = "9999"; // узнать свой ид клуба http://ССЫЛКА/SmartShell_Alisa.php?d=clubs
$ya_token = "токен"; // как получить токен умного дома от яндекса смотрите http://www.youtube.com/watch?v=zHcx-TD4ZPU
```
<br>

5. <b>Закинуть на хостинг файл SmartShell_Alisa.php</b>

<b>Для тех у кого нет хостинга:</b> 
1) установить на компьютер openserver (скачать можно тут https://biblprog.org.ua/ru/open_server/download/)
2) закинуть файл SmartShell_Alisa.php в папку localhost (пример пути C:\OpenServer\domains\localhost)
<br>

6. <b>Создать задания на опрос состояния розеток (яндекс умный дом) и приставок (в SmartShell) в планировщике задач (cron)</b> <br>
```PHP
* * * * *  wget http://localhost/SmartShell_Alisa.php?d=check
```
<br>

Для тех кто настраивает на openserver, зайдите в настройки openserver, найдите вкладку Планировщик заданий, укажите все как на скришоте ниже и нажмите кнопку добавить <br><br>
![image](https://user-images.githubusercontent.com/33205124/193473603-b5da8b87-801d-4207-949e-e2b61f74d4ea.png)<br>
так же в настройках включите автозапуск<br><br>
![image](https://user-images.githubusercontent.com/33205124/193473508-87239679-1178-415c-9425-cbe1ae00c75b.png)
<br>


7. Проверить нет ли ошибок в логе, файл log.txt<br><br>

Радуемся! Теперь работа ваших приставкой полностью автоматизирована!<br><br>


Если вопросы, пишем сюда - https://t.me/zaifat
