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
    const icon = recordBtn.querySelector('.icon');
    
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

    // Set current session ID in UI
    if (currentSessionId) {
        currentSessionId.textContent = sessionId.split('_')[1] || sessionId.substring(0, 8);
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

    // --- Initialize UI ---
    updateUI('IDLE');
    loadSessions();

    // --- Session Management Functions ---
    async function loadSessions() {
        try {
            const response = await fetch('/api/chat/sessions?limit=20');
            const data = await response.json();
            displaySessions(data.sessions);
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

    function loadSession(newSessionId) {
        // Update URL and reload page with new session
        const newUrl = `${window.location.pathname}?session_id=${newSessionId}`;
        window.location.href = newUrl;
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
    function addConversationTurn(userMessage, agentResponse) {
        // Remove welcome message if it exists
        const welcomeMessage = conversationHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const turnElement = document.createElement('div');
        turnElement.className = 'conversation-turn';
        
        const timestamp = new Date().toLocaleTimeString();
        
        turnElement.innerHTML = `
            <div class="user-message">
                <div class="message-avatar">
                    <span class="material-icons">person</span>
                </div>
                <div class="message-content">
                    ${userMessage}
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
            <div class="agent-message">
                <div class="message-avatar">
                    <span class="material-icons">smart_toy</span>
                </div>
                <div class="message-content">
                    ${agentResponse}
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
        `;
        
        conversationHistory.appendChild(turnElement);
        
        // Scroll to bottom
        conversationHistory.scrollTop = conversationHistory.scrollHeight;
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
            ws = new WebSocket(`ws://localhost:8000/ws/stream-audio?session_id=${encodeURIComponent(sessionId)}`);
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
                        
                        // Reset state for next interaction
                        setTimeout(() => {
                            isStreamingStarted = false;
                            audioChunksForPlayback = [];
                            audioChunks = [];
                            clearLiveTranscript();
                            updateUI('IDLE');
                            console.log('🔄 [Day 23] Audio streaming state reset');
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
        
        // Update button
        switch (state) {
            case 'IDLE':
                recordBtn.classList.remove('recording', 'thinking');
                recordBtn.disabled = false;
                icon.textContent = 'mic';
                agentMessage.textContent = 'Click the microphone to start';
                agentStatusIndicator.className = 'status-indicator idle';
                agentStatusText.textContent = 'Ready to listen';
                break;
            case 'RECORDING':
                recordBtn.classList.add('recording');
                recordBtn.classList.remove('thinking');
                recordBtn.disabled = false;
                icon.textContent = 'stop';
                agentMessage.textContent = 'Listening...';
                agentStatusIndicator.className = 'status-indicator listening';
                agentStatusText.textContent = 'Listening...';
                break;
            case 'THINKING':
                recordBtn.classList.add('thinking');
                recordBtn.classList.remove('recording');
                recordBtn.disabled = true;
                icon.textContent = 'hourglass_top';
                agentMessage.textContent = 'Processing...';
                agentStatusIndicator.className = 'status-indicator processing';
                agentStatusText.textContent = 'Processing your request';
                break;
            case 'SPEAKING':
                recordBtn.classList.remove('recording', 'thinking');
                recordBtn.disabled = false; // Enable for barge-in
                icon.textContent = 'mic_off'; // Indicate user can interrupt
                agentMessage.textContent = 'Playing response...';
                agentStatusIndicator.className = 'status-indicator speaking';
                agentStatusText.textContent = 'Speaking...';
                break;
        }
    };

    // --- Event Listeners ---
    recordBtn.addEventListener('click', handleInteraction);

    agentAudio.onplay = () => updateUI('SPEAKING');
    agentAudio.onended = () => {
        console.log('Agent audio finished.');
        updateUI('IDLE');
    };
    agentAudio.onerror = () => playFallback('Error playing agent audio.');

    // New session button
    if (newSessionBtn) {
        newSessionBtn.addEventListener('click', createNewSession);
    }

    // Initial UI state
    updateUI('IDLE');
});
