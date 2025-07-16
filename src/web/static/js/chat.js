// chat.js
// Chat and message handling logic for frontend

function addMessage(sender, message, type = 'info') {
    // Add a message to the chat window
    if (!window.chatWindow) window.chatWindow = document.getElementById('chat-window');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender} ${type}`;
    msgDiv.innerHTML = `<div class="message-content">${formatMessage(message)}</div>`;
    window.chatWindow.appendChild(msgDiv);
    setTimeout(() => msgDiv.classList.add('visible'), 10);
    window.chatWindow.scrollTop = window.chatWindow.scrollHeight;
}

function formatMessage(message) {
    // Format message for display (basic HTML escaping)
    return String(message).replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function sendMessage() {
    // Send user message to backend and display response
    if (!window.userInput) window.userInput = document.getElementById('user-input');
    const text = window.userInput.value.trim();
    if (!text) return;
    addMessage('user', text);
    window.userInput.value = '';
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        addMessage('ai', data.reply || '[No reply]');
    } catch (error) {
        addSystemMessage('Failed to send message: ' + error.message, 'error');
    }
}

function addSystemMessage(message, type = 'info') {
    // Add a system message to the chat window
    addMessage('system', message, type);
}

// Export to window for global access
window.addMessage = addMessage;
window.formatMessage = formatMessage;
window.sendMessage = sendMessage;
window.addSystemMessage = addSystemMessage;
