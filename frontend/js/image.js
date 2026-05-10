/* ═══════════════════════════════════════════════════════════
   MediMind AI — Image Upload Handler
   Drag-and-drop + click-to-upload with preview
   ═══════════════════════════════════════════════════════════ */

const ImageHandler = {
    init() {
        const imageInput = document.getElementById('image-input');
        const removeBtn = document.getElementById('image-remove-btn');
        const chatArea = document.getElementById('chat-area');

        if (imageInput) {
            imageInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) this.handleImage(file);
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', () => this.clearImage());
        }

        // Drag and drop on chat area
        if (chatArea) {
            chatArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                chatArea.style.outline = '2px dashed var(--accent-primary)';
                chatArea.style.outlineOffset = '-4px';
            });

            chatArea.addEventListener('dragleave', () => {
                chatArea.style.outline = 'none';
            });

            chatArea.addEventListener('drop', (e) => {
                e.preventDefault();
                chatArea.style.outline = 'none';

                const file = e.dataTransfer.files[0];
                if (file && file.type.startsWith('image/')) {
                    this.handleImage(file);
                } else {
                    showToast('Please drop an image file', 'error');
                }
            });
        }
    },

    handleImage(file) {
        // Validate
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        if (!validTypes.includes(file.type)) {
            showToast('Please upload a valid image (JPEG, PNG, GIF, WebP)', 'error');
            return;
        }

        // 10MB limit
        if (file.size > 10 * 1024 * 1024) {
            showToast('Image must be under 10MB', 'error');
            return;
        }

        // Store pending image in Chat module
        Chat.pendingImage = file;

        // Show preview
        const previewBar = document.getElementById('image-preview-bar');
        const previewImg = document.getElementById('image-preview-img');

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewBar.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Enable send button
        document.getElementById('send-btn').disabled = false;
        showToast('Image ready. Add a description or click send.', 'info', 2500);
    },

    clearImage() {
        Chat.pendingImage = null;
        document.getElementById('image-preview-bar').style.display = 'none';
        document.getElementById('image-input').value = '';

        // Re-check send button state
        const input = document.getElementById('message-input');
        document.getElementById('send-btn').disabled = !input.value.trim();
    },
};
