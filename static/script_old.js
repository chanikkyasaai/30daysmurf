document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FastAPI Voice Agents Challenge - Day 23 Complete Voice Agent Loaded');

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
    
    // --- New Elements for Transcript Display ---
    const currentTranscript = document.getElementById('current-transcript');
    const transcriptHistory = document.getElementById('transcript-history');
    const audioIndicator = document.getElementById('audio-indicator');

    // --- New Elements for Agent Response and Chat History ---
    const agentResponseSection = document.getElementById('agent-response-section');
    const agentResponseText = document.getElementById('agent-response-text');
    const chatHistoryDisplay = document.getElementById('chat-history-display');
    const loadHistoryBtn = document.getElementById('load-history-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    // --- State Management ---
    let mediaRecorder;
    let ws;
    let audioContext;
    let pcmProcessorNode;
    let agentState = 'IDLE';
    let silenceTimeout;
    
    // --- Day 21: Audio Data Accumulation ---
    let audioChunks = []; // Array to accumulate base64 audio chunks
    
    // --- Day 22: Audio Playback ---
    let streamingAudioContext; // Separate audio context for playback
    let playheadTime;
    let isPlaying = false;
    let wavHeaderSet = true;
    let audioChunksForPlayback = []; // Store base64 chunks for blob creation
    let currentAudioElement;
    let isStreamingStarted = false;
    const SAMPLE_RATE = 44100;

    // --- Day 22: Blob-Based Audio Streaming (Production Ready) ---
    
    // Convert base64 to Uint8Array for blob creation (with robust error handling)
    function base64ToUint8Array(base64) {
        try {
            // Debug suspicious chunks
            if (base64.length === 1000) {
                console.warn(`🔍 [Day 22] Suspicious chunk length: ${base64.length}, starts with: "${base64.substring(0, 50)}..."`);
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
            console.error('❌ [Day 22] Base64 decode error:', error, 'String length:', base64.length);
            console.error('❌ [Day 22] Problematic chunk preview:', base64.substring(0, 100));
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
    
    // Play accumulated chunks as a single audio file (robust reassembly approach)
    function playAccumulatedChunks() {
        if (audioChunksForPlayback.length === 0) return;
        
        try {
            console.log(`🎵 [Day 22] Playing ${audioChunksForPlayback.length} accumulated chunks`);
            
            // Reassemble the complete base64 string first
            const completeBase64 = audioChunksForPlayback.join('');
            console.log(`🔗 [Day 22] Reassembled base64 string length: ${completeBase64.length}`);
            
            // Try to decode the complete base64 string
            const bytes = base64ToUint8Array(completeBase64);
            
            if (!bytes) {
                console.error('❌ [Day 22] Failed to decode complete base64 audio string');
                return;
            }
            
            console.log(`✅ [Day 22] Successfully decoded ${bytes.length} bytes from complete base64`);
            
            // Check if it's a WAV file and skip header if needed
            let audioData = bytes;
            if (bytes.length > 44 && bytes[0] === 0x52 && bytes[1] === 0x49) { // "RI" from "RIFF"
                console.log(`🎧 [Day 22] Detected WAV header - using raw PCM data`);
                audioData = bytes.slice(44);
            }
            
            // Create complete WAV file with header
            const wavHeader = createWavHeader(audioData.length);
            const finalWav = new Uint8Array(wavHeader.length + audioData.length);
            finalWav.set(wavHeader, 0);
            finalWav.set(audioData, wavHeader.length);
            
            console.log(`🎼 [Day 22] Created final WAV file: ${finalWav.length} bytes`);
            
            // Create blob and play
            const blob = new Blob([finalWav], { type: "audio/wav" });
            const url = URL.createObjectURL(blob);
            
            // Use the existing audio element
            const audioElement = agentAudio;
            audioElement.src = url;
            audioElement.play().then(() => {
                console.log('✅ [Day 22] Audio playback started successfully');
                audioIndicator.style.display = 'block';
            }).catch(error => {
                console.error('❌ [Day 22] Audio playback failed:', error);
            });
            
            // Clean up URL after playback
            audioElement.onended = () => {
                URL.revokeObjectURL(url);
                audioIndicator.style.display = 'none';
                console.log('🏁 [Day 22] Audio playback completed');
            };
            
            // Clear the chunks array
            audioChunksForPlayback = [];
            
        } catch (error) {
            console.error('❌ [Day 22] Error playing accumulated chunks:', error);
        }
    }


    // Process audio chunk - accumulate and play when we have enough
    function playAudioChunk(base64Audio) {
        try {
            console.log(`🎵 [Day 22] Received audio chunk (${base64Audio.length} chars)`);
            
            // Add to accumulation array
            audioChunksForPlayback.push(base64Audio);
            
            // Start playing after we have a few chunks (reduces initial artifacts)
            if (!isStreamingStarted && audioChunksForPlayback.length >= 3) {
                isStreamingStarted = true;
                console.log('🎬 [Day 22] Starting accumulated audio playback');
                playAccumulatedChunks();
            }
            
        } catch (error) {
            console.error('❌ [Day 22] Error processing audio chunk:', error);
        }
    }

    // --- Day 23: Toast Functions ---
    function showRetryToast(message, attempt, maxRetries) {
        // Remove any existing retry toast
        const existingToast = document.querySelector('.retry-toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = 'retry-toast';
        toast.innerHTML = `
            <div class="toast-header">
                <span class="material-icons">hourglass_top</span>
                Retrying...
            </div>
            <div class="toast-body">
                ${message}
            </div>
            <div class="toast-progress">
                <div class="progress-bar" style="width: ${(attempt / maxRetries) * 100}%"></div>
            </div>
        `;
        
        document.body.appendChild(toast);
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

    function showAgentResponse(text) {
        agentResponseText.textContent = text;
        agentResponseSection.style.display = 'block';
        
        // Auto-scroll to show the response
        agentResponseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // --- Day 23: Chat History Functions ---
    async function loadChatHistory() {
        try {
            const response = await fetch(`/api/chat/history/${sessionId}?limit=10`);
            const data = await response.json();
            displayChatHistory(data.history);
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    async function clearChatHistory() {
        if (confirm('Are you sure you want to clear the chat history for this session?')) {
            try {
                const response = await fetch(`/api/chat/history/${sessionId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    chatHistoryDisplay.innerHTML = '<p class="no-history">Chat history cleared.</p>';
                    agentResponseSection.style.display = 'none';
                } else {
                    console.error('Failed to clear chat history');
                }
            } catch (error) {
                console.error('Error clearing chat history:', error);
            }
        }
    }

    function displayChatHistory(history) {
        if (history.length === 0) {
            chatHistoryDisplay.innerHTML = '<p class="no-history">No chat history found.</p>';
            return;
        }

        const historyHtml = history.reverse().map(turn => `
            <div class="chat-turn">
                <div class="user-message">
                    <strong>You:</strong> ${turn.user_message}
                </div>
                <div class="agent-message">
                    <strong>Agent:</strong> ${turn.agent_response}
                </div>
                <div class="timestamp">${new Date(turn.timestamp).toLocaleString()}</div>
            </div>
        `).join('');

        chatHistoryDisplay.innerHTML = historyHtml;
    }
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
        
        // Day 21: Clear previous audio chunks
        audioChunks = [];
        console.log('🗑️ [Day 21] Audio chunks array cleared for new session');
        
        // Day 22: Reset real-time streaming state
        rawAudioChunks = [];
        audioQueue = [];
        isPlaying = false;
        isStreamingStarted = false;
        wavHeaderSet = true;
        audioIndicator.style.display = 'none'; // Hide audio indicator
        if (streamingAudioContext) {
            playheadTime = streamingAudioContext.currentTime;
        }
        console.log('🔄 [Day 22] Real-time streaming state reset for new session');
        
        try {
            // Initialize WebSocket (include session_id for per-session chat history)
            ws = new WebSocket(`ws://localhost:8000/ws/stream-audio?session_id=${encodeURIComponent(sessionId)}`);
            ws.onerror = (e) => {
                console.error('WebSocket error:', e);
                playFallback('WebSocket error.');
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

            // Handle incoming messages from the server (turn detection)
            ws.onmessage = (event) => {
                try {
                    console.log('Received WebSocket message:', event.data);
                    const message = JSON.parse(event.data);
                    
                    if (message.type === 'turn_end') {
                        console.log('Turn ended:', message.transcript);
                        displayTranscript(message.transcript, message.timestamp);
                    } 
                    // Day 21 & 22: Handle audio data chunks
                    else if (message.type === 'audio_chunk') {
                        console.log(`📻 [Day 21] Received audio chunk: ${message.chunk_id} (${message.data.length} chars)`);
                        
                        // Day 21: Accumulate the base64 audio chunk
                        audioChunks.push({
                            id: message.chunk_id,
                            data: message.data,
                            timestamp: message.timestamp
                        });
                        
                        // Print acknowledgement
                        console.log(`✅ [Day 21] Audio chunk ${message.chunk_id} added to array. Total chunks: ${audioChunks.length}`);
                        console.log(`📊 [Day 21] Audio chunks array:`, audioChunks.map(chunk => ({
                            id: chunk.id,
                            dataLength: chunk.data.length,
                            timestamp: chunk.timestamp
                        })));
                        
                        // Day 22: Play the audio chunk using blob approach
                        playAudioChunk(message.data);
                    }
                    // Day 23: Handle agent response text
                    else if (message.type === 'agent_response_text') {
                        console.log(`📝 [Day 23] Received agent response text: ${message.text}`);
                        showAgentResponse(message.text);
                    }
                    // Day 23: Handle retry toast
                    else if (message.type === 'retry_toast') {
                        console.log(`⏳ [Day 23] Showing retry toast: ${message.message}`);
                        showRetryToast(message.message, message.attempt, message.max_retries);
                    }
                    // Handle final audio message
                    else if (message.type === 'audio_complete') {
                        console.log(`🎉 [Day 21] Audio streaming complete! Total chunks received: ${audioChunks.length}`);
                        console.log(`📈 [Day 21] Total base64 audio data: ${audioChunks.reduce((total, chunk) => total + chunk.data.length, 0)} characters`);
                        
                        // Day 22: Reassemble full audio from all chunks and play once
                        const fullBase64 = audioChunks.map(chunk => chunk.data).join('');
                        console.log(`🎞️ [Day 22] Reassembled full audio base64 length: ${fullBase64.length}`);
                        audioChunksForPlayback = [fullBase64];
                        console.log('🎬 [Day 22] Playing final assembled audio');
                        playAccumulatedChunks();
                        
                        // Reset state for next interaction
                        setTimeout(() => {
                            isStreamingStarted = false;
                            audioChunksForPlayback = [];
                            audioChunks = [];
                            console.log('🔄 [Day 22] Audio streaming state reset');
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

    const displayTranscript = (transcript, timestamp) => {
        // Clear current transcript display
        currentTranscript.textContent = '';
        
        // Show toast notification for turn detection
        showTurnDetectionToast(transcript);
        
        // Add to history
        const transcriptItem = document.createElement('div');
        transcriptItem.className = 'transcript-item';
        
        const timeString = new Date(timestamp * 1000).toLocaleTimeString();
        transcriptItem.innerHTML = `
            <span class="timestamp">[${timeString}]</span>
            <span class="transcript-text">${transcript}</span>
        `;
        
        // Add to the top of history
        transcriptHistory.insertBefore(transcriptItem, transcriptHistory.firstChild);
        
        // Keep only the last 10 transcripts
        while (transcriptHistory.children.length > 10) {
            transcriptHistory.removeChild(transcriptHistory.lastChild);
        }
        
        // Update the agent message to show the latest transcript
        agentMessage.textContent = `Latest: "${transcript}"`;
        
        // Auto-scroll to show the latest transcript
        transcriptHistory.scrollTop = 0;
    };

    const showTurnDetectionToast = (transcript) => {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'turn-detection-toast';
        toast.innerHTML = `
            <div class="toast-header">
                <span class="material-icons">volume_off</span>
                Turn Detected!
            </div>
            <div class="toast-body">
                You stopped speaking. Transcript captured.
            </div>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    };

    const handleRecordingStop = async () => {
        // This is now handled by stopRecording()
    };

    const updateUI = (state) => {
        agentState = state;
        console.log(`UI updated to state: ${state}`);
        switch (state) {
            case 'IDLE':
                recordBtn.classList.remove('recording', 'thinking');
                recordBtn.disabled = false;
                icon.textContent = 'mic';
                agentMessage.textContent = 'Click the mic to start';
                break;
            case 'RECORDING':
                recordBtn.classList.add('recording');
                recordBtn.classList.remove('thinking');
                recordBtn.disabled = false;
                icon.textContent = 'stop';
                agentMessage.textContent = 'Listening...';
                break;
            case 'THINKING':
                recordBtn.classList.add('thinking');
                recordBtn.classList.remove('recording');
                recordBtn.disabled = true;
                icon.textContent = 'hourglass_top';
                agentMessage.textContent = 'Thinking...';
                break;
            case 'SPEAKING':
                recordBtn.classList.remove('recording', 'thinking');
                recordBtn.disabled = false; // Enable for barge-in
                icon.textContent = 'mic_off'; // Indicate user can interrupt
                agentMessage.textContent = 'Playing response...';
                break;
        }
    };

    // --- Event Listeners ---
    recordBtn.addEventListener('click', handleInteraction);

    agentAudio.onplay = () => updateUI('SPEAKING');
    agentAudio.onended = () => {
        console.log('Agent audio finished.');
        updateUI('IDLE');
        // Optional: auto-record again after agent finishes
        // setTimeout(startRecording, 500);
    };
    agentAudio.onerror = () => playFallback('Error playing agent audio.');

    // Day 23: Chat History Event Listeners
    loadHistoryBtn.addEventListener('click', loadChatHistory);
    clearHistoryBtn.addEventListener('click', clearChatHistory);

    // Initial UI state
    updateUI('IDLE');
    
    // Load chat history on page load
    loadChatHistory();
});