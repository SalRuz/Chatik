<?php
header('Content-Type: text/html; charset=utf-8');

if (file_exists('messages.txt')) {
    echo file_get_contents('messages.txt');
} else {
    echo "<em>Сообщений пока нет.</em>";
}
?>
