/* ═══════════════════════════════════════════════════════════
   MediMind AI — Chat Module
   Handles messaging, rendering, session management
   ═══════════════════════════════════════════════════════════ */

const Chat = {
    currentSessionId: null,
    isProcessing: false,
    pendingImage: null,  // Set by ImageHandler

    elements: {},

    init() {
        this.elements = {
            chatArea: document.getElementById('chat-area'),
            messagesContainer: document.getElementById('messages-container'),
            welcomeScreen: document.getElementById('welcome-screen'),
            typingIndicator: document.getElementById('typing-indicator'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            sessionList: document.getElementById('session-list'),
            sessionTitle: document.getElementById('session-title'),
            exportBtn: document.getElementById('export-btn'),
            deleteSessionBtn: document.getElementById('delete-session-btn'),
            newChatBtn: document.getElementById('new-chat-btn'),
        };

        // Event listeners
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.elements.messageInput.addEventListener('input', () => {
            autoResizeTextarea(this.elements.messageInput);
            this.elements.sendBtn.disabled = !this.elements.messageInput.value.trim() && !this.pendingImage;
        });

        this.elements.newChatBtn.addEventListener('click', () => this.newSession());
        this.elements.exportBtn.addEventListener('click', () => this.exportChat());
        this.elements.deleteSessionBtn.addEventListener('click', () => this.deleteCurrentSession());

        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                this.elements.messageInput.value = query;
                autoResizeTextarea(this.elements.messageInput);
                this.elements.sendBtn.disabled = false;
                this.sendMessage();
            });
        });

        // Load sessions
        this.loadSessions();
        this.loadRAGStats();
    },

    async sendMessage() {
        const text = this.elements.messageInput.value.trim();
        const image = this.pendingImage;

        if (!text && !image) return;
        if (this.isProcessing) return;

        this.isProcessing = true;
        this.elements.sendBtn.disabled = true;

        // Hide welcome, show messages
        this.elements.welcomeScreen.style.display = 'none';
        this.elements.messagesContainer.style.display = 'flex';

        // Determine message type
        let msgType = 'text';
        let imageUrl = null;

        if (image) {
            msgType = 'image';
            imageUrl = URL.createObjectURL(image);
        }

        // Render user message
        this.renderMessage({
            role: 'user',
            content: text || 'Analyze this medical image',
            message_type: msgType,
            image_url: imageUrl,
            timestamp: new Date().toISOString(),
        });

        // Clear input
        this.elements.messageInput.value = '';
        autoResizeTextarea(this.elements.messageInput);
        this.clearPendingImage();

        // Show typing indicator
        this.showTyping(true);
        this.scrollToBottom();

        try {
            let result;

            if (image) {
                // Image message
                const formData = new FormData();
                formData.append('image', image);
                formData.append('message', text || 'Please analyze this medical image.');
                if (this.currentSessionId) formData.append('session_id', this.currentSessionId);

                result = await apiFormRequest('/api/chat/image', formData);
            } else {
                // Text message
                const formData = new FormData();
                formData.append('message', text);
                if (this.currentSessionId) formData.append('session_id', this.currentSessionId);

                result = await apiFormRequest('/api/chat/message', formData);
            }

            // Update session
            if (result.session_id) {
                this.currentSessionId = result.session_id;
            }

            // Render AI response
            this.renderMessage({
                role: 'assistant',
                content: result.response,
                message_type: image ? 'image' : 'text',
                sources: result.sources,
                web_results: result.web_results,
                image_analysis: result.image_analysis,
                tts_audio: result.tts_audio,
                timestamp: new Date().toISOString(),
            });

            // Refresh session list
            this.loadSessions();

        } catch (error) {
            this.renderMessage({
                role: 'assistant',
                content: `⚠️ **Error:** ${error.message}\n\nPlease try again or check if the backend is running.`,
                timestamp: new Date().toISOString(),
            });
            showToast(error.message, 'error');
        } finally {
            this.showTyping(false);
            this.isProcessing = false;
            this.scrollToBottom();
        }
    },

    async sendVoiceMessage(audioBlob) {
        if (this.isProcessing) return;

        this.isProcessing = true;
        this.elements.welcomeScreen.style.display = 'none';
        this.elements.messagesContainer.style.display = 'flex';

        // Render placeholder user message
        this.renderMessage({
            role: 'user',
            content: '🎤 Voice message...',
            message_type: 'voice',
            timestamp: new Date().toISOString(),
        });

        this.showTyping(true);
        this.scrollToBottom();

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            if (this.currentSessionId) formData.append('session_id', this.currentSessionId);

            const result = await apiFormRequest('/api/chat/voice', formData);

            if (result.session_id) {
                this.currentSessionId = result.session_id;
            }

            // Update user message with transcription
            if (result.transcribed_text) {
                const lastUserMsg = this.elements.messagesContainer.querySelector('.message.user:last-of-type .message-content');
                if (lastUserMsg) {
                    lastUserMsg.innerHTML = markdownToHtml(result.transcribed_text);
                }
            }

            this.renderMessage({
                role: 'assistant',
                content: result.response,
                message_type: 'voice',
                sources: result.sources,
                tts_audio: result.tts_audio,
                timestamp: new Date().toISOString(),
            });

            // Auto-play TTS if available
            if (result.tts_audio) {
                this.playTTSAudio(result.tts_audio);
            }

            this.loadSessions();

        } catch (error) {
            this.renderMessage({
                role: 'assistant',
                content: `⚠️ **Error:** ${error.message}`,
                timestamp: new Date().toISOString(),
            });
            showToast(error.message, 'error');
        } finally {
            this.showTyping(false);
            this.isProcessing = false;
            this.scrollToBottom();
        }
    },

    renderMessage(msg) {
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;

        const avatarText = msg.role === 'user' ? 'You' : '🧠';
        const avatarSvg = msg.role === 'assistant'
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`
            : 'U';

        let imageHtml = '';
        if (msg.image_url && msg.role === 'user') {
            imageHtml = `<div class="message-image" onclick="openLightbox('${msg.image_url}')">
                <img src="${msg.image_url}" alt="Uploaded medical image">
            </div>`;
        }

        let sourcesHtml = '';
        if (msg.sources && msg.sources.length > 0) {
            const sourceItems = msg.sources.map(s =>
                `<span class="source-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    ${s.source} (p.${s.page})
                </span>`
            ).join('');
            sourcesHtml = `<div class="source-citations">
                <div class="sources-header">📚 Sources</div>
                <div>${sourceItems}</div>
            </div>`;
        }

        let webResultsHtml = '';
        if (msg.web_results && msg.web_results.length > 0) {
            const items = msg.web_results.map(r =>
                `<a class="web-result-item" href="${r.url}" target="_blank" rel="noopener">
                    <div class="web-result-title">${r.title}</div>
                    <div class="web-result-url">${r.url}</div>
                </a>`
            ).join('');
            webResultsHtml = `<div class="web-results">
                <div class="web-results-header">🌐 Web Sources</div>
                ${items}
            </div>`;
        }

        let analysisHtml = '';
        if (msg.image_analysis && msg.role === 'assistant') {
            analysisHtml = `<div class="image-analysis-card">
                <div class="analysis-header">👁️ LLaVA Vision Analysis</div>
                <div class="analysis-findings" style="white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; padding-top: 8px;">${msg.image_analysis}</div>
            </div>`;
        }

        let ttsHtml = '';
        if (msg.tts_audio && msg.role === 'assistant') {
            ttsHtml = `<div class="tts-player">
                <button class="tts-play-btn" onclick="Chat.playTTSAudio('${msg.tts_audio}')">
                    🔊 Play Response
                </button>
            </div>`;
        }

        let typeBadge = '';
        if (msg.message_type === 'voice') {
            typeBadge = '<span class="message-type-badge voice">🎤 Voice</span>';
        } else if (msg.message_type === 'image' && msg.role === 'assistant') {
            typeBadge = '<span class="message-type-badge image">🔬 Image Analysis</span>';
        }

        div.innerHTML = `
            <div class="message-avatar">${avatarSvg}</div>
            <div class="message-bubble">
                ${imageHtml}
                ${analysisHtml}
                <div class="message-content">${markdownToHtml(msg.content)}</div>
                ${sourcesHtml}
                ${webResultsHtml}
                ${ttsHtml}
                <div class="message-footer">
                    ${typeBadge}
                    <span>${formatTime(msg.timestamp)}</span>
                </div>
            </div>
        `;

        this.elements.messagesContainer.appendChild(div);
    },

    showTyping(show) {
        this.elements.typingIndicator.style.display = show ? 'flex' : 'none';
    },

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.elements.chatArea.scrollTop = this.elements.chatArea.scrollHeight;
        });
    },

    clearPendingImage() {
        this.pendingImage = null;
        const previewBar = document.getElementById('image-preview-bar');
        if (previewBar) previewBar.style.display = 'none';
        const input = document.getElementById('image-input');
        if (input) input.value = '';
    },

    playTTSAudio(base64Audio) {
        try {
            const bytes = atob(base64Audio);
            const arr = new Uint8Array(bytes.length);
            for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
            const blob = new Blob([arr], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.play().catch(() => showToast('Could not play audio', 'error'));
        } catch (e) {
            console.error('TTS playback error:', e);
        }
    },

    // ── Session Management ──

    async loadSessions() {
        try {
            const sessions = await apiRequest('/api/chat/sessions');
            this.renderSessionList(sessions);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    },

    renderSessionList(sessions) {
        const list = this.elements.sessionList;
        list.innerHTML = '';

        if (sessions.length === 0) {
            list.innerHTML = `<div style="padding:16px;text-align:center;color:var(--text-tertiary);font-size:0.8rem;">
                No conversations yet
            </div>`;
            return;
        }

        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `session-item ${s.id === this.currentSessionId ? 'active' : ''}`;
            item.innerHTML = `
                <span class="session-item-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                </span>
                <span class="session-item-text" title="${s.title}">${s.title}</span>
                <button class="session-item-delete" title="Delete" onclick="event.stopPropagation(); Chat.deleteSession(${s.id})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;
            item.addEventListener('click', () => this.loadSession(s.id));
            list.appendChild(item);
        });
    },

    async loadSession(sessionId) {
        try {
            const data = await apiRequest(`/api/chat/sessions/${sessionId}`);
            this.currentSessionId = sessionId;

            // Clear and render messages
            this.elements.messagesContainer.innerHTML = '';
            this.elements.welcomeScreen.style.display = 'none';
            this.elements.messagesContainer.style.display = 'flex';
            this.elements.sessionTitle.textContent = data.title || 'Conversation';

            data.messages.forEach(msg => this.renderMessage(msg));
            this.scrollToBottom();
            this.loadSessions(); // Update active indicator

            // Close sidebar on mobile
            document.getElementById('sidebar').classList.remove('open');
            const overlay = document.querySelector('.sidebar-overlay');
            if (overlay) overlay.classList.remove('show');

        } catch (error) {
            showToast('Failed to load session', 'error');
        }
    },

    async newSession() {
        this.currentSessionId = null;
        this.elements.messagesContainer.innerHTML = '';
        this.elements.messagesContainer.style.display = 'none';
        this.elements.welcomeScreen.style.display = 'flex';
        this.elements.sessionTitle.textContent = 'New Conversation';
        this.elements.messageInput.focus();
        this.loadSessions();
    },

    async deleteSession(sessionId) {
        if (!confirm('Delete this conversation?')) return;
        try {
            await apiRequest(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
            if (this.currentSessionId === sessionId) {
                this.newSession();
            }
            this.loadSessions();
            showToast('Conversation deleted', 'success');
        } catch (error) {
            showToast('Failed to delete', 'error');
        }
    },

    async deleteCurrentSession() {
        if (!this.currentSessionId) return;
        this.deleteSession(this.currentSessionId);
    },

    async exportChat() {
        if (!this.currentSessionId) {
            showToast('No conversation to export', 'info');
            return;
        }
        try {
            const data = await apiRequest(`/api/chat/export/${this.currentSessionId}`);
            const text = data.messages.map(m =>
                `[${m.timestamp}] ${m.role.toUpperCase()}: ${m.content}`
            ).join('\n\n---\n\n');

            const blob = new Blob(
                [`MediMind AI - Chat Export\nSession: ${data.title}\nDate: ${data.created_at}\n\n${'='.repeat(50)}\n\n${text}`],
                { type: 'text/plain' }
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `medimind_chat_${data.session_id}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('Chat exported successfully', 'success');
        } catch (error) {
            showToast('Export failed', 'error');
        }
    },

    async loadRAGStats() {
        try {
            const stats = await apiRequest('/api/chat/rag-stats');
            const el = document.getElementById('rag-stats-text');
            if (stats.status === 'ready') {
                el.textContent = `${stats.total_chunks} knowledge chunks indexed`;
            } else {
                el.textContent = 'Knowledge base loading...';
            }
        } catch {
            document.getElementById('rag-stats-text').textContent = 'Knowledge base unavailable';
        }
    },
};

// Lightbox helper
function openLightbox(imageUrl) {
    const lb = document.getElementById('lightbox');
    const img = document.getElementById('lightbox-img');
    img.src = imageUrl;
    lb.style.display = 'flex';
}
