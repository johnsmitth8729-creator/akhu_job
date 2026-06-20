// Al-Khwarizmi University Recruitment Portal - Drag & Drop File Upload & Previews

document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    const form = document.querySelector('form');
    
    fileInputs.forEach(input => {
        const dropZone = document.getElementById(`drop-zone-${input.id}`);
        const previewContainer = document.getElementById(`preview-${input.id}`);
        
        if (!dropZone || !previewContainer) return;
        
        // Click drop zone to trigger input click
        dropZone.addEventListener('click', () => input.click());
        
        // Drag over effects
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            }, false);
        });
        
        // File drop handler
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                input.files = files;
                handleFileSelect(input, files[0], previewContainer);
            }
        });
        
        // Input file change handler
        input.addEventListener('change', function() {
            if (this.files.length) {
                handleFileSelect(input, this.files[0], previewContainer);
            }
        });
    });
    
    // File validation and preview generation
    function handleFileSelect(input, file, previewContainer) {
        const allowedExtensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'];
        const maxSizeBytes = 20 * 1024 * 1024; // 20 MB
        
        const ext = file.name.split('.').pop().toLowerCase();
        
        // Validate Extension
        if (!allowedExtensions.includes(ext)) {
            alert(`File type .${ext} is not allowed. Supported: PDF, DOC, DOCX, JPG, JPEG, PNG.`);
            input.value = '';
            previewContainer.style.display = 'none';
            return;
        }
        
        // Validate Size
        if (file.size > maxSizeBytes) {
            alert(`File "${file.name}" exceeds the maximum 20 MB size limit.`);
            input.value = '';
            previewContainer.style.display = 'none';
            return;
        }
        
        // Clear previous previews
        previewContainer.innerHTML = '';
        previewContainer.style.display = 'block';
        
        // Create Details Wrapper
        const details = document.createElement('div');
        details.className = 'd-flex align-items-center justify-content-between p-2';
        
        const fileInfo = document.createElement('div');
        fileInfo.className = 'small text-truncate';
        fileInfo.innerHTML = `<strong>${file.name}</strong> <span class="text-muted">(${(file.size / (1024 * 1024)).toFixed(2)} MB)</span>`;
        details.appendChild(fileInfo);
        
        // Check file type for preview
        if (['jpg', 'jpeg', 'png'].includes(ext)) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'img-thumbnail mt-2';
                img.style.maxHeight = '120px';
                img.style.display = 'block';
                
                previewContainer.appendChild(img);
                previewContainer.appendChild(details);
            };
            reader.readAsDataURL(file);
        } else if (ext === 'pdf') {
            const blobUrl = URL.createObjectURL(file);
            const iframe = document.createElement('iframe');
            iframe.src = blobUrl;
            iframe.style.width = '100%';
            iframe.style.height = '180px';
            iframe.style.border = 'none';
            iframe.className = 'rounded mt-2';
            
            previewContainer.appendChild(iframe);
            previewContainer.appendChild(details);
        } else {
            // Word Document representation
            const docWrapper = document.createElement('div');
            docWrapper.className = 'text-center p-3 text-muted';
            docWrapper.innerHTML = `
                <i class="bi bi-file-earmark-word text-primary" style="font-size: 2rem;"></i>
                <div class="mt-1 small">Word Document Preview Unavailable</div>
            `;
            previewContainer.appendChild(docWrapper);
            previewContainer.appendChild(details);
        }
    }
    
    // Bind progress modal on form submit
    if (form && fileInputs.length > 0) {
        form.addEventListener('submit', function(e) {
            // Ensure required fields are filled before launching progress bar
            let valid = true;
            form.querySelectorAll('[required]').forEach(reqInput => {
                if (!reqInput.value) valid = false;
            });
            
            if (!valid) return;
            
            // Create progress modal dynamically if not already in HTML
            let modal = document.getElementById('uploadProgressModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'uploadProgressModal';
                modal.className = 'modal fade';
                modal.setAttribute('data-bs-backdrop', 'static');
                modal.setAttribute('data-bs-keyboard', 'false');
                modal.innerHTML = `
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 glass-panel">
                            <div class="modal-body text-center p-4">
                                <h5 class="mb-3 text-white">Uploading Documents</h5>
                                <p class="text-muted small">Please do not close this tab or refresh the page while files are being securely uploaded.</p>
                                <div class="progress" style="height: 10px; background-color: var(--bg-primary);">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%; background-color: var(--color-accent);"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
            // Show BS modal if bootstrap exists
            if (window.bootstrap && bootstrap.Modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    }
});
