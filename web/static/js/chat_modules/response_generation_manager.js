/**
 * Response Generation Manager
 * Handles AI message generation, context building, and response validation
 */
class ResponseGenerationManager {
    constructor() {
        this.responseCache = new Map();
        this.generationInProgress = new Set();
    }

    // Main response generation method
    async generateAutonomousMessage(avatar, messageType, context = {}) {
        const cacheKey = `${avatar.id}_${messageType}_${JSON.stringify(context)}`;
        
        // Check if generation is already in progress for this request
        if (this.generationInProgress.has(cacheKey)) {
            console.log(`⏳ Response generation already in progress for ${avatar.displayName}`);
            return null;
        }

        this.generationInProgress.add(cacheKey);

        try {
            // Build comprehensive context for AI generation
            const aiContext = await this.buildAIGenerationContext(avatar, messageType, context);
            
            // Generate response using AI API
            const response = await this.callAIGenerationAPI(avatar, aiContext);
            
            // Validate and process response
            const processedResponse = await this.processAIResponse(response, avatar, aiContext);
            
            this.generationInProgress.delete(cacheKey);
            return processedResponse;

        } catch (error) {
            console.error(`❌ Error generating autonomous message for ${avatar.displayName}:`, error);
            this.generationInProgress.delete(cacheKey);
            return this.getFallbackResponse(avatar, messageType, context);
        }
    }

    async buildAIGenerationContext(avatar, messageType, context) {
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        // Get personality manager instance
        const personalityManager = window.avatarPersonalityManager || new AvatarPersonalityManager();
        const conversationManager = window.conversationContextManager || new ConversationContextManager();

        // Get comprehensive avatar context
        const personalityTraits = await personalityManager.getAvatarPersonalityTraits(avatar.id);
        const contentCapabilities = await personalityManager.getAvatarContentCapabilities(avatar.id);
        const behavioralConstraints = personalityManager.calculateBehavioralConstraints(avatar.id, context);

        // Get conversation context
        const userAttention = conversationManager.detectUserAttentionFocus([avatar]);
        const environmentalFactors = conversationManager.getEnvironmentalFactors([avatar]);
        const conversationHistory = conversationManager.getRelevantConversationHistory(avatar.id, context);

        return {
            avatar: {
                id: avatar.id,
                name: avatar.displayName || avatar.name,
                personality_traits: personalityTraits,
                content_capabilities: contentCapabilities,
                behavioral_constraints: behavioralConstraints
            },
            message_type: messageType,
            context: {
                ...context,
                user_attention: userAttention,
                environmental_factors: environmentalFactors,
                conversation_history: conversationHistory,
                addressing_analysis: conversationManager.analyzeAddressingContext(avatar, context)
            },
            generation_parameters: {
                response_style: this.determineResponseStyle(personalityTraits, context),
                emotional_tone: this.determineEmotionalTone(personalityTraits, environmentalFactors),
                content_filtering: this.buildContentFiltering(contentCapabilities, behavioralConstraints),
                contextual_awareness: this.buildContextualAwareness(userAttention, environmentalFactors)
            }
        };
    }

