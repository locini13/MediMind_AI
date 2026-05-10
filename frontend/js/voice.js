/* ═══════════════════════════════════════════════════════════
   MediMind AI — Voice Recording Module
   Uses MediaRecorder API for voice capture
   ═══════════════════════════════════════════════════════════ */

const VoiceHandler = {
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
    stream: null,

    init() {
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.toggleRecording());
        }
    },

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    },

    async startRecording() {
        try {
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                    ? 'audio/webm;codecs=opus'
                    : 'audio/webm',
            });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.audioChunks = [];

                // Stop all tracks
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                    this.stream = null;
                }

                // Send to chat handler
                if (audioBlob.size > 0) {
                    Chat.sendVoiceMessage(audioBlob);
                }
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateUI(true);
            showToast('Recording... Click again to stop', 'info', 2000);

        } catch (error) {
            console.error('Microphone access error:', error);
            if (error.name === 'NotAllowedError') {
                showToast('Microphone access denied. Please allow microphone access in browser settings.', 'error');
            } else {
                showToast('Could not start voice recording. Check your microphone.', 'error');
            }
        }
    },

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        this.isRecording = false;
        this.updateUI(false);
    },

    updateUI(recording) {
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            if (recording) {
                voiceBtn.classList.add('recording');
            } else {
                voiceBtn.classList.remove('recording');
            }
        }
    },
};
