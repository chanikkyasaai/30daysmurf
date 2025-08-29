document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AI Voice Agent - Day 23 Complete Version Loaded');

    // --- Session Management ---
    let sessionId = new URLSearchParams(window.location.search).get('session_id');
    if (!sessionId) {
        sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        const newUrl = `${window.location.pathname}?session_id=${sessionId}`;
        window.history.replaceState({ path: newUrl }, '', newUrl);
    }
    console.log(`Session ID: ${sessionId}`);

    // --- Element Selection ---
    const recordBtn = document.getElementById('record-btn');
    const agentAudio = document.getElementById('echo-audio');
    const agentMessage = document.getElementById('echo-message');
    const icon = recordBtn ? recordBtn.querySelector('.icon') : null;
    
    // New UI Elements
    const currentSessionId = document.getElementById('current-session-id');
    const agentStatusIndicator = document.getElementById('agent-status-indicator');
    const agentStatusText = document.getElementById('agent-status-text');
    const liveTranscript = document.getElementById('current-transcript');
    const conversationHistory = document.getElementById('conversation-history');
    const audioIndicator = document.getElementById('audio-indicator');
    const sessionsList = document.getElementById('sessions-list');
    const newSessionBtn = document.getElementById('new-session-btn');
    const toastContainer = document.getElementById('toast-container');

    // Configuration Elements
    const configBtn = document.getElementById('config-btn');
    const configSection = document.getElementById('config-section');
    const closeConfigBtn = document.getElementById('close-config-btn');
    const saveConfigBtn = document.getElementById('save-config-btn');
    const testConfigBtn = document.getElementById('test-config-btn');
    const configStatus = document.getElementById('config-status');
    
    // API Key Input Elements
    const assemblyaiKeyInput = document.getElementById('assemblyai-key');
    const openaiKeyInput = document.getElementById('openai-key');
    const murfrKeyInput = document.getElementById('murf-key');
    const tavilyKeyInput = document.getElementById('tavily-key');

    // Set current session ID in UI
    if (currentSessionId) {
        currentSessionId.textContent = sessionId.split('_')[1] || sessionId.substring(0, 8);
    }

    // --- Configuration Management ---
    const API_KEYS_STORAGE_KEY = 'ravi_api_keys';
    const CHAT_HISTORY_STORAGE_KEY = 'ravi_chat_history';
    const SESSION_LIST_STORAGE_KEY = 'ravi_session_list';

    // Client-side Chat History Management
    class ClientChatStorage {
        constructor() {
            this.chatHistory = this.loadChatHistory();
            this.sessionList = this.loadSessionList();
        }

        loadChatHistory() {
            try {
                const stored = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
                return stored ? JSON.parse(stored) : {};
            } catch (error) {
                console.error('Error loading chat history from localStorage:', error);
                return {};
            }
        }

        loadSessionList() {
            try {
                const stored = localStorage.getItem(SESSION_LIST_STORAGE_KEY);
                return stored ? JSON.parse(stored) : [];
            } catch (error) {
                console.error('Error loading session list from localStorage:', error);
                return [];
            }
        }

        saveChatTurn(sessionId, userMessage, agentResponse) {
            try {
                // Ensure session exists in history
                if (!this.chatHistory[sessionId]) {
                    this.chatHistory[sessionId] = [];
                }

                // Add new turn
                const turn = {
                    user_message: userMessage,
                    agent_response: agentResponse,
                    timestamp: new Date().toISOString()
                };

                this.chatHistory[sessionId].push(turn);

                // Limit history to last 100 turns per session
                if (this.chatHistory[sessionId].length > 100) {
                    this.chatHistory[sessionId] = this.chatHistory[sessionId].slice(-100);
                }

                // Update session list
                this.updateSessionList(sessionId);

                // Save to localStorage
                localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(this.chatHistory));
                localStorage.setItem(SESSION_LIST_STORAGE_KEY, JSON.stringify(this.sessionList));

                console.log('💾 Chat turn saved to localStorage');
                return true;
            } catch (error) {
                console.error('Error saving chat turn:', error);
                return false;
            }
        }

        updateSessionList(sessionId) {
            // Remove existing entry if it exists
            this.sessionList = this.sessionList.filter(s => s.session_id !== sessionId);

            // Add/update session
            const session = {
                session_id: sessionId,
                last_activity: new Date().toISOString(),
                message_count: this.chatHistory[sessionId] ? this.chatHistory[sessionId].length : 0
            };

            this.sessionList.unshift(session);

            // Limit session list to 50 most recent
            if (this.sessionList.length > 50) {
                this.sessionList = this.sessionList.slice(0, 50);
            }
        }

        getChatHistory(sessionId, limit = 50) {
            const history = this.chatHistory[sessionId] || [];
            // Return in chronological order (oldest first) for proper display
            return history.slice(-limit);
        }

        getSessionList(limit = 20) {
            return this.sessionList.slice(0, limit);
        }

        clearSessionHistory(sessionId) {
            try {
                if (this.chatHistory[sessionId]) {
                    delete this.chatHistory[sessionId];
                    this.sessionList = this.sessionList.filter(s => s.session_id !== sessionId);
                    
                    localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(this.chatHistory));
                    localStorage.setItem(SESSION_LIST_STORAGE_KEY, JSON.stringify(this.sessionList));
                    
                    console.log('🗑️ Session history cleared from localStorage');
                    return true;
                }
                return false;
            } catch (error) {
                console.error('Error clearing session history:', error);
                return false;
            }
        }
    }

    // Initialize client-side chat storage
    const clientChatStorage = new ClientChatStorage();
    
    // Load saved API keys
    function loadApiKeys() {
        try {
            const savedKeys = localStorage.getItem(API_KEYS_STORAGE_KEY);
            if (savedKeys) {
                const keys = JSON.parse(savedKeys);
                if (assemblyaiKeyInput) assemblyaiKeyInput.value = keys.assemblyai || '';
                if (openaiKeyInput) openaiKeyInput.value = keys.openai || '';
                if (murfrKeyInput) murfrKeyInput.value = keys.murf || '';
                if (tavilyKeyInput) tavilyKeyInput.value = keys.tavily || '';
                console.log('🔑 API keys loaded from localStorage');
                
                // Send to backend for runtime use
                fetch('/api/set-runtime-keys', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(keys)
                }).then(response => response.json())
                  .then(result => {
                      if (result.success) {
                          console.log('🔗 API keys sent to backend for runtime use');
                      }
                  }).catch(error => {
                      console.warn('Failed to send API keys to backend:', error);
                  });
            }
        } catch (error) {
            console.error('Error loading API keys:', error);
        }
    }
    
    // Save API keys
    function saveApiKeys() {
        try {
            const keys = {
                assemblyai: assemblyaiKeyInput?.value?.trim() || '',
                openai: openaiKeyInput?.value?.trim() || '',
                murf: murfrKeyInput?.value?.trim() || '',
                tavily: tavilyKeyInput?.value?.trim() || ''
            };
            localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(keys));
            
            // Also send to backend for runtime use
            fetch('/api/set-runtime-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(keys)
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      showConfigStatus('Configuration saved and applied successfully!', 'success');
                      console.log('💾 API keys saved and sent to backend');
                  } else {
                      showConfigStatus('Saved locally but failed to apply: ' + result.message, 'error');
                  }
              }).catch(error => {
                  showConfigStatus('Saved locally but failed to apply: ' + error.message, 'error');
              });
            
            return true;
        } catch (error) {
            console.error('Error saving API keys:', error);
            showConfigStatus('Failed to save configuration: ' + error.message, 'error');
            return false;
        }
    }
    
    // Check if API keys are configured
    function areApiKeysConfigured() {
        try {
            const savedKeys = localStorage.getItem(API_KEYS_STORAGE_KEY);
            if (!savedKeys) return false;
            
            const keys = JSON.parse(savedKeys);
            // Check if at least the essential keys are configured
            const hasAssemblyAI = keys.assemblyai && keys.assemblyai.trim() !== '';
            const hasOpenAI = keys.openai && keys.openai.trim() !== '';
            const hasMurf = keys.murf && keys.murf.trim() !== '';
            
            return hasAssemblyAI && hasOpenAI && hasMurf;
        } catch (error) {
            console.error('Error checking API keys:', error);
            return false;
        }
    }
    
    // Show API configuration prompt
    function showApiConfigPrompt() {
        showToast('Please configure your API keys first! Click the gear icon to set up.', 'warning', 5000);
        
        // Optionally pulse the config button to draw attention
        if (configBtn) {
            configBtn.style.animation = 'pulse 1s ease-in-out 3';
            setTimeout(() => {
                configBtn.style.animation = '';
            }, 3000);
        }
    }
    
    // Test API keys
    async function testApiKeys() {
        showConfigStatus('Testing API keys...', 'info');
        
        const keys = {
            assemblyai: assemblyaiKeyInput?.value?.trim() || '',
            openai: openaiKeyInput?.value?.trim() || '',
            murf: murfrKeyInput?.value?.trim() || '',
            tavily: tavilyKeyInput?.value?.trim() || ''
        };
        
        try {
            const response = await fetch('/api/test-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(keys)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showConfigStatus(`✅ ${result.message}`, 'success');
            } else {
                showConfigStatus(`❌ ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Error testing API keys:', error);
            showConfigStatus('Failed to test API keys: ' + error.message, 'error');
        }
    }
    
    // Show configuration status message
    function showConfigStatus(message, type) {
        if (!configStatus) return;
        
        configStatus.textContent = message;
        configStatus.className = `config-status ${type}`;
        configStatus.style.display = 'block';
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                configStatus.style.display = 'none';
            }, 5000);
        }
    }
    
    // Toggle password visibility
    function setupPasswordToggle() {
        document.querySelectorAll('.toggle-visibility').forEach(btn => {
            btn.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const input = document.getElementById(targetId);
                const icon = this.querySelector('.material-icons');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.textContent = 'visibility_off';
                } else {
                    input.type = 'password';
                    icon.textContent = 'visibility';
                }
            });
        });
    }
    
    // Configuration Event Listeners
    if (configBtn) {
        configBtn.addEventListener('click', function() {
            if (configSection.style.display === 'none') {
                configSection.style.display = 'block';
                configBtn.classList.add('active');
                loadApiKeys(); // Load keys when opening
            } else {
                configSection.style.display = 'none';
                configBtn.classList.remove('active');
            }
        });
    }
    
    if (closeConfigBtn) {
        closeConfigBtn.addEventListener('click', function() {
            configSection.style.display = 'none';
            configBtn?.classList.remove('active');
        });
    }
    
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveApiKeys);
    }
    
    if (testConfigBtn) {
        testConfigBtn.addEventListener('click', testApiKeys);
    }
    
    // Initialize password toggle functionality
    setupPasswordToggle();
    
    // Load API keys on page load
    loadApiKeys();

    // Check if required elements exist
    if (!recordBtn) {
        console.error('❌ Record button not found! Check HTML structure.');
        return;
    }

    // --- State Management ---
    let mediaRecorder;
    let ws;
    let audioContext;
    let pcmProcessorNode;
    let agentState = 'IDLE';
    let silenceTimeout;
    
    // --- Audio Data Accumulation ---
    let audioChunks = [];
    
    // --- Audio Playback ---
    let streamingAudioContext;
    let playheadTime;
    let isPlaying = false;
    let wavHeaderSet = true;
    let audioChunksForPlayback = [];
    let currentAudioElement;
    let isStreamingStarted = false;
    const SAMPLE_RATE = 44100;

    // --- Session Management Functions ---
    async function loadSessions() {
        try {
            // Use client-side storage instead of server API
            const sessions = clientChatStorage.getSessionList(20);
            displaySessions(sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    function displaySessions(sessions) {
        if (!sessionsList) return;
        
        if (sessions.length === 0) {
            sessionsList.innerHTML = '<div class="no-sessions">No previous sessions</div>';
            return;
        }

        const sessionsHtml = sessions.map(session => {
            const isActive = session.session_id === sessionId;
            const lastActivity = new Date(session.last_activity).toLocaleDateString();
            const sessionName = session.session_id.split('_')[1] || session.session_id.substring(0, 8);
            
            return `
                <div class="session-item ${isActive ? 'active' : ''}" data-session-id="${session.session_id}">
                    <div class="session-name">Session ${sessionName}</div>
                    <div class="session-preview">${session.message_count} messages</div>
                    <div class="session-time">${lastActivity}</div>
                </div>
            `;
        }).join('');

        sessionsList.innerHTML = sessionsHtml;

        // Add click handlers
        sessionsList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionIdToLoad = item.dataset.sessionId;
                if (sessionIdToLoad !== sessionId) {
                    loadSession(sessionIdToLoad);
                }
            });
        });
    }

    async function loadSession(newSessionId) {
        try {
            // Update session ID
            sessionId = newSessionId;
            
            // Update URL without reloading
            const newUrl = `${window.location.pathname}?session_id=${newSessionId}`;
            window.history.replaceState({ path: newUrl }, '', newUrl);
            
            // Update UI session ID display
            if (currentSessionId) {
                currentSessionId.textContent = sessionId.split('_')[1] || sessionId.substring(0, 8);
            }
            
            // Load chat history for this session
            await loadChatHistory(newSessionId);
            
            // Update sessions list to highlight current session
            await loadSessions();
            
        } catch (error) {
            console.error('Error loading session:', error);
            showToast('Failed to load session', 'error');
        }
    }

    async function loadChatHistory(sessionIdToLoad) {
        try {
            console.log(`Loading chat history for session: ${sessionIdToLoad}`);
            
            // Use client-side storage instead of server API
            const history = clientChatStorage.getChatHistory(sessionIdToLoad, 50);
            console.log('Chat history loaded from localStorage:', history);
            
            // Clear current conversation
            clearConversationHistory();
            
            // Display chat history in chronological order (oldest first)
            if (history && history.length > 0) {
                for (const turn of history) {
                    displayChatTurn(turn.user_message, turn.agent_response, turn.timestamp);
                }
            } else {
                // Show welcome message if no history
                showWelcomeMessage();
            }
            
        } catch (error) {
            console.error('Error loading chat history:', error);
            showToast('Failed to load chat history', 'error');
        }
    }

    function clearConversationHistory() {
        if (conversationHistory) {
            // Remove all chat turns but keep the welcome message structure
            const chatTurns = conversationHistory.querySelectorAll('.chat-turn');
            chatTurns.forEach(turn => turn.remove());
        }
    }

    function showWelcomeMessage() {
        if (conversationHistory) {
            const welcomeExists = conversationHistory.querySelector('.welcome-message');
            if (!welcomeExists) {
                const welcomeMessage = document.createElement('div');
                welcomeMessage.className = 'welcome-message';
                welcomeMessage.innerHTML = `
                    <div class="welcome-icon">
                        <span class="material-icons">🎭</span>
                    </div>
                    <h2>Namaste! I'm RAVI, your Comedy AI Assistant!</h2>
                    <p>Ready for some laughs? Just click the mic and let's chat, yaar! I'll crack jokes while solving your problems. Guaranteed entertainment with every response! 😄</p>
                `;
                conversationHistory.appendChild(welcomeMessage);
            }
        }
    }

    function createNewSession() {
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        loadSession(newSessionId);
    }

    // --- Toast Functions ---
    function showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const iconMap = {
            info: 'info',
            success: 'check_circle',
            warning: 'warning',
            error: 'error',
            retry: 'hourglass_top'
        };

        toast.innerHTML = `
            <div class="toast-header">
                <span class="material-icons">${iconMap[type]}</span>
                ${type.charAt(0).toUpperCase() + type.slice(1)}
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto-remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, duration);
    }

    function showRetryToast(message, attempt, maxRetries) {
        // Remove any existing retry toast
        const existingToast = toastContainer.querySelector('.toast.retry');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = 'toast retry';
        toast.innerHTML = `
            <div class="toast-header">
                <span class="material-icons">hourglass_top</span>
                Retrying...
            </div>
            <div class="toast-body">${message}</div>
            <div class="toast-progress">
                <div class="progress-bar" style="width: ${(attempt / maxRetries) * 100}%"></div>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    // --- Conversation Functions ---
    function displayChatTurn(userMessage, agentResponse, timestamp) {
        // Function to display historical chat turns with WhatsApp-style bubbles
        
        // Format timestamp if it's a string
        let formattedTime = timestamp;
        if (timestamp) {
            try {
                const date = new Date(timestamp);
                formattedTime = date.toLocaleTimeString();
            } catch (e) {
                formattedTime = timestamp;
            }
        } else {
            formattedTime = new Date().toLocaleTimeString();
        }
        
        // Add user message bubble
        addMessageBubble('user', userMessage, formattedTime);
        
        // Add agent response bubble
        setTimeout(() => {
            addMessageBubble('ai', agentResponse, formattedTime);
        }, 100);
    }

    function addMessageBubble(type, content, timestamp = null) {
        // Remove welcome message if it exists
        const welcomeMessage = conversationHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const bubble = document.createElement('div');
        bubble.className = `conversation-bubble ${type}`;
        
        const time = timestamp || new Date().toLocaleTimeString();
        
        // Handle different content types
        let bubbleContent = '';
        if (typeof content === 'string') {
            // Check if content contains HTML (like images)
            if (content.includes('<img') || content.includes('<div')) {
                bubbleContent = content;
            } else {
                bubbleContent = `<p>${content}</p>`;
            }
        } else {
            bubbleContent = `<p>${content}</p>`;
        }
        
        bubble.innerHTML = `
            ${bubbleContent}
            <div class="message-time">${time}</div>
        `;
        
        conversationHistory.appendChild(bubble);
        
        // Scroll to bottom with animation
        setTimeout(() => {
            conversationHistory.scrollTop = conversationHistory.scrollHeight;
        }, 100);
    }

    function addConversationTurn(userMessage, agentResponse) {
        // Save to client-side storage
        clientChatStorage.saveChatTurn(sessionId, userMessage, agentResponse);
        
        // Add user message bubble
        addMessageBubble('user', userMessage);
        
        // Add agent response bubble with slight delay for natural feel
        setTimeout(() => {
            addMessageBubble('ai', agentResponse);
        }, 300);
        
        // Update session list in sidebar
        loadSessions();
    }

    function updateLiveTranscript(text) {
        if (liveTranscript) {
            liveTranscript.textContent = text;
            liveTranscript.classList.add('active');
        }
    }

    function clearLiveTranscript() {
        if (liveTranscript) {
            liveTranscript.textContent = '';
            liveTranscript.classList.remove('active');
        }
    }

    // --- Audio Functions ---
    function base64ToUint8Array(base64) {
        try {
            // Debug suspicious chunks
            if (base64.length === 1000) {
                console.warn(`🔍 [Day 23] Suspicious chunk length: ${base64.length}, starts with: "${base64.substring(0, 50)}..."`);
            }
            
            // Clean the base64 string - remove any whitespace and invalid characters
            let cleanBase64 = base64.replace(/[^A-Za-z0-9+/=]/g, '');
            
            // Ensure proper padding
            const paddingNeeded = (4 - cleanBase64.length % 4) % 4;
            cleanBase64 = cleanBase64 + '='.repeat(paddingNeeded);
            
            // Validate base64 format
            if (!/^[A-Za-z0-9+/]*={0,2}$/.test(cleanBase64)) {
                throw new Error('Invalid base64 format after cleaning');
            }
            
            const binary = atob(cleanBase64);
            const len = binary.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            return bytes;
        } catch (error) {
            console.error('❌ [Day 23] Base64 decode error:', error, 'String length:', base64.length);
            console.error('❌ [Day 23] Problematic chunk preview:', base64.substring(0, 100));
            return null;
        }
    }
    
    // Create WAV header for proper audio playback
    function createWavHeader(dataLength, sampleRate = SAMPLE_RATE, numChannels = 1, bitDepth = 16) {
        const blockAlign = (numChannels * bitDepth) / 8;
        const byteRate = sampleRate * blockAlign;
        const buffer = new ArrayBuffer(44);
        const view = new DataView(buffer);

        function writeStr(offset, str) {
            for (let i = 0; i < str.length; i++) {
                view.setUint8(offset + i, str.charCodeAt(i));
            }
        }

        writeStr(0, "RIFF");
        view.setUint32(4, 36 + dataLength, true);
        writeStr(8, "WAVE");
        writeStr(12, "fmt ");
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitDepth, true);
        writeStr(36, "data");
        view.setUint32(40, dataLength, true);

        return new Uint8Array(buffer);
    }
    
    // Play accumulated chunks as a single audio file
    function playAccumulatedChunks() {
        if (audioChunksForPlayback.length === 0) return;
        
        try {
            console.log(`🎵 [Day 23] Playing ${audioChunksForPlayback.length} accumulated chunks`);
            
            // Reassemble the complete base64 string first
            const completeBase64 = audioChunksForPlayback.join('');
            console.log(`🔗 [Day 23] Reassembled base64 string length: ${completeBase64.length}`);
            
            // Try to decode the complete base64 string
            const bytes = base64ToUint8Array(completeBase64);
            
            if (!bytes) {
                console.error('❌ [Day 23] Failed to decode complete base64 audio string');
                return;
            }
            
            console.log(`✅ [Day 23] Successfully decoded ${bytes.length} bytes from complete base64`);
            
            // Check if it's a WAV file and skip header if needed
            let audioData = bytes;
            if (bytes.length > 44 && bytes[0] === 0x52 && bytes[1] === 0x49) { // "RI" from "RIFF"
                console.log(`🎧 [Day 23] Detected WAV header - using raw PCM data`);
                audioData = bytes.slice(44);
            }
            
            // Create complete WAV file with header
            const wavHeader = createWavHeader(audioData.length);
            const finalWav = new Uint8Array(wavHeader.length + audioData.length);
            finalWav.set(wavHeader, 0);
            finalWav.set(audioData, wavHeader.length);
            
            console.log(`🎼 [Day 23] Created final WAV file: ${finalWav.length} bytes`);
            
            // Create blob and play
            const blob = new Blob([finalWav], { type: "audio/wav" });
            const url = URL.createObjectURL(blob);
            
            // Use the existing audio element
            const audioElement = agentAudio;
            audioElement.src = url;
            audioElement.play().then(() => {
                console.log('✅ [Day 23] Audio playback started successfully');
                audioIndicator.style.display = 'flex';
            }).catch(error => {
                console.error('❌ [Day 23] Audio playback failed:', error);
            });
            
            // Clean up URL after playback
            audioElement.onended = () => {
                URL.revokeObjectURL(url);
                audioIndicator.style.display = 'none';
                console.log('🏁 [Day 23] Audio playback completed');
            };
            
            // Clear the chunks array
            audioChunksForPlayback = [];
            
        } catch (error) {
            console.error('❌ [Day 23] Error playing accumulated chunks:', error);
        }
    }

    // Process audio chunk - accumulate and play when we have enough
    function playAudioChunk(base64Audio) {
        try {
            console.log(`🎵 [Day 23] Received audio chunk (${base64Audio.length} chars)`);
            
            // Add to accumulation array
            audioChunksForPlayback.push(base64Audio);
            
            // Start playing after we have a few chunks (reduces initial artifacts)
            if (!isStreamingStarted && audioChunksForPlayback.length >= 3) {
                isStreamingStarted = true;
                console.log('🎬 [Day 23] Starting accumulated audio playback');
                playAccumulatedChunks();
            }
            
        } catch (error) {
            console.error('❌ [Day 23] Error processing audio chunk:', error);
        }
    }

    // --- Core Functions ---
    async function playFallback(message = "I'm having trouble connecting right now.") {
        agentMessage.textContent = message;
        if ('speechSynthesis' in window) {
            const utter = new SpeechSynthesisUtterance(message);
            window.speechSynthesis.speak(utter);
        }
        updateUI('IDLE');
    }

    const handleInteraction = () => {
        // Check if API keys are configured before allowing interaction
        if (!areApiKeysConfigured()) {
            showApiConfigPrompt();
            return;
        }
        
        switch (agentState) {
            case 'IDLE':
            case 'THINKING': // Allow starting a new recording even if it's thinking
                startRecording();
                break;
            case 'RECORDING':
                stopRecording();
                break;
            case 'SPEAKING':
                // Barge-in implementation
                console.log("--- Barge-in: User interrupted agent ---");
                agentAudio.pause(); // Stop the agent from speaking
                agentAudio.currentTime = 0;
                startRecording(); // Immediately start a new recording
                break;
        }
    };

    const startRecording = async () => {
        console.log('--- Start recording (streaming) ---');
        updateUI('RECORDING');
        
        // Clear previous audio chunks
        audioChunks = [];
        console.log('🗑️ [Day 23] Audio chunks array cleared for new session');
        
        // Reset real-time streaming state
        isPlaying = false;
        isStreamingStarted = false;
        wavHeaderSet = true;
        audioIndicator.style.display = 'none';
        if (streamingAudioContext) {
            playheadTime = streamingAudioContext.currentTime;
        }
        console.log('🔄 [Day 23] Real-time streaming state reset for new session');
        
        // Clear live transcript
        clearLiveTranscript();
        
        try {
            // Initialize WebSocket (include session_id for per-session chat history)
            // Use dynamic WebSocket URL based on current location
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = `${protocol}//${host}/ws/stream-audio?session_id=${encodeURIComponent(sessionId)}`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            ws = new WebSocket(wsUrl);
            ws.onerror = (e) => {
                console.error('WebSocket error:', e);
                playFallback('WebSocket error.');
                showToast('WebSocket connection failed', 'error');
            };
            ws.onclose = () => console.log('WebSocket connection closed');

            // Initialize AudioContext and Worklet
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            await audioContext.audioWorklet.addModule('/static/pcm-processor.js');
            
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const source = audioContext.createMediaStreamSource(stream);
            
            pcmProcessorNode = new AudioWorkletNode(audioContext, 'pcm-processor');
            
            // Connect the source to the processor
            source.connect(pcmProcessorNode);
            
            // The processor will send messages to the main thread
            pcmProcessorNode.port.onmessage = (event) => {
                const pcm16Data = new Int16Array(event.data);
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(pcm16Data.buffer);
                }
            };

            // Handle incoming messages from the server
            ws.onmessage = (event) => {
                try {
                    console.log('Received WebSocket message:', event.data);
                    const message = JSON.parse(event.data);
                    
                    if (message.type === 'turn_end') {
                        console.log('Turn ended:', message.transcript);
                        updateLiveTranscript(message.transcript);
                        updateUI('THINKING');
                    } 
                    // Handle audio data chunks
                    else if (message.type === 'audio_chunk') {
                        console.log(`📻 [Day 23] Received audio chunk: ${message.chunk_id} (${message.data.length} chars)`);
                        
                        // Accumulate the base64 audio chunk
                        audioChunks.push({
                            id: message.chunk_id,
                            data: message.data,
                            timestamp: message.timestamp
                        });
                        
                        console.log(`✅ [Day 23] Audio chunk ${message.chunk_id} added to array. Total chunks: ${audioChunks.length}`);
                        
                        // Play the audio chunk using blob approach
                        playAudioChunk(message.data);
                    }
                    // Handle agent response text
                    else if (message.type === 'agent_response_text') {
                        console.log(`📝 [Day 23] Received agent response text: ${message.text}`);
                        // Store for when audio completes
                        window.lastAgentResponse = message.text;
                    }
                    // Handle retry toast
                    else if (message.type === 'retry_toast') {
                        console.log(`⏳ [Day 23] Showing retry toast: ${message.message}`);
                        showRetryToast(message.message, message.attempt, message.max_retries);
                    }
                    // Handle generated images - NEW DAY 26 FEATURE
                    else if (message.type === 'image_generated') {
                        console.log(`🎨 [Day 26] Image generated: ${message.image_url}`);
                        displayGeneratedImage(message.image_url, message.image_path);
                    }
                    // Handle final audio message
                    else if (message.type === 'audio_complete') {
                        console.log(`🎉 [Day 23] Audio streaming complete! Total chunks received: ${audioChunks.length}`);
                        
                        updateUI('SPEAKING');
                        
                        // Add to conversation history if we have both user and agent messages
                        if (liveTranscript.textContent && window.lastAgentResponse) {
                            addConversationTurn(liveTranscript.textContent, window.lastAgentResponse);
                        }
                        
                        // Reassemble full audio from all chunks and play once
                        const fullBase64 = audioChunks.map(chunk => chunk.data).join('');
                        console.log(`🎞️ [Day 23] Reassembled full audio base64 length: ${fullBase64.length}`);
                        audioChunksForPlayback = [fullBase64];
                        console.log('🎬 [Day 23] Playing final assembled audio');
                        playAccumulatedChunks();
                        
                        // Reset streaming state but keep WebSocket open for continuous conversation
                        setTimeout(() => {
                            isStreamingStarted = false;
                            audioChunksForPlayback = [];
                            audioChunks = [];
                            clearLiveTranscript();
                            // Go back to RECORDING state since WebSocket is still open and listening
                            updateUI('RECORDING');
                            console.log('🔄 [Day 23] Ready for next conversation turn');
                            
                            // Show a subtle toast to indicate ready for next turn
                            showToast('Ready for your next question! 🎤', 'success', 3000);
                        }, 1000);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error, event.data);
                }
            };

            ws.onopen = () => {
                console.log('WebSocket connection opened for audio streaming');
                setupSilenceTimeout();
            };

        } catch (err) {
            playFallback('Microphone or AudioWorklet error.');
            console.error('Error starting recording:', err);
            showToast('Microphone access failed', 'error');
        }
    };

    const stopRecording = () => {
        console.log('--- Stop recording ---');
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
        if (pcmProcessorNode) {
            pcmProcessorNode.disconnect();
            pcmProcessorNode = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        updateUI('IDLE');
    };

    const setupSilenceTimeout = () => {
        clearTimeout(silenceTimeout);
        silenceTimeout = setTimeout(() => {
            console.log("--- Silence detected, stopping recording ---");
            if (agentState === 'RECORDING') {
                stopRecording();
            }
        }, 5000); // 5 seconds of silence
    };

    const updateUI = (state) => {
        agentState = state;
        console.log(`UI updated to state: ${state}`);
        
        // Update button - with null checks
        switch (state) {
            case 'IDLE':
                if (recordBtn) {
                    recordBtn.classList.remove('recording', 'thinking');
                    recordBtn.disabled = false;
                }
                if (icon) icon.textContent = 'mic';
                if (agentMessage) agentMessage.textContent = 'Click the microphone to start';
                if (agentStatusIndicator) agentStatusIndicator.className = 'status-indicator idle';
                if (agentStatusText) agentStatusText.textContent = 'Ready to listen';
                break;
            case 'RECORDING':
                if (recordBtn) {
                    recordBtn.classList.add('recording');
                    recordBtn.classList.remove('thinking');
                    recordBtn.disabled = false;
                }
                if (icon) icon.textContent = 'stop';
                if (agentMessage) agentMessage.textContent = 'Listening... (Click to stop)';
                if (agentStatusIndicator) agentStatusIndicator.className = 'status-indicator listening';
                if (agentStatusText) agentStatusText.textContent = 'Listening for your voice...';
                break;
            case 'THINKING':
                if (recordBtn) {
                    recordBtn.classList.add('thinking');
                    recordBtn.classList.remove('recording');
                    recordBtn.disabled = true;
                }
                if (icon) icon.textContent = 'hourglass_top';
                if (agentMessage) agentMessage.textContent = 'Processing...';
                if (agentStatusIndicator) agentStatusIndicator.className = 'status-indicator processing';
                if (agentStatusText) agentStatusText.textContent = 'Processing your request';
                break;
            case 'SPEAKING':
                if (recordBtn) {
                    recordBtn.classList.remove('recording', 'thinking');
                    recordBtn.disabled = false; // Enable for barge-in
                }
                if (icon) icon.textContent = 'mic_off'; // Indicate user can interrupt
                if (agentMessage) agentMessage.textContent = 'Playing response... (Click to interrupt)';
                if (agentStatusIndicator) agentStatusIndicator.className = 'status-indicator speaking';
                if (agentStatusText) agentStatusText.textContent = 'Speaking...';
                break;
        }
    };

    // --- Event Listeners ---
    if (recordBtn) {
        recordBtn.addEventListener('click', handleInteraction);
    }

    if (agentAudio) {
        agentAudio.onplay = () => updateUI('SPEAKING');
        agentAudio.onended = () => {
            console.log('Agent audio finished.');
            // Check if WebSocket is still open - if so, go back to recording state
            if (ws && ws.readyState === WebSocket.OPEN) {
                updateUI('RECORDING');
                console.log('🎤 Audio finished but still listening for next turn');
            } else {
                updateUI('IDLE');
                console.log('🏁 Audio finished and WebSocket closed');
            }
        };
        agentAudio.onerror = () => playFallback('Error playing agent audio.');
    }

    // --- Day 26: Image Display Function (WhatsApp Style) ---
    function displayGeneratedImage(imageUrl, imagePath) {
        console.log('🎨 Displaying generated image:', imageUrl);
        
        // Create image content for the bubble
        const imageContent = `
            <div style="text-align: center;">
                <h4 style="margin: 0 0 10px 0; color: #4CAF50; font-size: 14px;">🎨 RAVI's Masterpiece</h4>
                <img src="${imageUrl}" alt="Generated by RAVI AI" style="
                    max-width: 100%;
                    max-height: 300px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    cursor: pointer;
                    margin-bottom: 10px;
                " onclick="window.open('${imageUrl}', '_blank')">
                <div>
                    <button onclick="
                        const a = document.createElement('a');
                        a.href = '${imageUrl}';
                        a.download = 'ravi_art_${Date.now()}.png';
                        a.click();
                    " style="
                        padding: 6px 12px;
                        background: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 12px;
                        margin-top: 5px;
                    ">📥 Download</button>
                </div>
            </div>
        `;
        
        // Add image as an AI message bubble
        addMessageBubble('ai', imageContent);
        
        // Show success toast
        showToast('🎨 Image generated successfully! Click to enlarge.', 'success');
    }

    // New session button
    if (newSessionBtn) {
        newSessionBtn.addEventListener('click', createNewSession);
    }

    // --- Initialize UI ---
    updateUI('IDLE');
    loadSessions();
    
    // Load chat history for current session
    loadChatHistory(sessionId);
});
