/**
 * Avatar Interaction Manager
 * Handles multi-avatar conversations, avatar-to-avatar interactions, and response orchestration
 */
class AvatarInteractionManager {
    constructor() {
        this.activeAvatars = new Map();
        this.interactionQueue = [];
        this.lastSpeaker = null;
        this.conversationTurn = 0;
        this.interactionHistory = [];
    }

    // Update active avatars list
    updateActiveAvatars(avatarsMap) {
        this.activeAvatars = new Map(avatarsMap);
        console.log(`🎭 Avatar Interaction Manager updated with ${this.activeAvatars.size} active avatars`);
    }

    // Determine which avatar should respond to user input
    async determineResponder(userMessage, context = {}) {
        const activeAvatarList = Array.from(this.activeAvatars.values());
        if (activeAvatarList.length === 0) {
            console.warn('⚠️ No active avatars available for response');
            return null;
        }

        if (activeAvatarList.length === 1) {
            return activeAvatarList[0];
        }

        // Get managers
        const personalityManager = window.avatarPersonalityManager || new AvatarPersonalityManager();
        const conversationManager = window.conversationContextManager || new ConversationContextManager();

        // Analyze user attention and addressing
        const userAttention = conversationManager.detectUserAttentionFocus(activeAvatarList);
        
        // If user directly addressed an avatar, that avatar should respond
        if (userAttention.focused_avatars.length === 1) {
            const targetAvatarId = userAttention.focused_avatars[0];
            const targetAvatar = this.activeAvatars.get(targetAvatarId);
            if (targetAvatar) {
                console.log(`🎯 User directly addressed ${targetAvatar.displayName}`);
                return targetAvatar;
            }
        }

        // Calculate response probabilities for each avatar
        const responseProbabilities = await this.calculateResponseProbabilities(
            activeAvatarList, 
            userMessage, 
            context,
            personalityManager,
            conversationManager
        );

        // Select responder based on probabilities
        const selectedAvatar = this.selectAvatarByProbability(responseProbabilities);
        
        console.log(`🎭 Selected ${selectedAvatar.displayName} to respond (probability: ${responseProbabilities.find(p => p.avatar.id === selectedAvatar.id)?.probability.toFixed(2)})`);
        
        return selectedAvatar;
    }

    async calculateResponseProbabilities(avatarList, userMessage, context, personalityManager, conversationManager) {
        const probabilities = [];

        for (const avatar of avatarList) {
            const personality = await personalityManager.getAvatarPersonalityTraits(avatar.id);
            const behavioralConstraints = await personalityManager.calculateBehavioralConstraints(avatar.id, context);
            const addressingContext = conversationManager.analyzeAddressingContext(avatar, context);

            let probability = this.calculateBaseProbability(personality);
            
            // Adjust for addressing context
            if (addressingContext.direct_address) {
                probability *= 3.0; // Strong boost for direct addressing
            } else if (addressingContext.expected_response) {
                probability *= 1.5; // Moderate boost for implied addressing
            }

            // Adjust for conversation flow
            probability *= this.calculateConversationFlowModifier(avatar, userMessage);
            
            // Adjust for behavioral constraints
            if (behavioralConstraints.response_threshold > 0.7) {
                probability *= 0.3; // Reduce for shy/hesitant avatars
            }

            // Adjust for recent activity (avoid same avatar responding too often)
            probability *= this.calculateRecencyModifier(avatar.id);

            // Adjust for personality-specific response likelihood
            probability *= this.calculatePersonalityResponseModifier(personality, userMessage, context);

            probabilities.push({
                avatar: avatar,
                probability: Math.max(0.01, Math.min(1.0, probability)),
                factors: {
                    base: this.calculateBaseProbability(personality),
                    addressing: addressingContext.addressing_confidence,
                    flow: this.calculateConversationFlowModifier(avatar, userMessage),
                    constraints: 1.0 - (behavioralConstraints.response_threshold - 0.3),
                    recency: this.calculateRecencyModifier(avatar.id),
                    personality: this.calculatePersonalityResponseModifier(personality, userMessage, context)
                }
            });
        }

        return probabilities;
    }

    calculateBaseProbability(personality) {
        // Base probability influenced by extroversion and confidence
        const extroversionFactor = personality.extroversion || 0.5;
        const confidenceFactor = personality.confidence || 0.5;
        return (extroversionFactor + confidenceFactor) / 2;
    }

