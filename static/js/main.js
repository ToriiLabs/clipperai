const input = document.getElementById('input');
const sendButton = document.getElementById('send');
const chatDiv = document.getElementById('chat');

function addMessage(speaker, message, className) {
    const div = document.createElement('div');
    div.className = className;
    div.innerHTML = `<strong>${speaker}:</strong> ${message}`;
    chatDiv.appendChild(div);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message, 'user-message');
    const loadingDiv = addMessage('Clipper', 'Thinking...', 'loading'); // temporary

    input.value = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        if (res.ok) {
            const data = await res.json();
            // Remove temporary loading message
            chatDiv.removeChild(loadingDiv);
            addMessage('Clipper', data.response, 'ai-message');
        } else {
            chatDiv.removeChild(loadingDiv);
            addMessage('Error', 'Failed to get response', 'ai-message');
        }
    } catch (err) {
        chatDiv.removeChild(loadingDiv);
        addMessage('Error', err.message, 'ai-message');
    }
}

sendButton.addEventListener('click', sendMessage);

input.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
