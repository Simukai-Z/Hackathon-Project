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
        if (!gameResult) {
            console.warn('No game result provided to AI popup');
            return;
        }
        
        console.log('AI popup showing with result:', gameResult);
        
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
        if (this.overlay) {
            this.overlay.style.display = 'flex';
            this.overlay.classList.add('show');
            this.isVisible = true;
            
            // Auto-scroll to top
            if (this.body) this.body.scrollTop = 0;
            
            console.log('AI popup displayed with message');
        } else {
            console.error('AI popup overlay not found!');
        }
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
                excellent: [
                    `🎉 EXCELLENT WORK! You absolutely crushed "${gameResult.set_name}" with ${gameResult.accuracy}% accuracy and ${gameResult.score} points!`,
                    `Your mastery of this material is impressive! You're clearly putting in the effort and it's paying off beautifully.`,
                    `You should be proud of this achievement - this level of performance shows real understanding, not just memorization. Keep this momentum going!`
                ],
                great: [
                    `🌟 GREAT JOB! You conquered "${gameResult.set_name}" with ${gameResult.accuracy}% accuracy and ${gameResult.score} points!`,
                    `Your study skills are really developing well. This kind of consistent performance shows you're building solid learning habits.`,
                    `You're doing exactly what successful students do - engaging actively with the material and testing your knowledge. Excellent work!`
                ],
                good: [
                    `✨ WELL DONE! You successfully completed "${gameResult.set_name}" with ${gameResult.accuracy}% accuracy and ${gameResult.score} points!`,
                    `Every successful study session like this builds your confidence and knowledge. You're making steady, meaningful progress.`,
                    `Your dedication to learning is evident. Consider this a solid foundation to build upon as you continue mastering these concepts.`
                ]
            },
            loss: {
                close: [
                    `💪 YOU'RE SO CLOSE! Great attempt on "${gameResult.set_name}" - you scored ${gameResult.score} points with ${gameResult.accuracy}% accuracy!`,
                    `Your performance shows you understand most of the concepts really well. You were just a few points away from mastering this!`,
                    `Don't get discouraged - this is exactly how learning works. You're building knowledge with each attempt. Try reviewing the tricky cards and come back for another round!`
                ],
                learning: [
                    `📚 GREAT EFFORT! Learning "${gameResult.set_name}" takes practice, and you're doing exactly what you should - you scored ${gameResult.score} points with ${gameResult.accuracy}% accuracy.`,
                    `Every attempt like this helps solidify the concepts in your memory. You're making real progress, even if it doesn't feel like it yet.`,
                    `Remember, struggling with new material is completely normal and actually a sign that you're challenging yourself appropriately. Keep going!`
                ],
                encouraging: [
                    `🌱 YOU'RE LEARNING! Working on "${gameResult.set_name}" is challenging, and you're tackling it with determination - you scored ${gameResult.score} points with ${gameResult.accuracy}% accuracy.`,
                    `Your ${gameResult.accuracy}% accuracy shows you're grasping some key concepts. Every correct answer represents real understanding building in your mind.`,
                    `Learning is a journey, not a destination. Each study session, each attempt, each question you engage with is moving you forward. You're doing great by simply showing up and trying!`
                ]
            }
        };
        
        // Determine message category with more detailed performance levels
        let category, subcategory;
        if (gameResult.is_win) {
            category = 'win';
            if (gameResult.accuracy >= 95 && gameResult.score >= 80) subcategory = 'excellent';
            else if (gameResult.accuracy >= 80 || gameResult.score >= 60) subcategory = 'great';
            else subcategory = 'good';
        } else {
            category = 'loss';
            if (gameResult.accuracy >= 65) subcategory = 'close';
            else if (gameResult.accuracy >= 40) subcategory = 'learning';
            else subcategory = 'encouraging';
        }
        
        const messageArray = messages[category][subcategory];
        const selectedMessages = [...messageArray]; // Take all messages for this category
        
        // Add personalized study tips based on performance
        const studyTips = this.getPersonalizedStudyTips(gameResult);
        if (studyTips) {
            selectedMessages.push(studyTips);
        }
        
        return `
            <div class="ai-message">
                ${selectedMessages.map(msg => `<p>${msg}</p>`).join('')}
            </div>
        `;
    }
    
    getPersonalizedStudyTips(gameResult) {
        const excellentTips = [
            `🎯 <strong>Advanced Strategy:</strong> Since you're mastering this material, try explaining these concepts to someone else or teaching them - it's the ultimate test of understanding!`,
            `🚀 <strong>Level Up:</strong> You're ready for more challenging material! Consider exploring related advanced topics or taking on harder question types.`,
            `⭐ <strong>Mastery Tip:</strong> Try creating your own questions about this material - it's what experts do to deepen their understanding.`
        ];
        
        const goodTips = [
            `💡 <strong>Study Tip:</strong> Focus on the cards you missed - review them in study mode, then try the game again. Targeted practice is super effective!`,
            `🧠 <strong>Memory Hack:</strong> Try creating mental images or stories connecting the concepts - your brain loves visual and narrative connections!`,
            `🔄 <strong>Spaced Learning:</strong> Come back to this material tomorrow or in a few days. Your brain consolidates memories better with spaced repetition.`,
            `📝 <strong>Active Learning:</strong> Write out the key concepts in your own words. The act of writing engages different parts of your brain and strengthens memory.`
        ];
        
        const strugglingTips = [
            `📖 <strong>Foundation Building:</strong> Spend some time in study mode going through each card slowly. Understanding comes before memorization.`,
            `🗣️ <strong>Learning Hack:</strong> Read the questions and answers out loud - hearing information activates additional memory pathways in your brain.`,
            `🎯 <strong>Focus Strategy:</strong> Pick 3-5 cards that seem most important and focus on mastering just those first. Small wins build confidence!`,
            `🤝 <strong>Study Buddy:</strong> Consider studying with a friend or asking someone to quiz you. Social learning can make difficult concepts click!`,
            `⏰ <strong>Patience Tip:</strong> Remember that everyone learns at their own pace. Some concepts take time to sink in, and that's completely normal and okay.`
        ];
        
        // Choose tips based on performance
        let tipPool;
        if (gameResult.is_win && gameResult.accuracy >= 90) {
            tipPool = excellentTips;
        } else if (gameResult.is_win || gameResult.accuracy >= 60) {
            tipPool = goodTips;
        } else {
            tipPool = strugglingTips;
        }
        
        // Return a random tip from the appropriate pool
        return tipPool[Math.floor(Math.random() * tipPool.length)];
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
        
        // Create comprehensive game results data for AI context
        const enhancedGameResults = {
            set_name: gameResult.set_name,
            score: gameResult.score,
            accuracy: gameResult.accuracy,
            total_questions: gameResult.total_questions,
            correct_answers: gameResult.correct_answers,
            performance_level: gameResult.performance_level || 'unknown',
            is_win: gameResult.is_win,
            average_time: gameResult.average_time || 0,
            lives_remaining: gameResult.lives_remaining || 0,
            detailed_results: gameResult.detailed_results || [],
            timestamp: new Date().toISOString()
        };
        
        const aiUrl = `/ai?game_results=${encodeURIComponent(JSON.stringify(enhancedGameResults))}`;
        window.location.href = aiUrl;
    } else {
        window.location.href = '/ai';
    }
}

function tryGameAgain() {
    // Close the AI popup
    if (window.aiPopup) {
        window.aiPopup.hide();
    }
    
    // Call the global tryGameAgain function if it exists
    if (window.tryGameAgain && typeof window.tryGameAgain === 'function') {
        window.tryGameAgain();
    }
    // Fallback: look for the function in the global scope
    else if (typeof tryGameAgain === 'function') {
        tryGameAgain();
    }
    // Last resort: reload the page to reset the game
    else {
        window.location.reload();
    }
}

// Initialize popup when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.aiPopup = new AIGamePopup();
});
