let username = '';

function setUsername() {
  const input = document.getElementById('username').value.trim();
  if (input === '') {
    alert('Пожалуйста, введите имя!');
    return;
  }
  username = input;
  document.getElementById('name-form').classList.add('hidden');
  document.getElementById('chat-container').classList.remove('hidden');
  loadMessages();
  // Автообновление чата каждые 2 секунды
  setInterval(loadMessages, 2000);
}

function sendMessage() {
  const msgInput = document.getElementById('message-input');
  const message = msgInput.value.trim();
  if (message === '') return;

  fetch('save_message.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `username=${encodeURIComponent(username)}&message=${encodeURIComponent(message)}`
  }).then(() => {
    msgInput.value = '';
    loadMessages();
  });
}

function loadMessages() {
  fetch('get_messages.php')
    .then(response => response.text())
    .then(data => {
      document.getElementById('chat-box').innerHTML = data;
      // Прокрутка вниз
      const chatBox = document.getElementById('chat-box');
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}
