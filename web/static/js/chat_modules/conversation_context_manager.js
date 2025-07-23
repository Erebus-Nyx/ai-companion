/**
 * Conversation Context Manager
 * Handles conversation analysis, user attention detection, and context building
 */
class ConversationContextManager {
    constructor(messageHistory = []) {
        this.messageHistory = messageHistory;
        this.contextCache = new Map();
    }

    updateMessageHistory(history) {
        this.messageHistory = history;
        this.contextCache.clear(); // Clear cache when history updates
    }

    // User mood and pattern analysis
    inferUserMood() {
        const recentUserMessages = this.messageHistory
            .filter(msg => msg.type === 'user')
            .slice(-3);
        
        if (recentUserMessages.length === 0) return 'neutral';
        
        const messageTones = recentUserMessages.map(msg => this.analyzeMessageTone(msg.message));
        const dominantTone = this.findDominantEmotion(messageTones);
        
        return dominantTone;
    }

    analyzeMessageTone(message) {
        const lowerMessage = message.toLowerCase();
        
        // Positive indicators
        if (lowerMessage.match(/\b(happy|joy|love|great|awesome|wonderful|amazing|excited|good|nice|thanks|thank you)\b/)) {
            return 'positive';
        }
        
        // Negative indicators
        if (lowerMessage.match(/\b(sad|angry|mad|frustrated|annoyed|upset|hate|terrible|awful|bad|horrible)\b/)) {
            return 'negative';
        }
        
        // Question indicators
        if (message.includes('?')) {
            return 'curious';
        }
        
        // Exclamation indicators
        if (message.includes('!')) {
            return 'enthusiastic';
        }
        
        return 'neutral';
    }

    findDominantEmotion(emotions) {
        const emotionCounts = {};
        emotions.forEach(emotion => {
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        });
        
        return Object.keys(emotionCounts).reduce((a, b) => 
            emotionCounts[a] > emotionCounts[b] ? a : b, 'neutral');
    }

    analyzeUserConversationPattern() {
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user');
        
        if (userMessages.length < 3) return 'insufficient_data';
        
        const avgLength = userMessages.reduce((sum, msg) => sum + msg.message.length, 0) / userMessages.length;
        const questionCount = userMessages.filter(msg => msg.message.includes('?')).length;
        const exclamationCount = userMessages.filter(msg => msg.message.includes('!')).length;
        
        let pattern = 'balanced';
        
        if (avgLength < 20) pattern = 'brief';
        else if (avgLength > 100) pattern = 'verbose';
        
        if (questionCount / userMessages.length > 0.5) pattern = 'inquisitive';
        if (exclamationCount / userMessages.length > 0.3) pattern = 'enthusiastic';
        
        return pattern;
    }

    // User attention and focus detection
    detectUserAttentionFocus(activeAvatars = []) {
        const recentMessages = this.messageHistory.slice(-5);
        const mentionedAvatars = new Set();
        const mentionedTopics = new Set();
        
        recentMessages.forEach(msg => {
            if (msg.type === 'user') {
                // Check for avatar mentions
                activeAvatars.forEach(avatar => {
                    const avatarName = avatar.displayName || avatar.name;
                    if (this.isAvatarNameMentioned(avatar, msg.message)) {
                        mentionedAvatars.add(avatar.id);
                    }
                });
                
                // Extract topic keywords
                const topics = this.extractTopicKeywords(msg.message);
                topics.forEach(topic => mentionedTopics.add(topic));
            }
        });
        
        return {
            focused_avatars: Array.from(mentionedAvatars),
            focused_topics: Array.from(mentionedTopics),
            attention_distribution: this.calculateAttentionDistribution(mentionedAvatars, activeAvatars),
            conversation_focus: mentionedTopics.size > 0 ? 'topic_focused' : 'social_focused'
        };
    }

    isAvatarNameMentioned(avatar, message) {
        const lowerMessage = message.toLowerCase();
        const avatarName = (avatar.displayName || avatar.name || avatar.id).toLowerCase();
        return lowerMessage.includes(avatarName);
    }

    extractTopicKeywords(message) {
        const topics = new Set();
        const lowerMessage = message.toLowerCase();
        
        // Common topic categories
        const topicCategories = {
            emotions: ['feel', 'emotion', 'happy', 'sad', 'angry', 'love', 'like', 'hate'],
            activities: ['do', 'play', 'work', 'game', 'watch', 'read', 'listen'],
            relationships: ['friend', 'love', 'relationship', 'date', 'together'],
            hobbies: ['hobby', 'interest', 'music', 'art', 'sport', 'movie', 'book'],
            personal: ['tell', 'about', 'yourself', 'you', 'me', 'personal', 'story']
        };
        
        Object.entries(topicCategories).forEach(([category, keywords]) => {
            if (keywords.some(keyword => lowerMessage.includes(keyword))) {
                topics.add(category);
            }
        });
        
        return Array.from(topics);
    }

    calculateAttentionDistribution(mentionedAvatars, activeAvatars) {
        const totalAvatars = activeAvatars.length;
        const mentionedCount = mentionedAvatars.size;
        
        if (totalAvatars === 0) return 'none';
        if (mentionedCount === 0) return 'unfocused';
        if (mentionedCount === 1) return 'single_focus';
        if (mentionedCount === totalAvatars) return 'equal_attention';
        return 'partial_focus';
    }

