const messages = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

const chatbot = {
  messages: [],
  addMessage(message, from = "user") {
    const li = document.createElement('li');
    if (from === 'chatbot') {
      li.classList.add('chatbot-message');
      li.textContent = message; // Affichez le message en tant que texte brut
    } else {
      li.classList.add('user-message');
      li.textContent = message;
    }
    messages.appendChild(li);
    messages.scrollTop = messages.scrollHeight; // Auto-scroll to the bottom
  }
};

sendButton.addEventListener('click', () => {
  const message = messageInput.value.trim();
  if (message) {
    chatbot.addMessage(`You: ${message}`, 'user');
    handleChatbotResponse(message);
    messageInput.value = '';
  }
});

messageInput.addEventListener('keydown', event => {
  if (event.key === 'Enter') {
    event.preventDefault();
    sendButton.click();
  }
});

function handleChatbotResponse(message) {
  // Send the message to the Flask backend and get the response
  fetch('/send_message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `message=${message}`,
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Received data:', data);
      const responseMessage = data.response;
      chatbot.addMessage(responseMessage, 'chatbot');
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

chatbot.addMessage('Chatbot: Salut, comment puis-je vous assister ?', 'chatbot');