    async callAIGenerationAPI(avatar, aiContext) {
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        const requestBody = {
            avatar_id: avatar.id,
            message_type: aiContext.message_type,
            context: aiContext.context,
            personality: aiContext.avatar.personality_traits,
            generation_params: aiContext.generation_parameters,
            conversation_history: aiContext.context.conversation_history,
            environmental_context: aiContext.context.environmental_factors
        };

        console.log('🤖 Sending AI generation request:', requestBody);

        const response = await fetch(`${apiBaseUrl}/api/chat/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`AI generation API failed: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('🤖 AI generation response:', data);
        
        return data;
    }

    async processAIResponse(response, avatar, aiContext) {
        if (!response || !response.message) {
            throw new Error('Invalid AI response format');
        }

        // Extract message content
        let messageContent = response.message;
        if (typeof messageContent === 'object' && messageContent.content) {
            messageContent = messageContent.content;
        }

        // Validate content appropriateness
        const isAppropriate = await this.validateContentAppropriateness(
            messageContent, 
            aiContext.generation_parameters.content_filtering
        );

        if (!isAppropriate) {
            console.warn('⚠️ Generated content failed appropriateness check, using fallback');
            return this.getFallbackResponse(avatar, aiContext.message_type, aiContext.context);
        }

        // Build final response object
        return {
            message: messageContent,
            avatar: avatar,
            timestamp: new Date().toISOString(),
            type: 'avatar',
            message_type: aiContext.message_type,
            emotional_tone: response.emotional_tone || aiContext.generation_parameters.emotional_tone,
            personality_expression: response.personality_expression || [],
            generated_by: 'ai_api',
            confidence: response.confidence || 0.8
        };
    }

    determineResponseStyle(personalityTraits, context) {
        return {
            formality: personalityTraits.conscientiousness > 0.6 ? 'formal' : 'casual',
            verbosity: personalityTraits.extroversion > 0.6 ? 'verbose' : 'concise',
            directness: personalityTraits.confidence > 0.7 ? 'direct' : 'subtle',
            emotional_expression: personalityTraits.extroversion > 0.6 ? 'expressive' : 'reserved',
            humor_level: personalityTraits.playfulness > 0.6 ? 'high' : 'moderate',
            personality_emphasis: this.calculatePersonalityEmphasis(personalityTraits, context)
        };
    }

    determineEmotionalTone(personalityTraits, environmentalFactors) {
        const baseEmotion = environmentalFactors.environmental_mood || 'neutral';
        const personalityModifier = this.calculateEmotionalModifier(personalityTraits);
        
        return {
            primary_emotion: this.blendEmotions(baseEmotion, personalityModifier),
            intensity: this.calculateEmotionalIntensity(personalityTraits, environmentalFactors),
            stability: personalityTraits.emotional_stability || 0.7,
            expressiveness: personalityTraits.extroversion || 0.5
        };
    }

    buildContentFiltering(contentCapabilities, behavioralConstraints) {
        return {
            nsfw_allowed: contentCapabilities.nsfw_capable && 
                         behavioralConstraints.content_filters?.allow_nsfw_content,
            mature_themes_allowed: contentCapabilities.mature_content_capable && 
                                  behavioralConstraints.content_filters?.allow_mature_themes,
            personality_expression_level: behavioralConstraints.content_filters?.personality_expression_level || 'moderate',
            content_boundaries: this.defineContentBoundaries(contentCapabilities, behavioralConstraints)
        };
    }

    buildContextualAwareness(userAttention, environmentalFactors) {
        return {
            user_focus: userAttention.attention_distribution,
            conversation_flow: userAttention.conversation_focus,
            social_context: environmentalFactors.social_context,
            time_awareness: environmentalFactors.time_context,
            interaction_intensity: environmentalFactors.interaction_intensity
        };
    }

    calculatePersonalityEmphasis(personalityTraits, context) {
        const emphasis = [];
        
        // Emphasize dominant personality traits
        if (personalityTraits.seductive > 0.7) emphasis.push('seductive');
        if (personalityTraits.flirtatious > 0.7) emphasis.push('flirtatious');
        if (personalityTraits.confidence > 0.8) emphasis.push('confident');
        if (personalityTraits.playfulness > 0.7) emphasis.push('playful');
        if (personalityTraits.mischievous > 0.6) emphasis.push('mischievous');
        
        return emphasis;
    }

    calculateEmotionalModifier(personalityTraits) {
        if (personalityTraits.extroversion > 0.7) return 'enthusiastic';
        if (personalityTraits.agreeableness > 0.8) return 'warm';
        if (personalityTraits.neuroticism > 0.6) return 'anxious';
        if (personalityTraits.openness > 0.7) return 'curious';
        return 'balanced';
    }

    blendEmotions(baseEmotion, modifier) {
        const emotionBlends = {
            'neutral_enthusiastic': 'friendly',
            'positive_enthusiastic': 'excited',
            'neutral_warm': 'caring',
            'positive_warm': 'loving',
            'neutral_curious': 'interested',
            'positive_curious': 'eager'
        };
        
        const blendKey = `${baseEmotion}_${modifier}`;
        return emotionBlends[blendKey] || baseEmotion;
    }

    calculateEmotionalIntensity(personalityTraits, environmentalFactors) {
        let intensity = 0.5; // Base intensity
        
        // Personality modifiers
        if (personalityTraits.intensity > 0.6) intensity += 0.2;
        if (personalityTraits.extroversion > 0.7) intensity += 0.1;
        if (personalityTraits.neuroticism > 0.6) intensity += 0.15;
        
        // Environmental modifiers
        if (environmentalFactors.interaction_intensity === 'high') intensity += 0.1;
        if (environmentalFactors.environmental_mood === 'positive') intensity += 0.05;
        
        return Math.min(1.0, Math.max(0.1, intensity));
    }

    defineContentBoundaries(contentCapabilities, behavioralConstraints) {
        return {
            max_suggestiveness: this.calculateMaxSuggestiveness(contentCapabilities, behavioralConstraints),
            emotional_openness: this.calculateEmotionalOpenness(contentCapabilities, behavioralConstraints),
            topic_freedom: this.calculateTopicFreedom(contentCapabilities, behavioralConstraints),
            personality_authenticity: this.calculatePersonalityAuthenticity(contentCapabilities, behavioralConstraints)
        };
    }

    calculateMaxSuggestiveness(capabilities, constraints) {
        if (!capabilities.nsfw_capable) return 'none';
        if (!constraints.content_filters?.allow_nsfw_content) return 'mild';
        if (constraints.content_filters?.personality_expression_level === 'high') return 'moderate';
        return 'mild';
    }

    calculateEmotionalOpenness(capabilities, constraints) {
        const baseOpenness = capabilities.explicit_content_comfort === 'high' ? 0.8 : 0.5;
        const constraintModifier = constraints.emotional_restraint?.expression_control || 0.5;
        return Math.min(1.0, baseOpenness * constraintModifier);
    }

    calculateTopicFreedom(capabilities, constraints) {
        return capabilities.roleplay_capable && 
               constraints.content_filters?.personality_expression_level !== 'low' ? 'high' : 'moderate';
    }

    calculatePersonalityAuthenticity(capabilities, constraints) {
        const naturalExpressions = capabilities.natural_personality_expression || [];
        const allowedLevel = constraints.content_filters?.personality_expression_level || 'moderate';
        
        if (allowedLevel === 'high' && naturalExpressions.length > 3) return 'authentic';
        if (allowedLevel === 'moderate') return 'balanced';
        return 'conservative';
    }

    async validateContentAppropriateness(content, contentFiltering) {
        // Basic content validation
        if (!content || typeof content !== 'string') return false;
        
        // Check for inappropriate content based on filtering settings
        if (!contentFiltering.nsfw_allowed && this.containsNSFWContent(content)) {
            return false;
        }
        
        if (!contentFiltering.mature_themes_allowed && this.containsMatureThemes(content)) {
            return false;
        }
        
        return true;
    }

    containsNSFWContent(content) {
        const nsfwPatterns = [
            /\b(sex|sexual|porn|nude|naked|orgasm|masturbat|fuck|shit|damn)\b/i,
            /\b(breast|dick|cock|pussy|ass|butt|genitals)\b/i
        ];
        
        return nsfwPatterns.some(pattern => pattern.test(content));
    }

    containsMatureThemes(content) {
        const maturePatterns = [
            /\b(violence|blood|kill|death|murder|suicide)\b/i,
            /\b(drug|alcohol|drunk|high|addiction)\b/i,
            /\b(hate|racist|sexist|discrimination)\b/i
        ];
        
        return maturePatterns.some(pattern => pattern.test(content));
    }

    getFallbackResponse(avatar, messageType, context) {
        const fallbackResponses = {
            greeting: [
                `Hello! ${avatar.displayName || avatar.name} here.`,
                `Hi there! It's good to see you!`,
                `Hey! How are you doing today?`,
                `Hello! How's your day going?`
            ],
            response: [
                "That's interesting! Tell me more.",
                "I see what you mean.",
                "That's a good point!",
                "I'm listening, please continue."
            ],
            question: [
                "That's a great question! Let me think about it.",
                "I'm not sure about that, but I'd love to learn more.",
                "What do you think about it?",
                "That's something worth exploring together."
            ]
        };
        
        const responses = fallbackResponses[messageType] || fallbackResponses.response;
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        return {
            message: randomResponse,
            avatar: avatar,
            timestamp: new Date().toISOString(),
            type: 'avatar',
            message_type: messageType,
            generated_by: 'fallback',
            confidence: 0.3
        };
    }

    // Cache management
    clearCache() {
        this.responseCache.clear();
        this.generationInProgress.clear();
    }
}

// Export for use in other modules
window.ResponseGenerationManager = ResponseGenerationManager;