    calculateConversationFlowModifier(avatar, userMessage) {
        // Check if this avatar was recently mentioned or involved in conversation
        const recentMentions = this.interactionHistory
            .slice(-5)
            .filter(interaction => 
                interaction.target_avatar === avatar.id || 
                interaction.responding_avatar === avatar.id
            ).length;

        if (recentMentions > 2) return 1.2; // Active in conversation
        if (recentMentions === 0) return 0.8; // Not recently involved
        return 1.0; // Normal involvement
    }

    calculateRecencyModifier(avatarId) {
        // Reduce probability if this avatar spoke recently
        const recentSpeakers = this.interactionHistory
            .slice(-3)
            .map(interaction => interaction.responding_avatar);

        const timesRecentlySpoke = recentSpeakers.filter(id => id === avatarId).length;
        
        if (timesRecentlySpoke >= 2) return 0.4; // Spoke multiple times recently
        if (timesRecentlySpoke === 1) return 0.7; // Spoke once recently
        return 1.0; // Hasn't spoken recently
    }

    calculatePersonalityResponseModifier(personality, userMessage, context) {
        let modifier = 1.0;
        const lowerMessage = userMessage.toLowerCase();

        // Question-responsive personalities
        if (userMessage.includes('?') && personality.openness > 0.6) {
            modifier *= 1.3;
        }

        // Emotionally responsive personalities
        if (this.containsEmotionalContent(lowerMessage) && personality.empathy > 0.6) {
            modifier *= 1.2;
        }

        // Flirtatious personalities respond more to certain contexts
        if (personality.flirtatious > 0.5 && this.containsFlirtatiousOpportunity(lowerMessage)) {
            modifier *= 1.4;
        }

        // Helpful personalities respond to requests
        if (this.containsHelpRequest(lowerMessage) && personality.agreeableness > 0.6) {
            modifier *= 1.3;
        }

        return modifier;
    }

    containsEmotionalContent(message) {
        const emotionalWords = ['feel', 'emotion', 'happy', 'sad', 'angry', 'love', 'heart', 'excited', 'worried'];
        return emotionalWords.some(word => message.includes(word));
    }

    containsFlirtatiousOpportunity(message) {
        const flirtTriggers = ['cute', 'beautiful', 'attractive', 'like you', 'about you', 'date', 'together'];
        return flirtTriggers.some(trigger => message.includes(trigger));
    }

    containsHelpRequest(message) {
        const helpWords = ['help', 'can you', 'would you', 'please', 'could you', 'advice', 'suggest'];
        return helpWords.some(word => message.includes(word));
    }

    selectAvatarByProbability(probabilities) {
        // Weighted random selection based on probabilities
        const totalProbability = probabilities.reduce((sum, p) => sum + p.probability, 0);
        
        if (totalProbability === 0) {
            // Fallback to random selection
            return probabilities[Math.floor(Math.random() * probabilities.length)].avatar;
        }

        let random = Math.random() * totalProbability;
        
        for (const prob of probabilities) {
            random -= prob.probability;
            if (random <= 0) {
                return prob.avatar;
            }
        }

        // Fallback to first avatar
        return probabilities[0].avatar;
    }

    // Check if avatars should interact with each other
    async checkForAvatarToAvatarInteractions(triggeringMessage, respondingAvatar) {
        const activeAvatarList = Array.from(this.activeAvatars.values())
            .filter(avatar => avatar.id !== respondingAvatar.id);

        if (activeAvatarList.length === 0) return [];

        const interactions = [];
        const personalityManager = window.avatarPersonalityManager || new AvatarPersonalityManager();

        for (const avatar of activeAvatarList) {
            const shouldInteract = await this.shouldAvatarInteract(
                avatar, 
                respondingAvatar, 
                triggeringMessage,
                personalityManager
            );

            if (shouldInteract.interact) {
                interactions.push({
                    avatar: avatar,
                    interaction_type: shouldInteract.type,
                    probability: shouldInteract.probability,
                    delay: shouldInteract.delay
                });
            }
        }

        return interactions.sort((a, b) => b.probability - a.probability);
    }

    async shouldAvatarInteract(avatar, respondingAvatar, triggeringMessage, personalityManager) {
        const personality = await personalityManager.getAvatarPersonalityTraits(avatar.id);
        const respondingPersonality = await personalityManager.getAvatarPersonalityTraits(respondingAvatar.id);

        // Base interaction probability
        let probability = personality.extroversion * 0.3 + personality.agreeableness * 0.2;

        // Relationship dynamics
        const relationshipDynamic = this.analyzeAvatarRelationship(avatar.id, respondingAvatar.id);
        probability *= relationshipDynamic.interaction_likelihood;

        // Context-specific triggers
        const contextTriggers = this.analyzeInteractionTriggers(
            triggeringMessage, 
            personality, 
            respondingPersonality
        );
        probability *= contextTriggers.multiplier;

        // Timing considerations
        const timingFactor = this.calculateInteractionTiming(avatar.id);
        probability *= timingFactor;

        const interact = probability > 0.3 && Math.random() < probability;

        return {
            interact: interact,
            type: contextTriggers.type || 'supportive_comment',
            probability: probability,
            delay: this.calculateInteractionDelay(personality, contextTriggers.type)
        };
    }

