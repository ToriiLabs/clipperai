const input = document.getElementById('input');
const sendButton = document.getElementById('send');
const chatDiv = document.getElementById('chat');

function addMessage(speaker, message, className = '') {
    const div = document.createElement('div');
    div.className = `flex ${speaker === 'You' ? 'justify-end' : 'justify-start'} message`;
    div.innerHTML = `
        <div class="${speaker === 'You' ? 'chat-bubble-user' : 'chat-bubble-ai'} px-6 py-4">
            <strong class="block text-xs opacity-75 mb-1">${speaker}</strong>
            <div class="prose prose-invert max-w-none">${message}</div>
        </div>
    `;
    chatDiv.appendChild(div);
    chatDiv.scrollTop = chatDiv.scrollHeight;
    return div;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message);
    const loadingDiv = addMessage('Clipper', '<i class="fa-solid fa-spinner fa-spin"></i> Thinking...', 'loading');

    input.value = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        chatDiv.removeChild(loadingDiv); // remove spinner

        if (res.ok) {
            const data = await res.json();
            // Type out the response for streaming feel
            typeOutMessage('Clipper', data.response);
        } else {
            addMessage('Error', 'Failed to get response');
        }
    } catch (err) {
        chatDiv.removeChild(loadingDiv);
        addMessage('Error', err.message);
    }
}

// Fake streaming typewriter effect (feels premium)
function typeOutMessage(speaker, fullText) {
    const div = addMessage(speaker, '');
    const textContainer = div.querySelector('.prose');
    let i = 0;
    const interval = setInterval(() => {
        if (i < fullText.length) {
            textContainer.innerHTML += fullText.charAt(i) === '\n' ? '<br>' : fullText.charAt(i);
            i++;
            chatDiv.scrollTop = chatDiv.scrollHeight;
        } else {
            clearInterval(interval);
        }
    }, 8); // adjust speed if needed
}

sendButton.addEventListener('click', sendMessage);

input.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Placeholder sidebar functions (you can hook these into your existing RAG/clip logic later)
function newSession() {
    chatDiv.innerHTML = '';
    document.getElementById('session-title').textContent = 'New Brainstorm Session';
}

function clearChat() {
    if (confirm('Clear this chat?')) chatDiv.innerHTML = '';
}

function clearAll() {
    if (confirm('Clear everything?')) {
        chatDiv.innerHTML = '';
        // TODO: call your backend clear endpoint
    }
}

// Boot
console.log('%c✅ ClipperAI Pro UI loaded!', 'color:#3b82f6;font-weight:bold');
