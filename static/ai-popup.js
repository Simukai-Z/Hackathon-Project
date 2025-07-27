/**
 * AI Game Results Popup Functionality
 * Enhanced popup for displaying personalized AI messages after game completion
 */

class AIGamePopup {
    constructor() {
        this.overlay = document.getElementById('ai-popup-overlay');
        this.popup = document.getElementById('ai-popup');
        this.body = document.getElementById('ai-popup-body');
        this.stats = document.getElementById('ai-game-stats');
        this.scoreElement = document.getElementById('ai-final-score');
        this.accuracyElement = document.getElementById('ai-final-accuracy');
        this.currentGameResult = null;
        this.isVisible = false;
        
        // Bind methods
        this.show = this.show.bind(this);
        this.hide = this.hide.bind(this);
        this.generateAIMessage = this.generateAIMessage.bind(this);
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Close on overlay click
        if (this.overlay) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.hide();
                }
            });
        }
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });
    }
    
    setCurrentGameResult(gameResult) {
        this.currentGameResult = gameResult;
    }
    
    async show(gameResult) {
        if (!gameResult) gameResult = this.currentGameResult;
        if (!gameResult || !this.overlay) return;
        
        this.currentGameResult = gameResult;
        
        // Update stats
        if (this.scoreElement) this.scoreElement.textContent = gameResult.score || 0;
        if (this.accuracyElement) this.accuracyElement.textContent = `${gameResult.accuracy || 0}%`;
        if (this.stats) this.stats.style.display = 'grid';
        
        // Generate AI message
        const aiMessage = await this.generateAIMessage(gameResult);
        if (this.body) this.body.innerHTML = aiMessage;
        
        // Update popup style based on win/loss
        if (this.popup) {
            this.popup.className = gameResult.is_win ? 'ai-popup win' : 'ai-popup loss';
        }
        
        // Show popup with animation
        this.overlay.style.display = 'flex';
        this.isVisible = true;
        
        // Trigger animation
        setTimeout(() => {
            this.overlay.classList.add('show');
        }, 50);
        
        // Auto-scroll to top
        if (this.body) this.body.scrollTop = 0;
        
        // Add typing effect to the message
        this.addTypingEffect();
    }
    
    hide() {
        if (!this.overlay) return;
        
        this.overlay.classList.remove('show');
        this.isVisible = false;
        
        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 300);
    }
    
    async generateAIMessage(gameResult) {
        const messages = {
            win: {
                high_score: [
                    `🎉 Outstanding performance! You've mastered "${gameResult.set_name}" with ${gameResult.accuracy}% accuracy and ${gameResult.score} points!`,
                    `Your dedication to studying is really paying off! This level of mastery shows you truly understand the material.`,
                    `Ready to challenge yourself with more advanced topics? You're clearly ready for the next level!`
                ],
                good_score: [
                    `🌟 Great work on "${gameResult.set_name}"! You achieved ${gameResult.accuracy}% accuracy with ${gameResult.score} points.`,
                    `You're developing strong study skills and it shows in your performance.`,
                    `Keep this momentum going - you're building excellent learning habits!`
                ],
                basic_win: [
                    `✨ Well done! You completed "${gameResult.set_name}" successfully with ${gameResult.accuracy}% accuracy.`,
                    `Every study session helps reinforce your knowledge. You're making steady progress!`,
                    `Consider reviewing the concepts you found challenging to strengthen your understanding.`
                ]
            },
            loss: {
                close_call: [
                    `💪 Good effort on "${gameResult.set_name}"! You scored ${gameResult.score} points with ${gameResult.accuracy}% accuracy.`,
                    `You were so close to mastering this! Your progress shows you're learning effectively.`,
                    `Try reviewing the flashcards once more, then come back for another challenge. You've got this!`
                ],
                needs_review: [
                    `📚 Thanks for practicing "${gameResult.set_name}"! You scored ${gameResult.score} points with ${gameResult.accuracy}% accuracy.`,
                    `This material can be challenging, but that's how we grow! Every attempt helps build your knowledge.`,
                    `I recommend spending some time reviewing the cards in study mode, then trying the game again.`
                ],
                encouraging: [
                    `🌱 Learning takes time, and you're making progress with "${gameResult.set_name}"!`,
                    `Your ${gameResult.accuracy}% accuracy shows you're grasping the concepts. Keep building on that foundation.`,
                    `Remember, every expert was once a beginner. Stay curious and keep practicing!`
                ]
            }
        };
        
        // Determine message category
        let category, subcategory;
        if (gameResult.is_win) {
            category = 'win';
            if (gameResult.accuracy >= 90) subcategory = 'high_score';
            else if (gameResult.accuracy >= 75) subcategory = 'good_score';
            else subcategory = 'basic_win';
        } else {
            category = 'loss';
            if (gameResult.accuracy >= 70) subcategory = 'close_call';
            else if (gameResult.accuracy >= 50) subcategory = 'needs_review';
            else subcategory = 'encouraging';
        }
        
        const messageArray = messages[category][subcategory];
        const selectedMessages = messageArray.slice(0, 2); // Take first 2 messages
        
        // Add personalized study tips
        const studyTips = this.getStudyTips(gameResult);
        if (studyTips) {
            selectedMessages.push(studyTips);
        }
        
        return `
            <div class="ai-message">
                ${selectedMessages.map(msg => `<p>${msg}</p>`).join('')}
            </div>
        `;
    }
    
    getStudyTips(gameResult) {
        const tips = [
            `💡 <strong>Study Tip:</strong> Try the spaced repetition technique - review difficult cards more frequently than easy ones.`,
            `🎯 <strong>Pro Tip:</strong> Create connections between concepts to improve retention and understanding.`,
            `🧠 <strong>Learning Hack:</strong> Explain the concepts out loud as if teaching someone else - it strengthens memory!`,
            `⚡ <strong>Quick Tip:</strong> Take short breaks between study sessions to help your brain consolidate information.`,
            `🔄 <strong>Strategy:</strong> Mix up the order of your flashcards to avoid relying on sequence memory.`
        ];
        
        if (gameResult.accuracy < 70) {
            return tips[Math.floor(Math.random() * tips.length)];
        }
        
        return null;
    }
    
    addTypingEffect() {
        if (!this.body) return;
        
        const messages = this.body.querySelectorAll('p');
        messages.forEach((msg, index) => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                msg.style.opacity = '1';
                msg.style.transform = 'translateY(0)';
                msg.style.transition = 'all 0.5s ease';
            }, index * 500);
        });
    }
}

// Global functions for popup controls
function closeAIPopup() {
    if (window.aiPopup) {
        window.aiPopup.hide();
    }
}

function goToAIAssistant() {
    if (window.aiPopup && window.aiPopup.currentGameResult) {
        const gameResult = window.aiPopup.currentGameResult;
        const aiUrl = `/ai?game_results=${encodeURIComponent(JSON.stringify({
            set_name: gameResult.set_name,
            score: gameResult.score,
            accuracy: gameResult.accuracy,
            is_win: gameResult.is_win,
            message: gameResult.message
        }))}`;
        window.location.href = aiUrl;
    } else {
        window.location.href = '/ai';
    }
}

// Initialize popup when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.aiPopup = new AIGamePopup();
});
