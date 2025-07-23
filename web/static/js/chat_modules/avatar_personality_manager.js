/**
 * Avatar Personality Manager
 * Handles personality traits, content capabilities, and behavioral analysis
 */
class AvatarPersonalityManager {
    constructor() {
        this.personalityCache = new Map();
        this.contentCapabilitiesCache = new Map();
        this.behavioralConstraintsCache = new Map();
    }

    // Personality trait management - fetches from database with fallback
    async getAvatarPersonalityTraits(avatarId) {
        if (this.personalityCache.has(avatarId)) {
            return this.personalityCache.get(avatarId);
        }

        // Try to fetch from database first
        const dbTraits = await this.fetchPersonalityTraitsFromDatabase(avatarId);
        if (dbTraits) {
            this.personalityCache.set(avatarId, dbTraits);
            return dbTraits;
        }

        // Fallback to default traits
        const defaultTraits = this.getDefaultPersonalityTraits(avatarId);
        this.personalityCache.set(avatarId, defaultTraits);
        return defaultTraits;
    }

    async fetchPersonalityTraitsFromDatabase(avatarId) {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/live2d/models/${avatarId}/personality`);
            if (response.ok) {
                const personality = await response.json();
                console.log(`🧠 Loaded personality traits for ${avatarId} from database:`, personality);
                return personality.traits || personality;
            }
        } catch (error) {
            console.warn(`Failed to load personality traits for ${avatarId} from database:`, error);
        }
        return null;
    }

    // Comprehensive default personality traits matching chat_manager structure
    getDefaultPersonalityTraits(avatarId) {
        // Complete trait set that matches the database structure
        return {
            // Big Five personality traits
            extroversion: 0.5,
            agreeableness: 0.5,
            conscientiousness: 0.5,
            neuroticism: 0.3,
            openness: 0.5,
            
            // Emotional traits
            emotional_stability: 0.7,
            intelligence: 0.6,
            empathy: 0.6,
            emotional_depth: 0.5,
            
            // Romantic/sexual traits
            seductive: 0.2,
            flirtatious: 0.2,
            passionate: 0.3,
            sensual: 0.2,
            sexually_adventurous: 0.1,
            horny: 0.1,
            
            // Behavioral traits
            mischievous: 0.3,
            dominant: 0.3,
            submissive: 0.3,
            intensity: 0.4,
            wild: 0.2,
            
            // Additional traits for character consistency
            confidence: 0.5,
            playfulness: 0.5,
            adventurous: 0.4,
            caring: 0.6,
            loyalty: 0.6
        };
    }

    // Content capabilities management
    async getAvatarContentCapabilities(avatarId) {
        if (this.contentCapabilitiesCache.has(avatarId)) {
            return this.contentCapabilitiesCache.get(avatarId);
        }

        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/live2d/models/${avatarId}/capabilities`);
            if (response.ok) {
                const capabilities = await response.json();
                this.contentCapabilitiesCache.set(avatarId, capabilities);
                return capabilities;
            }
        } catch (error) {
            console.warn(`Failed to load capabilities for ${avatarId}:`, error);
        }

        // Fallback to personality-based capabilities
        const capabilities = await this.deriveCapabilitiesFromPersonality(avatarId);
        this.contentCapabilitiesCache.set(avatarId, capabilities);
        return capabilities;
    }

    async deriveCapabilitiesFromPersonality(avatarId) {
        const personalityTraits = await this.getAvatarPersonalityTraits(avatarId);
        
        return {
            nsfw_capable: personalityTraits.seductive > 0.5 || personalityTraits.flirtatious > 0.5,
            mature_content_capable: personalityTraits.intensity > 0.6 || personalityTraits.passionate > 0.6,
            violence_capable: personalityTraits.intensity > 0.7,
            strong_language_capable: personalityTraits.intensity > 0.5,
            roleplay_capable: true,
            explicit_content_comfort: personalityTraits.seductive > 0.7 ? 'high' : 'moderate',
            natural_personality_expression: this.getAllowedPersonalityExpression(personalityTraits),
            conversation_style: this.deriveConversationStyle(personalityTraits),
            response_patterns: this.deriveResponsePatterns(personalityTraits)
        };
    }

    getAllowedPersonalityExpression(personalityTraits) {
        const expressions = [];
        
        if (personalityTraits.seductive > 0.3) expressions.push('seductive_behavior');
        if (personalityTraits.flirtatious > 0.3) expressions.push('flirtatious_behavior');
        if (personalityTraits.passionate > 0.3) expressions.push('passionate_responses');
        if (personalityTraits.mischievous > 0.3) expressions.push('playful_teasing');
        if (personalityTraits.confidence > 0.6) expressions.push('assertive_behavior');
        if (personalityTraits.playfulness > 0.5) expressions.push('humorous_responses');
        
        return expressions;
    }

    deriveConversationStyle(personalityTraits) {
        return {
            formality: personalityTraits.conscientiousness > 0.6 ? 'formal' : 'casual',
            directness: personalityTraits.confidence > 0.7 ? 'direct' : 'subtle',
            emotional_expression: personalityTraits.extroversion > 0.6 ? 'expressive' : 'reserved',
            humor_usage: personalityTraits.playfulness > 0.6 ? 'frequent' : 'occasional',
            topic_initiation: personalityTraits.extroversion > 0.7 ? 'proactive' : 'reactive'
        };
    }

    deriveResponsePatterns(personalityTraits) {
        return {
            greeting_style: personalityTraits.extroversion > 0.6 ? 'enthusiastic' : 'warm',
            question_approach: personalityTraits.openness > 0.6 ? 'curious' : 'polite',
            conversation_depth: personalityTraits.openness > 0.7 ? 'deep' : 'surface',
            emotional_responsiveness: personalityTraits.agreeableness > 0.6 ? 'empathetic' : 'neutral',
            conflict_handling: personalityTraits.agreeableness > 0.7 ? 'diplomatic' : 'assertive'
        };
    }

    // Behavioral constraints calculation
    async calculateBehavioralConstraints(avatarId, context) {
        const cacheKey = `${avatarId}_${JSON.stringify(context)}`;
        if (this.behavioralConstraintsCache.has(cacheKey)) {
            return this.behavioralConstraintsCache.get(cacheKey);
        }

        const personalityTraits = await this.getAvatarPersonalityTraits(avatarId);
        const constraints = {
            response_threshold: this.calculateResponseThreshold(personalityTraits, context),
            content_filters: this.buildContentFilters(personalityTraits),
            social_awareness: this.calculateSocialAwareness(personalityTraits, context),
            emotional_restraint: this.calculateEmotionalRestraint(personalityTraits),
            contextual_adaptation: this.calculateContextualAdaptation(personalityTraits, context)
        };

        this.behavioralConstraintsCache.set(cacheKey, constraints);
        return constraints;
    }

    calculateResponseThreshold(personalityTraits, context) {
        let threshold = 0.3; // Base threshold
        
        // Shy avatars have higher threshold
        if (personalityTraits.extroversion < 0.4) threshold += 0.2;
        
        // Context-specific adjustments
        if (context.context === 'greeting') threshold -= 0.1;
        if (context.addressing_analysis?.direct_address) threshold -= 0.1;
        
        return Math.max(0.1, Math.min(0.9, threshold));
    }

    buildContentFilters(personalityTraits) {
        return {
            allow_nsfw_content: personalityTraits.seductive > 0.6,
            allow_mature_themes: personalityTraits.intensity > 0.5,
            allow_strong_language: personalityTraits.intensity > 0.4,
            personality_expression_level: personalityTraits.confidence > 0.7 ? 'high' : 'moderate'
        };
    }

    calculateSocialAwareness(personalityTraits, context) {
        return {
            group_dynamics_awareness: personalityTraits.agreeableness * 0.8,
            user_attention_sensitivity: personalityTraits.agreeableness * 0.7,
            conversation_flow_awareness: personalityTraits.conscientiousness * 0.6,
            emotional_atmosphere_detection: personalityTraits.openness * 0.5
        };
    }

    calculateEmotionalRestraint(personalityTraits) {
        return {
            intensity_modulation: personalityTraits.conscientiousness,
            emotional_volatility: personalityTraits.neuroticism,
            expression_control: personalityTraits.conscientiousness,
            impulse_control: 1.0 - personalityTraits.neuroticism
        };
    }

    calculateContextualAdaptation(personalityTraits, context) {
        return {
            situational_flexibility: personalityTraits.openness,
            social_context_adaptation: personalityTraits.agreeableness,
            user_preference_accommodation: personalityTraits.agreeableness * 0.8,
            conversation_style_matching: personalityTraits.openness * 0.7
        };
    }

    // Clear caches when needed
    clearCache(avatarId = null) {
        if (avatarId) {
            this.personalityCache.delete(avatarId);
            this.contentCapabilitiesCache.delete(avatarId);
            // Clear behavioral constraints for this avatar
            for (const key of this.behavioralConstraintsCache.keys()) {
                if (key.startsWith(avatarId + '_')) {
                    this.behavioralConstraintsCache.delete(key);
                }
            }
        } else {
            this.personalityCache.clear();
            this.contentCapabilitiesCache.clear();
            this.behavioralConstraintsCache.clear();
        }
    }
}

// Export for use in other modules
window.AvatarPersonalityManager = AvatarPersonalityManager;