    // User interaction style analysis
    analyzeUserInteractionStyle() {
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user').slice(-10);
        
        if (userMessages.length < 3) return 'unknown';
        
        let directQuestions = 0;
        let statements = 0;
        let commands = 0;
        let casual = 0;
        
        userMessages.forEach(msg => {
            const message = msg.message.toLowerCase();
            
            if (message.includes('?')) directQuestions++;
            else if (message.match(/\b(tell|show|do|go|come|give|help|please)\b/)) commands++;
            else if (message.match(/\b(hi|hey|hello|thanks|yeah|ok|cool|nice)\b/)) casual++;
            else statements++;
        });
        
        const total = userMessages.length;
        if (directQuestions / total > 0.5) return 'questioning';
        if (commands / total > 0.3) return 'directive';
        if (casual / total > 0.5) return 'casual';
        return 'conversational';
    }

    // Environmental and contextual factors
    getEnvironmentalFactors(activeAvatars = []) {
        const timeOfDay = new Date().getHours();
        const activeAvatarCount = activeAvatars.length;
        const conversationLength = this.messageHistory.length;
        
        return {
            time_context: this.getTimeContext(timeOfDay),
            social_context: this.getSocialContext(activeAvatarCount),
            conversation_maturity: this.getConversationMaturity(conversationLength),
            interaction_intensity: this.calculateInteractionIntensity(),
            environmental_mood: this.calculateEnvironmentalMood()
        };
    }

    getTimeContext(hour) {
        if (hour < 6) return 'late_night';
        if (hour < 12) return 'morning';
        if (hour < 17) return 'afternoon';
        if (hour < 21) return 'evening';
        return 'night';
    }

    getSocialContext(avatarCount) {
        if (avatarCount === 0) return 'alone';
        if (avatarCount === 1) return 'private';
        if (avatarCount <= 3) return 'small_group';
        return 'large_group';
    }

    getConversationMaturity(messageCount) {
        if (messageCount < 5) return 'beginning';
        if (messageCount < 20) return 'developing';
        if (messageCount < 50) return 'established';
        return 'extended';
    }

    calculateInteractionIntensity() {
        const recentMessages = this.messageHistory.slice(-10);
        const timeSpan = recentMessages.length > 1 ? 
            new Date(recentMessages[recentMessages.length - 1].timestamp) - 
            new Date(recentMessages[0].timestamp) : 60000;
        
        const messagesPerMinute = (recentMessages.length / (timeSpan / 60000));
        
        if (messagesPerMinute > 3) return 'high';
        if (messagesPerMinute > 1) return 'medium';
        return 'low';
    }

    calculateEnvironmentalMood() {
        const recentEmotions = this.messageHistory
            .slice(-10)
            .filter(msg => msg.primary_emotion)
            .map(msg => msg.primary_emotion);
        
        if (recentEmotions.length === 0) return 'neutral';
        
        const positiveEmotions = ['happy', 'excited', 'friendly', 'caring'];
        const negativeEmotions = ['sad', 'angry', 'frustrated', 'worried'];
        
        const positiveCount = recentEmotions.filter(e => positiveEmotions.includes(e)).length;
        const negativeCount = recentEmotions.filter(e => negativeEmotions.includes(e)).length;
        
        if (positiveCount > negativeCount * 2) return 'positive';
        if (negativeCount > positiveCount * 2) return 'tense';
        return 'mixed';
    }

    // Conversation history utilities
    getRelevantConversationHistory(avatarId, context, limit = 7) {
        let relevantHistory = [];
        
        // Include recent messages involving this avatar
        const avatarMessages = this.messageHistory
            .filter(msg => 
                msg.avatar?.id === avatarId || 
                msg.responding_to === avatarId ||
                this.isAvatarNameMentioned({ id: avatarId, displayName: this.formatAvatarName(avatarId) }, msg.message)
            )
            .slice(-5);
        
        relevantHistory.push(...avatarMessages);
        
        // Include recent general conversation for context
        const generalContext = this.messageHistory.slice(-3);
        generalContext.forEach(msg => {
            if (!relevantHistory.find(rel => rel.timestamp === msg.timestamp)) {
                relevantHistory.push(msg);
            }
        });
        
        // Sort by timestamp
        relevantHistory.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        return relevantHistory.slice(-limit);
    }

    formatAvatarName(modelName) {
        return modelName.charAt(0).toUpperCase() + modelName.slice(1);
    }

    // Avatar interaction analysis
    analyzeAddressingContext(avatar, options = {}) {
        const recentMessages = this.messageHistory.slice(-3);
        const userMessages = recentMessages.filter(msg => msg.type === 'user');
        
        if (userMessages.length === 0) {
            return {
                direct_address: false,
                context_relevance: 'low',
                expected_response: false,
                addressing_confidence: 0.1
            };
        }
        
        const lastUserMessage = userMessages[userMessages.length - 1];
        const avatarName = avatar.displayName || avatar.name || avatar.id;
        
        // Check if avatar is directly mentioned
        const directMention = this.isAvatarNameMentioned(avatar, lastUserMessage.message);
        
        // Check for question directed at avatar
        const hasQuestion = lastUserMessage.message.includes('?');
        
        // Check for general addressing
        const generalAddressing = lastUserMessage.message.toLowerCase().match(/\b(you|your|what|how|why|when|where|who)\b/);
        
        const addressingConfidence = 
            (directMention ? 0.8 : 0) +
            (hasQuestion ? 0.3 : 0) +
            (generalAddressing ? 0.2 : 0) +
            (options.context === 'greeting' ? 0.3 : 0);
        
        return {
            direct_address: directMention || (hasQuestion && generalAddressing),
            context_relevance: addressingConfidence > 0.5 ? 'high' : addressingConfidence > 0.3 ? 'medium' : 'low',
            expected_response: addressingConfidence > 0.4,
            addressing_confidence: Math.min(1.0, addressingConfidence),
            question_present: hasQuestion,
            general_addressing: !!generalAddressing
        };
    }

    // Cache management
    clearCache() {
        this.contextCache.clear();
    }
}

// Export for use in other modules
window.ConversationContextManager = ConversationContextManager;
