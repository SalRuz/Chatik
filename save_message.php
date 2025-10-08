<?php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') exit;

$username = $_POST['username'] ?? '';
$message = $_POST['message'] ?? '';

if (empty($username) || empty($message)) exit;

// Очистка от потенциально опасных символов (минимальная защита)
$username = htmlspecialchars(trim($username), ENT_QUOTES, 'UTF-8');
$message = htmlspecialchars(trim($message), ENT_QUOTES, 'UTF-8');

$log = "[" . date('Y-m-d H:i:s') . "] <b>{$username}</b>: {$message}\n";

// Добавляем сообщение в файл
file_put_contents('messages.txt', $log, FILE_APPEND | LOCK_EX);
?>
