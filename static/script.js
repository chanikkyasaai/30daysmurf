document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FastAPI Voice Agents Challenge - Day 15 Loaded');

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

    // --- State Management ---
    let mediaRecorder;
    let audioChunks = [];
    let agentState = 'IDLE'; // IDLE, RECORDING, THINKING, SPEAKING
    let silenceTimeout;

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
        console.log('--- Start recording ---');
        updateUI('RECORDING');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                    // If we receive data, reset the silence timeout
                    clearTimeout(silenceTimeout);
                    setupSilenceTimeout();
                }
            };

            mediaRecorder.onstop = handleRecordingStop;
            mediaRecorder.start();
            
            // Initial silence timeout
            setupSilenceTimeout();

        } catch (err) {
            playFallback('Microphone access denied.');
            console.error('Microphone error:', err);
        }
    };

    const stopRecording = () => {
        console.log('--- Stop recording ---');
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop(); // This will trigger onstop event
        }
    };

    const setupSilenceTimeout = () => {
        clearTimeout(silenceTimeout);
        silenceTimeout = setTimeout(() => {
            console.log("--- Silence detected, stopping recording ---");
            playFallback("I didn't hear anything, please try again.");
            if (agentState === 'RECORDING') {
                stopRecording();
            }
            updateUI('IDLE');
        }, 5000); // 5 seconds of silence
    };

    const handleRecordingStop = async () => {
        clearTimeout(silenceTimeout);
        if (audioChunks.length === 0) {
            console.error("No audio recorded.");
            updateUI('IDLE');
            return;
        }
        
        updateUI('THINKING');
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        try {
            const formData = new FormData();
            formData.append('file', audioBlob, `recording-${Date.now()}.webm`);
            
            const response = await fetch(`/agent/chat/${sessionId}`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                agentAudio.src = data.audio_url;
                // Audio will autoplay due to 'autoplay' attribute
            } else {
                await playFallback();
            }
        } catch (err) {
            await playFallback();
        }
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

    // Initial UI state
    updateUI('IDLE');
});