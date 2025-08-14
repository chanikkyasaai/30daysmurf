document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FastAPI Voice Agents Challenge - Day 12 Loaded');

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

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // --- Core Functions ---
    async function playFallback() {
        const fallbackText = "I'm having trouble connecting right now.";
        agentMessage.textContent = fallbackText;
        if ('speechSynthesis' in window) {
            const utter = new SpeechSynthesisUtterance(fallbackText);
            window.speechSynthesis.speak(utter);
        }
        resetUI();
    }

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const startRecording = async () => {
        console.log('--- Start recording ---');
        agentMessage.textContent = 'Listening...';
        agentAudio.style.display = 'none';
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };
            mediaRecorder.onstop = handleRecordingStop;
            mediaRecorder.start();
            
            isRecording = true;
            recordBtn.classList.add('recording');
            icon.textContent = 'stop';
        } catch (err) {
            agentMessage.textContent = 'Microphone access denied.';
            console.error('Microphone error:', err);
            resetUI();
        }
    };

    const stopRecording = () => {
        console.log('--- Stop recording ---');
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.classList.remove('recording');
            icon.textContent = 'mic';
            agentMessage.textContent = 'Thinking...';
        }
    };

    const handleRecordingStop = async () => {
        console.log('--- Handling recording stop ---');
        if (audioChunks.length === 0) {
            console.error("No audio recorded.");
            agentMessage.textContent = 'No audio was recorded.';
            resetUI();
            return;
        }
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
                agentMessage.textContent = 'Playing response...';
            } else {
                await playFallback();
            }
        } catch (err) {
            await playFallback();
        }
    };

    const resetUI = () => {
        isRecording = false;
        recordBtn.classList.remove('recording');
        icon.textContent = 'mic';
        recordBtn.disabled = false;
        agentMessage.textContent = 'Click the mic to start';
    };

    // --- Event Listeners ---
    recordBtn.addEventListener('click', toggleRecording);

    agentAudio.addEventListener('ended', () => {
        console.log('Agent audio finished, starting new recording.');
        agentMessage.textContent = 'Your turn...';
        setTimeout(startRecording, 500);
    });

    agentAudio.addEventListener('error', async () => {
        console.error('Error playing agent audio.');
        await playFallback();
    });

    agentAudio.onplay = () => {
        recordBtn.disabled = true;
    };

    agentAudio.onended = () => {
        resetUI();
        setTimeout(startRecording, 500); // Auto-record again
    };

    // Initial UI state
    resetUI();
});