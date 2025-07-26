// Theme Management
function initializeTheme() {
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.body.classList.add('dark-mode');
    }

    // Listen for system theme changes
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        }
    });
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
    `;
    container.appendChild(toast);

    // Auto-remove toast after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || icons.info;
}

// Page Transitions
function initializePageTransitions() {
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href.startsWith(window.location.origin)) {
            e.preventDefault();
            document.body.style.opacity = '0';
            setTimeout(() => {
                window.location.href = link.href;
            }, 300);
        }
    });

    window.addEventListener('pageshow', () => {
        document.body.style.opacity = '1';
    });
}

// File Upload UI Enhancement
function initializeFileUploads() {
    document.querySelectorAll('input[type="file"]').forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.className = 'file-upload-wrapper';
        
        const label = document.createElement('label');
        label.className = 'file-upload-label';
        label.innerHTML = '<span>Choose a file</span> or drag it here';
        
        const preview = document.createElement('div');
        preview.className = 'file-preview';
        
        wrapper.appendChild(label);
        wrapper.appendChild(preview);
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Drag and drop functionality
        wrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            wrapper.classList.add('dragover');
        });

        wrapper.addEventListener('dragleave', () => {
            wrapper.classList.remove('dragover');
        });

        wrapper.addEventListener('drop', (e) => {
            e.preventDefault();
            wrapper.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                updateFilePreview(input, preview);
            }
        });

        input.addEventListener('change', () => {
            updateFilePreview(input, preview);
        });
    });
}

function updateFilePreview(input, preview) {
    preview.innerHTML = '';
    if (input.files.length) {
        const file = input.files[0];
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-name">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;
        preview.appendChild(item);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Form Validation and Enhancement
function initializeForms() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!form.checkValidity()) {
                e.preventDefault();
                highlightInvalidFields(form);
            }
        });

        // Real-time validation
        form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', () => {
                validateField(field);
            });
        });
    });
}

function validateField(field) {
    if (field.checkValidity()) {
        field.classList.remove('invalid');
        field.classList.add('valid');
    } else {
        field.classList.remove('valid');
        field.classList.add('invalid');
    }
}

function highlightInvalidFields(form) {
    form.querySelectorAll('input, textarea, select').forEach(validateField);
}

// Initialize all features when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializePageTransitions();
    initializeFileUploads();
    initializeForms();
});

// Handle back/forward navigation
window.addEventListener('popstate', () => {
    document.body.style.opacity = '1';
});