    analyzeAvatarRelationship(avatarId1, avatarId2) {
        // Analyze relationship between two avatars based on their personalities and history
        // This would ideally be stored in database, but for now use personality compatibility
        
        return {
            interaction_likelihood: 0.6, // Base likelihood
            relationship_type: 'friendly',
            conflict_potential: 0.2,
            support_tendency: 0.7
        };
    }

    analyzeInteractionTriggers(message, personality, respondingPersonality) {
        let multiplier = 1.0;
        let type = 'supportive_comment';

        const lowerMessage = message.toLowerCase();

        // Disagreement triggers
        if (this.containsControversialContent(lowerMessage) && personality.agreeableness < 0.4) {
            multiplier = 1.5;
            type = 'disagreement';
        }

        // Support triggers  
        if (this.containsEmotionalContent(lowerMessage) && personality.empathy > 0.6) {
            multiplier = 1.3;
            type = 'emotional_support';
        }

        // Competitive triggers
        if (personality.dominant > 0.6 && respondingPersonality.dominant > 0.6) {
            multiplier = 1.2;
            type = 'competitive_banter';
        }

        // Flirtatious triggers
        if (personality.flirtatious > 0.5 && this.containsFlirtatiousOpportunity(lowerMessage)) {
            multiplier = 1.4;
            type = 'flirtatious_interjection';
        }

        return { multiplier, type };
    }

    containsControversialContent(message) {
        const controversialWords = ['wrong', 'disagree', 'no way', 'nonsense', 'ridiculous'];
        return controversialWords.some(word => message.includes(word));
    }

    calculateInteractionTiming(avatarId) {
        // Reduce probability if avatar has interacted very recently
        const recentInteractions = this.interactionHistory
            .slice(-2)
            .filter(interaction => interaction.responding_avatar === avatarId);

        if (recentInteractions.length > 0) return 0.5;
        return 1.0;
    }

    calculateInteractionDelay(personality, interactionType) {
        let baseDelay = 2000; // 2 seconds

        // Extroverted avatars respond faster
        if (personality.extroversion > 0.7) baseDelay *= 0.7;
        
        // Thoughtful avatars take more time
        if (personality.conscientiousness > 0.7) baseDelay *= 1.3;

        // Type-specific delays
        switch (interactionType) {
            case 'disagreement':
                baseDelay *= 1.5; // More time to think before disagreeing
                break;
            case 'flirtatious_interjection':
                baseDelay *= 0.8; // Quick flirtatious responses
                break;
            case 'emotional_support':
                baseDelay *= 1.2; // Thoughtful support
                break;
        }

        return baseDelay + (Math.random() * 2000); // Add some randomness
    }

    // Record interaction for future analysis
    recordInteraction(respondingAvatarId, targetAvatarId, interactionType, context) {
        this.interactionHistory.push({
            timestamp: Date.now(),
            responding_avatar: respondingAvatarId,
            target_avatar: targetAvatarId,
            interaction_type: interactionType,
            context: context,
            turn: this.conversationTurn++
        });

        // Keep only last 20 interactions to prevent memory issues
        if (this.interactionHistory.length > 20) {
            this.interactionHistory = this.interactionHistory.slice(-20);
        }

        this.lastSpeaker = respondingAvatarId;
    }

    // Get interaction statistics for debugging
    getInteractionStats() {
        const stats = {
            total_interactions: this.interactionHistory.length,
            active_avatars: this.activeAvatars.size,
            last_speaker: this.lastSpeaker,
            conversation_turn: this.conversationTurn,
            avatar_participation: {}
        };

        // Calculate participation stats
        this.interactionHistory.forEach(interaction => {
            const avatarId = interaction.responding_avatar;
            if (!stats.avatar_participation[avatarId]) {
                stats.avatar_participation[avatarId] = 0;
            }
            stats.avatar_participation[avatarId]++;
        });

        return stats;
    }

    // Clear history when conversation resets
    clearHistory() {
        this.interactionHistory = [];
        this.lastSpeaker = null;
        this.conversationTurn = 0;
        console.log('🔄 Avatar interaction history cleared');
    }
}

// Export for use in other modules
window.AvatarInteractionManager = AvatarInteractionManager;
