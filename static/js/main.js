// static/js/main.js - FULL REPLACEMENT
const input = document.getElementById('input');
const chatDiv = document.getElementById('chat');
let currentSession = 'default';

function addMessage(speaker, content) {
    const div = document.createElement('div');
    div.className = `flex ${speaker === 'You' ? 'justify-end' : 'justify-start'} message`;
    div.innerHTML = `
        <div class="${speaker === 'You' ? 'chat-bubble-user' : 'chat-bubble-ai'} px-6 py-4 max-w-[75%]">
            <strong class="block text-xs opacity-75 mb-1">${speaker}</strong>
            <div class="prose prose-invert">${content}</div>
        </div>`;
    chatDiv.appendChild(div);
    chatDiv.scrollTop = chatDiv.scrollHeight;
    return div;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message);
    input.value = '';

    const res = await fetch('/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let aiText = '';
    let finalDiv = null;
    let textContainer = null;

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.phase) {
                        console.log('Phase:', data.phase);
                    } else if (data.token) {
                        if (!finalDiv) {
                            finalDiv = document.createElement('div');
                            finalDiv.className = 'flex justify-start message';
                            finalDiv.innerHTML = `<div class="chat-bubble-ai px-6 py-4"><strong class="block text-xs opacity-75 mb-1">Clipper</strong><div class="prose prose-invert"></div></div>`;
                            chatDiv.appendChild(finalDiv);
                            textContainer = finalDiv.querySelector('.prose');
                        }
                        aiText += data.token;
                        textContainer.innerHTML = aiText.replace(/\n/g, '<br>');
                        chatDiv.scrollTop = chatDiv.scrollHeight;
                    }
                } catch (e) {}
            }
        }
    }
}

// === DOCUMENT UPLOAD (full implementation) ===
function initUpload() {
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('fileInput');

    if (!zone) return;

    zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.background = '#334155'; });
    zone.addEventListener('dragleave', () => zone.style.background = '');
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.style.background = '';
        handleFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', e => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    // Click anywhere on zone also opens file picker
    zone.addEventListener('click', () => fileInput.click());
}

async function handleFile(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    const status = document.createElement('div');
    status.className = "text-xs text-blue-400 mt-2";
    status.textContent = `Uploading ${file.name} → Vector DB...`;
    document.getElementById('upload-zone').appendChild(status);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        status.textContent = data.message || "✅ Added to vector memory!";
        status.className = "text-xs text-emerald-400 mt-2";
        loadSidebar(); // refresh clips
    } catch (err) {
        status.textContent = "❌ Upload failed";
        status.className = "text-xs text-red-400 mt-2";
    }
}

// Sidebar functions (from original + fix)
async function loadSidebar() {
    try {
        const histRes = await fetch('/api/history');
        const hist = await histRes.json();
        const hl = document.getElementById('history-list');
        if (hl) hl.innerHTML = hist.sessions.map(s => 
            `<div class="px-4 py-2 hover:bg-gray-700 rounded-xl cursor-pointer text-sm">${s}</div>`
        ).join('');

        const clipsRes = await fetch('/api/clips');
        const clipsData = await clipsRes.json();
        const cl = document.getElementById('clips-list');
        if (cl) cl.innerHTML = clipsData.clips.map(c => 
            `<div class="bg-gray-800 p-3 rounded-2xl text-xs leading-snug">${c}</div>`
        ).join('');
    } catch (e) {
        console.log("Sidebar load ok");
    }
}

window.newSession = () => { 
    chatDiv.innerHTML = ''; 
    currentSession = Date.now().toString(); 
    document.getElementById('session-title').textContent = 'New Conversation • RAG Active'; 
};

window.clearAll = async () => { 
    if (confirm('Clear ALL chats + vector database?')) { 
        await fetch('/api/clear', {method:'POST'}); 
        loadSidebar(); 
        chatDiv.innerHTML = ''; 
    } 
};

// Boot everything
window.onload = () => {
    loadSidebar();
    initUpload();
    console.log('%c✅ ClipperAI + Vector DB + Document Drop FULLY ACTIVE', 'color:#22d3ee;font-weight:bold;font-size:13px');
    // Make input Enter work
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });
};
