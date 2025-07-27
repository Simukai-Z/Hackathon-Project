
// Fixed modal handling for teacher grading
function showGradingModal(classroomId, assignmentId, studentEmail, studentName, assignmentTitle, currentGrade, currentFeedback) {
    // Create modal elements if they don't exist
    let modal = document.getElementById('gradingModal');
    if (!modal) {
        modal = createGradingModal();
    }
    
    // Populate modal fields safely
    const form = modal.querySelector('#gradingForm');
    if (form) {
        form.querySelector('[name="classroom_id"]').value = classroomId || '';
        form.querySelector('[name="assignment_id"]').value = assignmentId || '';
        form.querySelector('[name="student_email"]').value = studentEmail || '';
        form.querySelector('[name="grade"]').value = currentGrade || '';
        form.querySelector('[name="feedback"]').value = currentFeedback || '';
        
        // Update modal title safely
        const titleElement = modal.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = `Grade Assignment: ${assignmentTitle || 'Unknown'}`;
        }
        
        // Update student name safely  
        const studentElement = modal.querySelector('.student-name');
        if (studentElement) {
            studentElement.textContent = `Student: ${studentName || studentEmail || 'Unknown'}`;
        }
    }
    
    // Show modal
    modal.style.display = 'flex';
    
    // Focus on grade input
    const gradeInput = modal.querySelector('[name="grade"]');
    if (gradeInput) {
        gradeInput.focus();
    }
}

// Enhanced version using data attributes (recommended)
function showGradingModalFromData(button) {
    const classroomId = button.dataset.classroomId;
    const assignmentId = button.dataset.assignmentId;
    const studentEmail = button.dataset.studentEmail;
    const studentName = button.dataset.studentName;
    const assignmentTitle = button.dataset.assignmentTitle;
    const currentGrade = button.dataset.currentGrade;
    const currentFeedback = button.dataset.currentFeedback;
    
    showGradingModal(classroomId, assignmentId, studentEmail, studentName, assignmentTitle, currentGrade, currentFeedback);
}

function createGradingModal() {
    const modalHTML = `
    <div class="modal-overlay" id="gradingModal" style="display: none;">
        <div class="modal-dialog">
            <div class="modal-header">
                <h5 class="modal-title">Grade Assignment</h5>
                <button type="button" class="close-modal" onclick="closeModal('gradingModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="student-name"></div>
                <form id="gradingForm" method="post" action="/grade_assignment">
                    <input type="hidden" name="classroom_id" value="">
                    <input type="hidden" name="assignment_id" value="">
                    <input type="hidden" name="student_email" value="">
                    
                    <div class="form-group">
                        <label for="grade">Grade (0-100):</label>
                        <input type="number" name="grade" min="0" max="100" required class="form-control">
                    </div>
                    
                    <div class="form-group">
                        <label for="feedback">Feedback:</label>
                        <textarea name="feedback" rows="4" class="form-control"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="use_ai" value="true">
                            Enhance feedback with AI
                        </label>
                    </div>
                    
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-primary">Save Grade</button>
                        <button type="button" class="btn btn-secondary" onclick="closeModal('gradingModal')">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    return document.getElementById('gradingModal');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// AI Grading modal
function showAIGradingModal(classroomId, assignmentId, studentEmail, studentName, assignmentTitle) {
    if (confirm(`Use AI to grade ${studentName || studentEmail}'s assignment "${assignmentTitle || 'Unknown'}"?`)) {
        // Create and submit form for AI grading
        const form = document.createElement('form');
        form.method = 'post';
        form.action = '/ai_grade_assignment';
        
        const fields = {
            'classroom_id': classroomId,
            'assignment_id': assignmentId,
            'student_email': studentEmail
        };
        
        for (const [name, value] of Object.entries(fields)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            input.value = value || '';
            form.appendChild(input);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Initialize modal system when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Convert any remaining onclick attributes to data-driven approach
    const gradingButtons = document.querySelectorAll('[onclick*="showGradingModal"]');
    gradingButtons.forEach(button => {
        // Extract parameters from onclick attribute and convert to data attributes
        const onclickAttr = button.getAttribute('onclick');
        if (onclickAttr) {
            // This is a fallback - ideally templates should use data attributes directly
            console.warn('Found onclick attribute, consider updating template to use data attributes');
        }
    });
});

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility function to safely set text content
function safeSetText(element, text) {
    if (element) {
        element.textContent = text || '';
    }
}
