const input = document.getElementById('input');
const sendButton = document.getElementById('send');
const chatDiv = document.getElementById('chat');
const waveBg = document.getElementById('wave-bg');

let currentSession = 'default';

function addMessage(speaker, content) {
    const div = document.createElement('div');
    div.className = `flex ${speaker === 'You' ? 'justify-end' : 'justify-start'} message`;
    div.innerHTML = `
        <div class="${speaker === 'You' ? 'chat-bubble-user' : 'chat-bubble-ai'} px-6 py-4">
            <strong class="block text-xs opacity-75 mb-1">${speaker}</strong>
            <div class="prose prose-invert max-w-none">${content}</div>
        </div>
    `;
    chatDiv.appendChild(div);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message);
    input.value = '';

    if (waveBg) waveBg.classList.add('thinking');

    const res = await fetch('/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: currentSession })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let aiText = '';

    const aiDiv = document.createElement('div');
    aiDiv.className = 'flex justify-start message';
    aiDiv.innerHTML = `<div class="chat-bubble-ai px-6 py-4"><strong class="block text-xs opacity-75 mb-1">Clipper</strong><div class="prose prose-invert"></div></div>`;
    chatDiv.appendChild(aiDiv);
    const textContainer = aiDiv.querySelector('.prose');

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    aiText += data.token;
                    textContainer.textContent = aiText;
                    chatDiv.scrollTop = chatDiv.scrollHeight;
                } catch (e) {}
            }
        }
    }

    if (waveBg) waveBg.classList.remove('thinking');
}

async function loadSidebar() {
    const histRes = await fetch('/api/history');
    const hist = await histRes.json();
    document.getElementById('history-list').innerHTML = hist.sessions.map(s => 
        `<div class="px-4 py-2 hover:bg-gray-800 rounded-xl cursor-pointer">${s}</div>`
    ).join('');

    const clipsRes = await fetch('/api/clips');
    const clipsData = await clipsRes.json();
    document.getElementById('clips-list').innerHTML = clipsData.clips.map(c => 
        `<div class="bg-gray-800 p-3 rounded-2xl text-sm">${c}</div>`
    ).join('');
}

sendButton.addEventListener('click', sendMessage);
input.addEventListener('keypress', e => { 
    if (e.key === 'Enter' && !e.shiftKey) { 
        e.preventDefault(); 
        sendMessage(); 
    } 
});

newSession = () => { 
    chatDiv.innerHTML = ''; 
    currentSession = Date.now().toString(); 
    document.getElementById('session-title').textContent = 'New Conversation'; 
};

clearChat = () => { 
    if (confirm('Clear this conversation?')) chatDiv.innerHTML = ''; 
};

clearAll = async () => { 
    if (confirm('Clear everything?')) { 
        await fetch('/api/clear', {method:'POST'}); 
        loadSidebar(); 
        chatDiv.innerHTML = ''; 
    } 
};

// Boot
loadSidebar();
console.log('%cClipper UI ready', 'color:#3b82f6;font-weight:500');
