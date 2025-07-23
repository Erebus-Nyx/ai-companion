// chat.js
// Multi-avatar chat and message handling logic for frontend

// Avatar management for chat with user context
class AvatarChatManager {
    constructor() {
        this.activeAvatars = new Map(); // Map of avatar_id -> avatar_data
        this.speakingAvatar = null; // Currently speaking avatar
        this.avatarDatabase = new Map(); // Avatar-specific information
        this.messageHistory = []; // Chat history with avatar attribution
        this.currentUser = null; // Current user information
        this.userProfile = null; // User profile data
        this.chatHistory = []; // Full chat history from database
        
        this.initializeAvatarSystem();
    }

    async initializeAvatarSystem() {
        console.log('🎭 Initializing avatar chat system...');
        
        // Load current user information
        await this.loadCurrentUser();
        
        // If no user found via API, check if there should be one from localStorage/user selection
        if (!this.currentUser) {
            await this.checkForExpectedUser();
        }
        
        // Load avatar database information
        await this.loadAvatarDatabase();
        // Load chat history (only if user is authenticated)
        await this.loadChatHistory();
        // Set up listeners for avatar changes
        this.setupAvatarListeners();
        
        console.log('🎭 Multi-avatar chat system initialized with user context:', this.currentUser?.display_name || 'No user');
    }

    async checkForExpectedUser() {
        // Check if localStorage indicates there should be a current user
        const storedUsername = localStorage.getItem('currentUser');
        const storedUserId = localStorage.getItem('currentUserId');
        
        if (storedUsername && storedUserId) {
            console.log('🔍 Found stored user info, but API returned no current user. Attempting to re-authenticate...');
            
            // Try a short delay and retry in case the backend is still setting up the session
            await new Promise(resolve => setTimeout(resolve, 500));
            await this.loadCurrentUser();
            
            if (!this.currentUser) {
                console.warn('⚠️ Stored user info exists but API still returns no current user. User may need to log in again.');
                // Clear invalid stored user info
                localStorage.removeItem('currentUser');
                localStorage.removeItem('currentUserId');
            }
        }
    }

    async loadCurrentUser() {
        try {
            console.log('🔍 Loading current user from API...');
            const response = await fetch('/api/users/current');
            console.log('📡 API response status:', response.status, response.statusText);
            
            if (response.ok) {
                this.currentUser = await response.json();
                console.log('👤 Current user loaded:', this.currentUser.display_name, 'ID:', this.currentUser.id);
                
                // Ensure user ID is a number
                if (typeof this.currentUser.id === 'string') {
                    console.log('🔄 Converting user ID from string to number');
                    this.currentUser.id = parseInt(this.currentUser.id);
                }
                
                // Load user profile
                await this.loadUserProfile();
            } else {
                console.warn('⚠️ No current user found - API returned:', response.status, 'operating in session mode');
                // Set null to indicate no authenticated user
                this.currentUser = null;
            }
        } catch (error) {
            console.warn('❌ Failed to load current user:', error);
            // Set null to indicate no authenticated user
            this.currentUser = null;
        }
    }

    async loadUserProfile() {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`/api/users/${this.currentUser.id}/profile`);
            if (response.ok) {
                this.userProfile = await response.json();
                console.log('📋 User profile loaded');
            }
        } catch (error) {
            console.warn('Failed to load user profile:', error);
        }
    }

    async loadChatHistory(limit = 50) {
        // Only load chat history if we have a valid authenticated user
        if (!this.currentUser || typeof this.currentUser.id !== 'number') {
            console.log('📚 Skipping chat history load - no authenticated user');
            return;
        }

        try {
            const response = await fetch(`/api/chat/history?user_id=${this.currentUser.id}&limit=${limit}`);
            if (response.ok) {
                const data = await response.json();
                this.chatHistory = data.history || [];
                console.log(`📚 Loaded ${this.chatHistory.length} previous chat messages for user ${this.currentUser.id}`);
                
                // Display recent history in chat window
                this.displayChatHistory();
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
        }
    }

    async loadAvatarDatabase() {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const models = await response.json();
                models.forEach(model => {
                    this.avatarDatabase.set(model.model_name, {
                        id: model.model_name,
                        name: model.model_name,
                        displayName: this.formatAvatarName(model.model_name),
                        description: model.description || '',
                        motions: model.motions || {},
                        expressions: model.expressions || {},
                        lastActive: null,
                        messageCount: 0,
                        personality: null // To be loaded separately when personality system is rebuilt
                    });
                });
                console.log(`📦 Loaded ${this.avatarDatabase.size} avatar profiles`);
            }
        } catch (error) {
            console.warn('Failed to load avatar database:', error);
        }
    }

    displayChatHistory() {
        // Display recent chat history in the chat window
        if (!this.chatHistory || this.chatHistory.length === 0) return;
        
        // Clear existing messages first
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            console.log('🧹 Cleared chat messages container for history display');
        }
        
        // Show last 10 messages to avoid overwhelming the interface
        const recentHistory = this.chatHistory.slice(-10);
        
        // Add a separator for history
        if (recentHistory.length > 0) {
            addSystemMessage(`📚 Previous conversation (${recentHistory.length} messages)`);
        }
        
        // Display each historical message with proper speaker identification
        recentHistory.forEach(msg => {
            // Add user message
            addMessage('user', msg.user_message, 'info', null, {
                timestamp: new Date(msg.timestamp).toLocaleString(),
                speaker: msg.user_display_name
            });
            
            // Add AI response with avatar info
            const avatarInfo = this.avatarDatabase.get(msg.avatar_id) || {
                displayName: msg.avatar_name,
                id: msg.avatar_id
            };
            
            addMessage('ai', msg.ai_response, 'info', avatarInfo, {
                timestamp: new Date(msg.timestamp).toLocaleString(),
                emotion: msg.primary_emotion
            });
        });
        
        // Add separator for new conversation
        if (recentHistory.length > 0) {
            addSystemMessage('--- New conversation ---', 'separator');
        }
    }

    formatAvatarName(modelName) {
        // Convert model names like 'haruka' to 'Haruka'
        return modelName.charAt(0).toUpperCase() + modelName.slice(1);
    }

    setupAvatarListeners() {
        console.log('🔧 Setting up avatar listeners...');
        
        // Listen for avatar changes from the Live2D system using events (efficient)
        if (window.live2dMultiModelManager) {
            // Listen for model loaded events instead of polling
            document.addEventListener('live2d:modelLoaded', (event) => {
                console.log('🎭 Model loaded event received:', event.detail);
                this.handleModelLoaded(event.detail);
            });
            
            // Listen for model changed events  
            document.addEventListener('live2d:modelChanged', (event) => {
                console.log('🎭 Model changed event received:', event.detail);
                this.updateActiveAvatars();
            });
            
            // Also do an initial check after a delay for already loaded models
            setTimeout(() => {
                console.log('🔍 Initial avatar check on startup');
                this.updateActiveAvatars();
            }, 2000);
        }
        
        // Listen for user changes from the user selection system
        document.addEventListener('userChanged', (event) => {
            console.log('👤 User changed event received:', event.detail.user);
            this.currentUser = event.detail.user;
            
            // Ensure user ID is numeric
            if (this.currentUser && typeof this.currentUser.id === 'string') {
                this.currentUser.id = parseInt(this.currentUser.id);
            }
            
            // Update localStorage for authentication check
            if (this.currentUser) {
                localStorage.setItem('currentUser', this.currentUser.username);
                localStorage.setItem('currentUserId', this.currentUser.id.toString());
            }
            
            // Reload user profile and chat history for the new user
            this.loadUserProfile();
            this.loadChatHistory();
            
            console.log('✅ Chat manager updated for user:', this.currentUser?.display_name, 'ID:', this.currentUser?.id);
        });
    }
    
    handleModelLoaded(modelDetail) {
        console.log('🎭 === HANDLING MODEL LOADED EVENT ===');
        console.log('Model detail received:', modelDetail);
        
        // Update active avatars to include the newly loaded model
        this.updateActiveAvatars();
        
        // Check if this is a new avatar that should send a greeting
        if (modelDetail && modelDetail.modelData && modelDetail.modelData.name) {
            const modelName = modelDetail.modelData.name;
            console.log('🎭 Processing newly loaded model:', modelName);
            
            const avatarInfo = this.avatarDatabase.get(modelName) || {
                id: modelName,
                name: modelName,
                displayName: this.formatAvatarName(modelName)
            };
            
            // Get the actual pixiModel for the greeting
            if (modelDetail.modelData.pixiModel) {
                avatarInfo.pixiModel = modelDetail.modelData.pixiModel;
                console.log('✅ PixiModel found for autonomous greeting');
            } else {
                console.warn('⚠️ No pixiModel found in model data');
            }
            
            // Trigger autonomous greeting for the newly loaded avatar
            const delay = 1000 + Math.random() * 2000; // Random delay 1-3 seconds for natural feel
            console.log(`👋 Scheduling autonomous greeting for ${avatarInfo.displayName} in ${delay.toFixed(0)}ms`);
            
            setTimeout(() => {
                console.log(`🎉 Triggering autonomous greeting for newly loaded avatar: ${avatarInfo.displayName}`);
                this.sendAutonomousGreeting(avatarInfo);
            }, delay);
        } else {
            console.warn('⚠️ Invalid model detail received:', modelDetail);
        }
        console.log('🎭 === END MODEL LOADED HANDLING ===');
    }

    // Method to manually refresh current user (useful for debugging and ensuring sync)
    async refreshCurrentUser() {
        console.log('🔄 Refreshing current user...');
        await this.loadCurrentUser();
        
        if (this.currentUser) {
            console.log('✅ Current user refreshed:', this.currentUser.display_name, 'ID:', this.currentUser.id);
            // Also reload profile and history
            await this.loadUserProfile();
            await this.loadChatHistory();
        } else {
            console.warn('⚠️ No current user found after refresh');
        }
    }

    updateActiveAvatars() {
        if (!window.live2dMultiModelManager) {
            console.log('🎭 Live2D multi model manager not available');
            return;
        }

        const currentActive = new Map();
        const allModels = window.live2dMultiModelManager.getAllModels();
        
        // Only log when there are actually models to check
        if (allModels.length > 0) {
            console.log('🔍 Checking all Live2D models:', allModels.length);
        }
        
        allModels.forEach((modelData, index) => {
            console.log(`🎭 Model ${index + 1}:`, {
                name: modelData.name,
                hasModel: !!modelData.pixiModel,
                visible: modelData.pixiModel?.visible,
                alpha: modelData.pixiModel?.alpha,
                isActive: modelData.isActive
            });
            
            // Check if model exists and is visible 
            // Note: Some Live2D models might not have alpha property or default to 1
            const isVisible = modelData.pixiModel && 
                             (modelData.pixiModel.visible === true || modelData.pixiModel.visible === undefined) &&
                             (modelData.pixiModel.alpha === undefined || modelData.pixiModel.alpha > 0);
            
            if (isVisible) {
                const avatarId = modelData.name;
                const avatarInfo = this.avatarDatabase.get(avatarId) || {
                    id: avatarId,
                    name: avatarId,
                    displayName: this.formatAvatarName(avatarId)
                };
                
                console.log('✅ Active avatar found:', avatarId);
                
                currentActive.set(avatarId, {
                    ...avatarInfo,
                    pixiModel: modelData.pixiModel,
                    isActive: true,
                    position: { x: modelData.pixiModel.x, y: modelData.pixiModel.y },
                    scale: modelData.pixiModel.scale.x
                });
            }
        });

        // Update active avatars map
        this.activeAvatars = currentActive;
        
        console.log('🎭 Updated active avatars:', this.activeAvatars.size, Array.from(this.activeAvatars.keys()));
        
        // Update UI if needed
        this.updateChatUI();
        
        // Notify autonomous system about avatar changes
        this.notifyAutonomousSystem();
    }
    
    notifyAutonomousSystem() {
        // Notify autonomous avatar system about active avatar changes
        if (typeof socket !== 'undefined' && socket.connected) {
            const activeAvatarData = Array.from(this.activeAvatars.values()).map(a => ({
                id: a.id,
                name: a.name,
                displayName: a.displayName
            }));
            
            socket.emit('active_avatars_updated', {
                avatars: activeAvatarData,
                count: activeAvatarData.length
            });
            
            // Trigger autonomous greetings for newly loaded avatars
            this.triggerAutonomousGreetings(activeAvatarData);
        }
    }
    
    triggerAutonomousGreetings(activeAvatars) {
        // Trigger greeting messages from newly loaded avatars
        if (activeAvatars.length > 0) {
            console.log('🎭 Triggering autonomous greetings for', activeAvatars.length, 'avatars');
            
            // Delay greeting messages to feel more natural
            activeAvatars.forEach((avatar, index) => {
                setTimeout(() => {
                    this.sendAutonomousGreeting(avatar);
                }, (index + 1) * 3000 + Math.random() * 2000); // Stagger greetings 3-5 seconds apart
            });
        }
    }
    
    // Enhanced sendAutonomousGreeting with synchronized personality system
    async sendAutonomousGreeting(avatar) {
        console.log('👋 === SENDING SYNCHRONIZED AUTONOMOUS GREETING ===');
        console.log('Avatar info:', avatar);
        
        // Check personality - shy avatars might not greet immediately
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        const userRelationship = this.getUserRelationshipContext(avatar.id);
        const addressingContext = this.analyzeAddressingContext(avatar, { context: 'greeting' });
        
        // Apply behavioral constraints
        const behavioralConstraints = this.calculateBehavioralConstraints(avatar.id, { 
            context: 'greeting',
            addressing_analysis: addressingContext
        });
        
        // Check if avatar should greet based on sophisticated analysis
        if (!this.shouldAvatarGreet(avatar.id, personalityTraits, userRelationship, behavioralConstraints)) {
            console.log(`🤐 ${avatar.displayName} chooses not to greet based on personality/context analysis`);
            return;
        }
        
        // Log autonomous activity
        if (window.consoleLogger) {
            window.consoleLogger.logEvent('SYNCHRONIZED_AUTONOMOUS_GREETING', {
                avatar_name: avatar.displayName || avatar.name,
                avatar_id: avatar.id,
                personality_traits: personalityTraits,
                user_relationship: userRelationship,
                timestamp: new Date().toISOString()
            });
        }
        
        try {
            // Enhanced context for roleplay and content filtering
            const roleplayContext = await this.buildRoleplayContext(avatar, {
                user_id: this.currentUser?.id,
                interaction_type: 'greeting',
                relationship_context: userRelationship
            });
            
            const contentFilters = await this.buildContentFilters(avatar.id, this.currentUser?.id);
            
            // Generate AI-based greeting using synchronized backend system
            const greetingResponse = await this.generateAutonomousMessage(avatar, 'greeting', {
                context: 'Avatar just loaded and is greeting the user',
                intent: 'welcome_user',
                emotion: this.determineGreetingEmotion(avatar.id, userRelationship),
                conversation_history: this.messageHistory.slice(-3),
                relationship_context: userRelationship,
                personality_influence: personalityTraits,
                addressing_analysis: addressingContext,
                behavioral_constraints: behavioralConstraints,
                roleplay_context: roleplayContext,
                content_filters: contentFilters,
                character_consistency: this.getCharacterConsistencyProfile(avatar.id)
            });
            
            console.log('💬 Generated synchronized greeting:', greetingResponse);
            
            if (greetingResponse) {
                // Get synchronized response details
                const syncDetails = await this.processSynchronizedResponse(avatar, 
                    { message: greetingResponse }, 
                    { 
                        context: 'greeting',
                        relationship_context: userRelationship,
                        personality_influence: personalityTraits
                    }
                );
                
                // Add greeting message with synchronized emotional parameters
                console.log('📝 Adding synchronized greeting message to chat...');
                addMessage('ai', syncDetails.message, 'autonomous', avatar, {
                    emotion: syncDetails.emotion,
                    emotion_intensity: syncDetails.emotion_intensity,
                    timestamp: new Date().toLocaleTimeString(),
                    is_autonomous: true,
                    is_greeting: true,
                    is_synchronized: true,
                    personality_influence: syncDetails.personality_influence,
                    tts_params: syncDetails.tts_params,
                    behavioral_cues: syncDetails.behavioral_cues
                });
                console.log('✅ Synchronized greeting message added to chat');
                
                // Add to message history with full emotional context
                this.messageHistory.push({
                    type: 'avatar',
                    message: syncDetails.message,
                    timestamp: new Date(),
                    avatar: avatar,
                    is_autonomous: true,
                    is_greeting: true,
                    is_synchronized: true,
                    emotions: [syncDetails.emotion],
                    primary_emotion: syncDetails.emotion,
                    emotion_intensity: syncDetails.emotion_intensity,
                    personality_influence: syncDetails.personality_influence,
                    tts_params: syncDetails.tts_params,
                    live2d_params: syncDetails.live2d_params,
                    behavioral_cues: syncDetails.behavioral_cues
                });
                console.log('✅ Synchronized greeting added to message history');
                
                // Trigger synchronized avatar motion and TTS
                await this.executeSynchronizedAvatarResponse(avatar, syncDetails);
                
                console.log(`🎉 ${avatar.displayName} sent synchronized autonomous greeting: "${syncDetails.message}"`);
            } else {
                console.warn('⚠️ Failed to generate greeting, avatar will remain silent');
            }
            
        } catch (error) {
            console.error('❌ Error sending synchronized autonomous greeting:', error);
        }
        
        console.log('👋 === END SYNCHRONIZED AUTONOMOUS GREETING ===');
        
        // Schedule follow-up autonomous behavior after greeting
        this.scheduleAutonomousInteractions(avatar);
    }

    shouldAvatarGreet(avatarId, personalityTraits, userRelationship, behavioralConstraints) {
        // Sophisticated decision making for greeting behavior including mature personality expression
        
        // Allow naturally flirtatious/seductive characters to express themselves when content is permitted
        const contentFilters = behavioralConstraints.content_filters || {};
        const naturalExpressions = personalityTraits.natural_personality_expression || [];
        
        // Characters with high horniness/seductive traits may greet differently when allowed
        if (personalityTraits.horny > 0.5 && contentFilters.allow_nsfw_content) {
            console.log(`🔥 ${avatarId} has high horniness (${personalityTraits.horny}) and NSFW is permitted - allowing natural expression`);
            // Don't block greeting, but allow natural personality to come through
        }
        
        if (personalityTraits.seductive > 0.5 && contentFilters.allow_mature_themes) {
            console.log(`💋 ${avatarId} has seductive traits (${personalityTraits.seductive}) and mature content is permitted`);
            // Allow seductive characters to be naturally seductive
        }
        
        // Shy or introverted avatars may delay or skip greeting
        if (personalityTraits.extroversion < 0.3 && Math.random() < 0.4) {
            // Schedule a delayed, subtle greeting instead
            setTimeout(() => this.sendDelayedSubtleGreeting({ id: avatarId }), 
                30000 + Math.random() * 60000);
            return false;
        }
        
        // Check for recent negative interactions
        if (userRelationship.last_interaction_tone === 'angry' && 
            userRelationship.unresolved_issues?.length > 0) {
            // Send cautious greeting instead
            setTimeout(() => this.sendCautiousGreeting({ id: avatarId }, userRelationship), 
                5000 + Math.random() * 10000);
            return false;
        }
        
        // Check behavioral constraints
        if (behavioralConstraints.response_threshold > 0.7) {
            return false; // Too hesitant to greet
        }
        
        // High neuroticism might cause hesitation
        if (personalityTraits.neuroticism > 0.7 && Math.random() < 0.3) {
            return false;
        }
        
        // Naturally horny characters might be more eager to greet (when content permits)
        if (personalityTraits.horny > 0.6 && contentFilters.allow_nsfw_content) {
            console.log(`😈 ${avatarId} is naturally horny and eager to interact`);
            return true; // Always greet when sexually motivated and content permits
        }
        
        return true; // Avatar should greet
    }

    async executeSynchronizedAvatarResponse(avatar, syncDetails) {
        console.log('🎭 Executing synchronized avatar response...');
        
        // Trigger Live2D motion with synchronized parameters
        if (avatar.pixiModel && typeof triggerAvatarMotion === 'function') {
            console.log('🎭 Triggering synchronized Live2D motion...');
            
            // Enhanced motion triggering with personality and emotional sync
            await this.triggerSynchronizedLive2DMotion(avatar.pixiModel, syncDetails.live2d_params);
        } else {
            console.warn('⚠️ Cannot trigger synchronized avatar motion:', {
                hasPixiModel: !!avatar.pixiModel,
                hasTriggerFunction: typeof triggerAvatarMotion === 'function'
            });
        }
        
        // Trigger TTS with synchronized emotional parameters
        if (typeof triggerEmotionalTTS === 'function') {
            console.log('🔊 Triggering synchronized emotional TTS...');
            await this.triggerSynchronizedTTS(syncDetails.message, syncDetails.tts_params);
        } else {
            console.warn('⚠️ Emotional TTS function not available');
        }
        
        // Apply behavioral cues
        if (syncDetails.behavioral_cues?.length > 0) {
            console.log('� Applying behavioral cues:', syncDetails.behavioral_cues);
            await this.applyBehavioralCues(avatar, syncDetails.behavioral_cues);
        }
        
        console.log('✅ Synchronized avatar response execution complete');
    }

    async triggerSynchronizedLive2DMotion(pixiModel, live2dParams) {
        // Enhanced Live2D motion triggering with personality synchronization
        try {
            if (live2dParams.motion) {
                // Trigger motion with personality-adjusted parameters
                if (typeof triggerAvatarMotion === 'function') {
                    await triggerAvatarMotion(pixiModel, live2dParams.emotion, {
                        motion: live2dParams.motion,
                        intensity: live2dParams.intensity,
                        duration: live2dParams.duration,
                        personality_influence: live2dParams.personality_influence,
                        sync_with_speech: live2dParams.sync_with_speech
                    });
                }
            }
            
            if (live2dParams.expression) {
                // Trigger expression change if supported
                if (typeof triggerAvatarExpression === 'function') {
                    await triggerAvatarExpression(pixiModel, live2dParams.expression, {
                        intensity: live2dParams.intensity
                    });
                }
            }
        } catch (error) {
            console.error('❌ Error triggering synchronized Live2D motion:', error);
        }
    }

    async triggerSynchronizedTTS(message, ttsParams) {
        // Enhanced TTS triggering with emotional and personality synchronization
        try {
            if (typeof triggerEmotionalTTS === 'function') {
                // Get the avatar info for proper TTS integration
                const avatarId = ttsParams.avatar_id || this.currentSpeaker || 'default';
                const personalityTraits = ttsParams.personality_traits || {};
                
                // Call the new triggerEmotionalTTS function with correct signature
                await triggerEmotionalTTS(
                    message,                    // text
                    ttsParams.emotion,          // emotion
                    avatarId,                   // avatarId
                    personalityTraits,          // personalityTraits
                    ttsParams.intensity || 0.5  // intensity
                );
                
                console.log(`🎵 Synchronized TTS triggered for ${avatarId} with emotion: ${ttsParams.emotion}`);
                
            } else if (typeof speak === 'function') {
                // Fallback to basic TTS with adjusted parameters
                speak(message, {
                    rate: ttsParams.speed,
                    pitch: ttsParams.pitch,
                    volume: ttsParams.volume
                });
            } else {
                console.warn('⚠️ No TTS function available');
            }
        } catch (error) {
            console.error('❌ Error triggering synchronized TTS:', error);
        }
    }

    async applyBehavioralCues(avatar, behavioralCues) {
        // Apply visual and behavioral cues to enhance avatar expression
        try {
            behavioralCues.forEach(cue => {
                switch (cue) {
                    case 'smile':
                        this.applyCue(avatar, 'facial_expression', 'smile');
                        break;
                    case 'direct_eye_contact':
                        this.applyCue(avatar, 'gaze_direction', 'user');
                        break;
                    case 'averted_gaze':
                        this.applyCue(avatar, 'gaze_direction', 'away');
                        break;
                    case 'animated_gestures':
                        this.applyCue(avatar, 'gesture_intensity', 'high');
                        break;
                    case 'minimal_gestures':
                        this.applyCue(avatar, 'gesture_intensity', 'low');
                        break;
                    // Add more behavioral cues as needed
                }
            });
        } catch (error) {
            console.error('❌ Error applying behavioral cues:', error);
        }
    }

    applyCue(avatar, cueType, cueValue) {
        // Apply specific behavioral cue to avatar
        // This would integrate with the Live2D system for visual cues
        console.log(`🎨 Applying ${cueType}: ${cueValue} to ${avatar.displayName}`);
        
        // Integration point for Live2D behavioral system
        if (typeof applyAvatarBehavioralCue === 'function') {
            applyAvatarBehavioralCue(avatar.pixiModel, cueType, cueValue);
        }
    }

    // Final Essential Helper Methods for Complete System
    inferUserMood() {
        // Analyze recent user messages to infer mood
        const recentUserMessages = this.messageHistory
            .filter(msg => msg.type === 'user')
            .slice(-3);
        
        if (recentUserMessages.length === 0) return 'neutral';
        
        const messageTones = recentUserMessages.map(msg => this.analyzeMessageTone(msg.message));
        const dominantTone = this.findDominantEmotion(messageTones);
        
        return dominantTone;
    }

    analyzeUserConversationPattern() {
        // Analyze user's conversation patterns
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

    detectUserAttentionFocus() {
        // Detect what the user is paying attention to
        const recentMessages = this.messageHistory.slice(-5);
        const mentionedAvatars = new Set();
        const mentionedTopics = new Set();
        
        recentMessages.forEach(msg => {
            if (msg.type === 'user') {
                // Check for avatar mentions
                this.getActiveAvatars().forEach(avatar => {
                    if (this.isAvatarNameMentioned(avatar, msg.message)) {
                        mentionedAvatars.add(avatar.id);
                    }
                });
                
                // Extract topics
                const topics = this.extractTopicKeywords(msg.message);
                topics.forEach(topic => mentionedTopics.add(topic));
            }
        });
        
        return {
            focused_avatars: Array.from(mentionedAvatars),
            focused_topics: Array.from(mentionedTopics),
            attention_distribution: this.calculateAttentionDistribution(mentionedAvatars),
            conversation_focus: mentionedTopics.size > 0 ? 'topic_focused' : 'social_focused'
        };
    }

    calculateAttentionDistribution(mentionedAvatars) {
        const totalAvatars = this.getActiveAvatars().length;
        const mentionedCount = mentionedAvatars.size;
        
        if (totalAvatars === 0) return 'none';
        if (mentionedCount === 0) return 'unfocused';
        if (mentionedCount === 1) return 'single_focus';
        if (mentionedCount === totalAvatars) return 'equal_attention';
        return 'partial_focus';
    }

    analyzeUserInteractionStyle() {
        // Analyze how user typically interacts
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user').slice(-10);
        
        if (userMessages.length < 3) return 'unknown';
        
        let directQuestions = 0;
        let statements = 0;
        let commands = 0;
        let casual = 0;
        
        userMessages.forEach(msg => {
            const message = msg.message.toLowerCase();
            
            if (message.includes('?')) directQuestions++;
            else if (message.includes('tell me') || message.includes('show me')) commands++;
            else if (message.length < 30 && !message.includes('.')) casual++;
            else statements++;
        });
        
        const total = userMessages.length;
        if (directQuestions / total > 0.5) return 'questioning';
        if (commands / total > 0.3) return 'directive';
        if (casual / total > 0.5) return 'casual';
        return 'conversational';
    }

    getEnvironmentalFactors() {
        // Analyze environmental context
        const timeOfDay = new Date().getHours();
        const activeAvatarCount = this.getActiveAvatars().length;
        const conversationLength = this.messageHistory.length;
        
        return {
            time_context: this.getTimeContext(timeOfDay),
            social_context: this.getSocialContext(),
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

    getRelevantConversationHistory(avatarId, context) {
        // Get conversation history relevant to this avatar and context
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
        
        return relevantHistory.slice(-7); // Keep last 7 relevant messages
    }

    getRecentInteractionsSummary(speakerId, listenerId) {
        // Get summary of recent interactions between two avatars
        const interactions = this.getAvatarConversationHistory(speakerId, listenerId, 5);
        
        if (interactions.length === 0) {
            return {
                interaction_count: 0,
                last_interaction_tone: 'neutral',
                interaction_frequency: 'never',
                relationship_trend: 'unknown'
            };
        }
        
        const lastInteraction = interactions[interactions.length - 1];
        const positiveInteractions = interactions.filter(msg => 
            ['happy', 'friendly', 'caring', 'excited'].includes(msg.primary_emotion)
        ).length;
        
        const relationshipTrend = positiveInteractions / interactions.length > 0.6 ? 'improving' : 
                                positiveInteractions / interactions.length < 0.3 ? 'deteriorating' : 'stable';
        
        return {
            interaction_count: interactions.length,
            last_interaction_tone: lastInteraction.primary_emotion || 'neutral',
            interaction_frequency: this.calculateInteractionFrequency(interactions),
            relationship_trend: relationshipTrend,
            recent_topics: this.extractRecentTopics(interactions)
        };
    }

    calculateInteractionFrequency(interactions) {
        if (interactions.length === 0) return 'never';
        if (interactions.length === 1) return 'rare';
        
        const timeSpan = new Date(interactions[interactions.length - 1].timestamp) - 
                        new Date(interactions[0].timestamp);
        const hoursSpan = timeSpan / (1000 * 60 * 60);
        
        if (hoursSpan < 1) return 'frequent';
        if (hoursSpan < 24) return 'regular';
        return 'occasional';
    }

    extractRecentTopics(interactions) {
        const topics = new Set();
        interactions.forEach(msg => {
            const messageTopics = this.extractTopicKeywords(msg.message);
            messageTopics.forEach(topic => topics.add(topic));
        });
        return Array.from(topics);
    }

    // Enhanced roleplay context building
    async buildRoleplayContext(avatar, options = {}) {
        console.log(`🎭 Building roleplay context for ${avatar.displayName}...`);
        
        const characterProfile = await this.getCharacterRoleplayProfile(avatar.id);
        const userPreferences = await this.getUserRoleplayPreferences(options.user_id);
        const situationalContext = this.analyzeSituationalRoleplayContext(options);
        
        return {
            character_profile: characterProfile,
            roleplay_mode: this.determineRoleplayMode(characterProfile, userPreferences, situationalContext),
            character_consistency_level: this.calculateCharacterConsistencyLevel(avatar.id),
            immersion_depth: this.calculateImmersionDepth(userPreferences, situationalContext),
            narrative_style: this.determineNarrativeStyle(characterProfile, options.interaction_type),
            character_boundaries: this.establishCharacterBoundaries(characterProfile, userPreferences),
            situational_context: situationalContext,
            roleplay_constraints: this.buildRoleplayConstraints(characterProfile, userPreferences)
        };
    }

    async buildContentFilters(avatarId, userId) {
        console.log(`🛡️ Building content filters for avatar ${avatarId}...`);
        
        const userProfile = await this.getUserContentPreferences(userId);
        const avatarCapabilities = await this.getAvatarContentCapabilities(avatarId);
        const contextualFactors = this.getContextualContentFactors();
        
        return {
            nsfw_allowed: userProfile?.allow_nsfw_content || false,
            mature_themes_allowed: userProfile?.allow_mature_themes || false,
            strong_language_allowed: userProfile?.allow_strong_language || false,
            violence_allowed: userProfile?.allow_violence || false,
            explicit_content_level: this.determineExplicitContentLevel(userProfile, avatarCapabilities),
            content_warnings_enabled: userProfile?.content_warnings_enabled || true,
            safe_mode: userProfile?.safe_mode || false,
            avatar_content_capabilities: avatarCapabilities,
            contextual_restrictions: this.buildContextualContentRestrictions(contextualFactors),
            escalation_thresholds: this.buildContentEscalationThresholds(userProfile, avatarCapabilities)
        };
    }

    getCharacterConsistencyProfile(avatarId) {
        const basePersonality = this.getAvatarPersonalityTraits(avatarId);
        const characterArchetype = this.getCharacterArchetype(avatarId);
        const behavioralPatterns = this.getCharacterBehavioralPatterns(avatarId);
        
        return {
            core_traits: basePersonality,
            character_archetype: characterArchetype,
            speech_patterns: this.getCharacterSpeechPatterns(avatarId),
            behavioral_patterns: behavioralPatterns,
            moral_compass: this.getCharacterMoralCompass(avatarId),
            emotional_tendencies: this.getCharacterEmotionalTendencies(avatarId),
            relationship_dynamics: this.getCharacterRelationshipDynamics(avatarId),
            consistency_strictness: this.getCharacterConsistencyStrictness(avatarId),
            character_development_allowance: this.getCharacterDevelopmentAllowance(avatarId)
        };
    }

    async getCharacterRoleplayProfile(avatarId) {
        // Get comprehensive roleplay profile for character
        const characterData = this.avatarDatabase.get(avatarId) || {};
        
        return {
            character_name: characterData.displayName || avatarId,
            character_background: characterData.background || this.generateDefaultBackground(avatarId),
            roleplay_competency: characterData.roleplay_competency || 'moderate',
            immersion_preference: characterData.immersion_preference || 'medium',
            narrative_involvement: characterData.narrative_involvement || 'reactive',
            character_agency: characterData.character_agency || 'moderate',
            roleplay_boundaries: characterData.roleplay_boundaries || this.getDefaultRoleplayBoundaries(),
            content_comfort_levels: characterData.content_comfort_levels || this.getDefaultContentComfortLevels(),
            character_consistency_importance: characterData.consistency_importance || 'high',
            improvisation_tolerance: characterData.improvisation_tolerance || 'medium'
        };
    }

    async getUserRoleplayPreferences(userId) {
        if (!userId) {
            return this.getDefaultRoleplayPreferences();
        }
        
        try {
            // In a real implementation, this would fetch from user profile API
            const userProfile = this.userProfile || {};
            
            return {
                roleplay_engagement_level: userProfile.roleplay_engagement_level || 'moderate',
                preferred_narrative_style: userProfile.preferred_narrative_style || 'conversational',
                immersion_preference: userProfile.immersion_preference || 'medium',
                character_consistency_expectation: userProfile.character_consistency_expectation || 'high',
                content_comfort_zones: userProfile.content_comfort_zones || this.getDefaultContentComfortZones(),
                roleplay_experience_level: userProfile.roleplay_experience_level || 'intermediate'
            };
        } catch (error) {
            console.warn('Failed to load user roleplay preferences:', error);
            return this.getDefaultRoleplayPreferences();
        }
    }

    async getUserContentPreferences(userId) {
        if (!userId) {
            return this.getDefaultContentPreferences();
        }
        
        try {
            // Fetch user content preferences from API
            const response = await fetch(`/api/users/${userId}/content-preferences`);
            if (response.ok) {
                const preferences = await response.json();
                console.log('📋 Loaded user content preferences:', preferences);
                return preferences;
            } else {
                console.warn('⚠️ Failed to load content preferences, using defaults');
                return this.getDefaultContentPreferences();
            }
        } catch (error) {
            console.warn('Failed to load user content preferences:', error);
            return this.getDefaultContentPreferences();
        }
    }

    async getAvatarContentCapabilities(avatarId) {
        // Get avatar content capabilities from database/character profile
        try {
            const response = await fetch(`/api/live2d/models/${avatarId}/capabilities`);
            if (response.ok) {
                const capabilities = await response.json();
                console.log(`🎭 Loaded content capabilities for ${avatarId}:`, capabilities);
                return capabilities;
            }
        } catch (error) {
            console.warn(`Failed to load capabilities for ${avatarId}:`, error);
        }
        
        // Fallback: determine capabilities from avatar database
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        // Check character profile for mature characteristics
        const hasSeductiveTraits = personalityTraits.seductive > 0.5 || 
                                 personalityTraits.flirtatious > 0.5 ||
                                 personalityTraits.sexually_adventurous > 0.5;
        
        const hasPassionateTraits = personalityTraits.passionate > 0.5 ||
                                  personalityTraits.sensual > 0.5;
        
        const hasIntenseTraits = personalityTraits.mischievous > 0.7 ||
                               personalityTraits.adventurous > 0.7;
        
        return {
            nsfw_capable: avatarData.nsfw_capable || hasSeductiveTraits || hasPassionateTraits,
            mature_content_capable: avatarData.mature_content_capable || hasIntenseTraits || hasSeductiveTraits,
            violence_capable: avatarData.violence_capable || personalityTraits.aggressive > 0.5,
            strong_language_capable: avatarData.strong_language_capable !== false, // Default true
            roleplay_capable: avatarData.roleplay_capable !== false, // Default true
            explicit_content_comfort: this.determineExplicitComfortLevel(personalityTraits, avatarData),
            content_adaptation_ability: avatarData.content_adaptation_ability || 'moderate',
            character_depth_for_mature_content: this.determineCharacterDepthForMatureContent(personalityTraits),
            natural_personality_expression: this.getAllowedPersonalityExpression(personalityTraits, avatarData)
        };
    }

    determineExplicitComfortLevel(personalityTraits, avatarData) {
        // Determine comfort level based on character personality
        if (personalityTraits.seductive > 0.7 && personalityTraits.sexually_adventurous > 0.7) {
            return 'high'; // Characters like Iori who are naturally seductive
        } else if (personalityTraits.flirtatious > 0.5 || personalityTraits.passionate > 0.5) {
            return 'medium'; // Characters with romantic tendencies
        } else if (personalityTraits.shy > 0.7 || personalityTraits.conservative > 0.7) {
            return 'none'; // Very shy or conservative characters
        }
        
        return avatarData.explicit_content_comfort || 'low';
    }

    determineCharacterDepthForMatureContent(personalityTraits) {
        // Characters with complex emotional profiles can handle mature themes better
        const emotionalComplexity = (personalityTraits.emotional_depth || 0) + 
                                   (personalityTraits.empathy || 0) +
                                   (personalityTraits.intelligence || 0);
        
        if (emotionalComplexity > 2.1) return 'sophisticated';
        if (emotionalComplexity > 1.5) return 'moderate';
        return 'basic';
    }

    getAllowedPersonalityExpression(personalityTraits, avatarData) {
        // Define what personality traits this character can naturally express
        const allowedExpressions = [];
        
        // Sexual/romantic expressions
        if (personalityTraits.seductive > 0.3) allowedExpressions.push('seductive_behavior');
        if (personalityTraits.flirtatious > 0.3) allowedExpressions.push('flirtatious_behavior');
        if (personalityTraits.passionate > 0.3) allowedExpressions.push('passionate_responses');
        if (personalityTraits.sexually_adventurous > 0.3) allowedExpressions.push('sexual_topics');
        if (personalityTraits.sensual > 0.3) allowedExpressions.push('sensual_language');
        
        // Emotional expressions
        if (personalityTraits.mischievous > 0.3) allowedExpressions.push('playful_teasing');
        if (personalityTraits.dominant > 0.3) allowedExpressions.push('assertive_behavior');
        if (personalityTraits.submissive > 0.3) allowedExpressions.push('submissive_behavior');
        
        // Intensity expressions
        if (personalityTraits.intensity > 0.5) allowedExpressions.push('intense_emotions');
        if (personalityTraits.wild > 0.5) allowedExpressions.push('uninhibited_behavior');
        
        return allowedExpressions;
    }

    determineRoleplayMode(characterProfile, userPreferences, situationalContext) {
        // Determine appropriate roleplay engagement mode
        const characterEngagement = characterProfile.roleplay_competency;
        const userEngagement = userPreferences.roleplay_engagement_level;
        const contextualNeed = situationalContext.roleplay_intensity_required;
        
        if (characterEngagement === 'high' && userEngagement === 'high' && contextualNeed === 'high') {
            return 'deep_immersion';
        } else if (characterEngagement === 'low' || userEngagement === 'low') {
            return 'casual_character';
        } else if (contextualNeed === 'high') {
            return 'narrative_focused';
        }
        
        return 'balanced_roleplay';
    }

    determineExplicitContentLevel(userProfile, avatarCapabilities) {
        if (!userProfile?.allow_nsfw_content || !avatarCapabilities?.nsfw_capable) {
            return 'none';
        }
        
        if (userProfile.safe_mode) {
            return 'none';
        }
        
        if (userProfile.allow_mature_themes && avatarCapabilities.mature_content_capable) {
            if (userProfile.explicit_comfort_level === 'high' && 
                avatarCapabilities.explicit_content_comfort === 'high') {
                return 'explicit';
            } else if (userProfile.explicit_comfort_level === 'medium') {
                return 'suggestive';
            }
        }
        
        return 'mild';
    }

    buildRoleplayConstraints(characterProfile, userPreferences) {
        return {
            character_consistency_required: userPreferences.character_consistency_expectation === 'high',
            immersion_boundaries: this.defineImmersionBoundaries(characterProfile, userPreferences),
            narrative_scope_limits: this.defineNarrativeScopeLimits(userPreferences),
            content_escalation_rules: this.defineContentEscalationRules(characterProfile, userPreferences),
            character_agency_limits: this.defineCharacterAgencyLimits(characterProfile),
            improvisation_guidelines: this.defineImprovisationGuidelines(characterProfile, userPreferences)
        };
    }

    // Final synchronization method for complete system integration
    async synchronizeAllSystems(avatar, emotionalResponse, personalityFilter) {
        console.log(`🔄 Synchronizing all systems for ${avatar.displayName}...`);
        
        try {
            // Ensure all systems use the same emotional and personality parameters
            const syncParams = {
                avatar_id: avatar.id,
                primary_emotion: emotionalResponse.primary_emotion,
                emotion_intensity: emotionalResponse.intensity,
                personality_traits: this.getAvatarPersonalityTraits(avatar.id),
                tts_params: personalityFilter.tts_params,
                live2d_params: personalityFilter.live2d_params,
                behavioral_cues: personalityFilter.behavioral_cues
            };
            
            // Update all system states simultaneously
            await Promise.all([
                this.updateEmotionalSystem(syncParams),
                this.updateTTSSystem(syncParams),
                this.updateLive2DSystem(syncParams),
                this.updatePersonalitySystem(syncParams)
            ]);
            
            console.log('✅ All systems synchronized successfully');
            
        } catch (error) {
            console.error('❌ Error synchronizing systems:', error);
        }
    }

    async updateEmotionalSystem(syncParams) {
        // Update emotional state system
        this.updateAvatarEmotionalState(
            syncParams.avatar_id, 
            syncParams.primary_emotion, 
            'system_sync'
        );
    }

    async updateTTSSystem(syncParams) {
        // Prepare TTS system with emotional parameters
        if (typeof prepareTTSWithEmotion === 'function') {
            await prepareTTSWithEmotion(syncParams.tts_params);
        }
    }

    async updateLive2DSystem(syncParams) {
        // Prepare Live2D system with emotional parameters
        if (typeof prepareLive2DWithEmotion === 'function') {
            await prepareLive2DWithEmotion(syncParams.live2d_params);
        }
    }

    // Content filtering and roleplay helper methods
    getDefaultRoleplayPreferences() {
        return {
            roleplay_engagement_level: 'moderate',
            preferred_narrative_style: 'conversational',
            immersion_preference: 'medium',
            character_consistency_expectation: 'high',
            content_comfort_zones: this.getDefaultContentComfortZones(),
            roleplay_experience_level: 'intermediate'
        };
    }

    getDefaultContentPreferences() {
        return {
            allow_nsfw_content: false,
            allow_mature_themes: false,
            allow_strong_language: false,
            allow_violence: false,
            content_warnings_enabled: true,
            safe_mode: true,
            explicit_comfort_level: 'none'
        };
    }

    getDefaultContentComfortZones() {
        return {
            romance: 'mild',
            violence: 'none',
            mature_themes: 'none',
            strong_language: 'mild',
            suggestive_content: 'none'
        };
    }

    getDefaultRoleplayBoundaries() {
        return {
            character_consistency: 'high',
            narrative_involvement: 'moderate',
            content_limits: 'safe',
            improvisation_allowed: true
        };
    }

    getDefaultContentComfortLevels() {
        return {
            nsfw: 'none',
            mature_themes: 'none',
            violence: 'none',
            strong_language: 'mild',
            suggestive: 'none'
        };
    }

    analyzeSituationalRoleplayContext(options) {
        const timeOfDay = new Date().getHours();
        const interactionType = options.interaction_type || 'casual';
        const relationshipContext = options.relationship_context || {};
        
        return {
            time_context: this.getTimeContext(timeOfDay),
            interaction_type: interactionType,
            relationship_intimacy_level: relationshipContext.intimacy_level || 'casual',
            conversation_privacy_level: this.determinePrivacyLevel(),
            roleplay_intensity_required: this.calculateRoleplayIntensityRequired(interactionType),
            narrative_opportunity: this.assessNarrativeOpportunity(options),
            character_development_potential: this.assessCharacterDevelopmentPotential(options)
        };
    }

    determinePrivacyLevel() {
        const activeAvatars = this.getActiveAvatars();
        if (activeAvatars.length <= 1) return 'private';
        if (activeAvatars.length <= 3) return 'semi_private';
        return 'public';
    }

    calculateRoleplayIntensityRequired(interactionType) {
        switch (interactionType) {
            case 'greeting': return 'low';
            case 'conversation': return 'medium';
            case 'story_interaction': return 'high';
            case 'character_development': return 'very_high';
            default: return 'low';
        }
    }

    assessNarrativeOpportunity(options) {
        // Assess potential for narrative development
        const conversationLength = this.messageHistory.length;
        const relationshipDepth = options.relationship_context?.relationship_depth || 0;
        
        if (conversationLength > 20 && relationshipDepth > 0.5) return 'high';
        if (conversationLength > 10) return 'medium';
        return 'low';
    }

    assessCharacterDevelopmentPotential(options) {
        const interactionHistory = this.getRelevantConversationHistory(options.avatar?.id, options);
        const relationshipProgression = options.relationship_context?.progression_rate || 0;
        
        if (interactionHistory.length > 15 && relationshipProgression > 0.3) return 'high';
        if (interactionHistory.length > 5) return 'medium';
        return 'low';
    }

    getCharacterArchetype(avatarId) {
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        return avatarData.character_archetype || this.inferCharacterArchetype(avatarId);
    }

    inferCharacterArchetype(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        if (personalityTraits.extroversion > 0.7 && personalityTraits.agreeableness > 0.7) {
            return 'friendly_outgoing';
        } else if (personalityTraits.extroversion < 0.3 && personalityTraits.conscientiousness > 0.7) {
            return 'quiet_thoughtful';
        } else if (personalityTraits.neuroticism > 0.7) {
            return 'sensitive_emotional';
        } else if (personalityTraits.openness > 0.7) {
            return 'curious_creative';
        }
        
        return 'balanced_personality';
    }

    getCharacterSpeechPatterns(avatarId) {
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            formality_level: personalityTraits.conscientiousness > 0.6 ? 'formal' : 'casual',
            verbosity: personalityTraits.extroversion > 0.6 ? 'verbose' : 'concise',
            emotional_expressiveness: personalityTraits.neuroticism > 0.5 ? 'high' : 'moderate',
            humor_usage: personalityTraits.openness > 0.6 ? 'frequent' : 'occasional',
            directness: personalityTraits.agreeableness < 0.4 ? 'very_direct' : 'diplomatic',
            vocabulary_complexity: personalityTraits.openness > 0.7 ? 'complex' : 'simple',
            slang_usage: personalityTraits.extroversion > 0.7 ? 'frequent' : 'rare'
        };
    }

    getCharacterBehavioralPatterns(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            response_speed: personalityTraits.extroversion > 0.6 ? 'quick' : 'thoughtful',
            topic_initiation: personalityTraits.extroversion > 0.7 ? 'frequent' : 'rare',
            conflict_approach: personalityTraits.agreeableness > 0.6 ? 'avoidant' : 'confrontational',
            emotional_regulation: personalityTraits.neuroticism < 0.4 ? 'stable' : 'volatile',
            social_boundaries: personalityTraits.conscientiousness > 0.6 ? 'respectful' : 'flexible',
            intimacy_comfort: personalityTraits.openness > 0.6 ? 'comfortable' : 'cautious'
        };
    }

    getCharacterMoralCompass(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            ethical_strictness: personalityTraits.conscientiousness > 0.7 ? 'strict' : 'flexible',
            empathy_level: personalityTraits.agreeableness > 0.6 ? 'high' : 'moderate',
            justice_orientation: personalityTraits.conscientiousness > 0.6 ? 'rule_based' : 'situational',
            moral_courage: personalityTraits.extroversion > 0.6 ? 'high' : 'moderate',
            forgiveness_tendency: personalityTraits.agreeableness > 0.7 ? 'forgiving' : 'grudge_holding'
        };
    }

    getCharacterEmotionalTendencies(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            emotional_volatility: personalityTraits.neuroticism > 0.6 ? 'high' : 'low',
            emotional_expressiveness: personalityTraits.extroversion > 0.6 ? 'expressive' : 'reserved',
            emotional_depth: personalityTraits.openness > 0.6 ? 'deep' : 'surface',
            emotional_contagion: personalityTraits.agreeableness > 0.6 ? 'high' : 'low',
            emotional_recovery: personalityTraits.conscientiousness > 0.6 ? 'quick' : 'slow'
        };
    }

    getCharacterRelationshipDynamics(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            attachment_style: this.determineAttachmentStyle(personalityTraits),
            relationship_pace: personalityTraits.extroversion > 0.6 ? 'fast' : 'slow',
            intimacy_comfort: personalityTraits.openness > 0.6 ? 'comfortable' : 'cautious',
            jealousy_tendency: personalityTraits.neuroticism > 0.6 ? 'high' : 'low',
            loyalty_level: personalityTraits.conscientiousness > 0.6 ? 'high' : 'moderate',
            boundary_respect: personalityTraits.agreeableness > 0.6 ? 'high' : 'moderate'
        };
    }

    determineAttachmentStyle(personalityTraits) {
        if (personalityTraits.neuroticism > 0.7 && personalityTraits.agreeableness < 0.4) {
            return 'anxious_avoidant';
        } else if (personalityTraits.neuroticism > 0.6) {
            return 'anxious_attached';
        } else if (personalityTraits.agreeableness < 0.3) {
            return 'dismissive_avoidant';
        }
        return 'secure';
    }

    getCharacterConsistencyStrictness(avatarId) {
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        return avatarData.consistency_strictness || 'high';
    }

    getCharacterDevelopmentAllowance(avatarId) {
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        return avatarData.development_allowance || 'moderate';
    }

    generateDefaultBackground(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const archetype = this.getCharacterArchetype(avatarId);
        
        // Generate a basic background based on personality and archetype
        return {
            origin: 'AI personality system generated',
            personality_based: true,
            archetype: archetype,
            core_traits: personalityTraits,
            background_depth: 'basic'
        };
    }

    defineImmersionBoundaries(characterProfile, userPreferences) {
        return {
            maximum_roleplay_depth: Math.min(
                this.convertToNumber(characterProfile.immersion_preference),
                this.convertToNumber(userPreferences.immersion_preference)
            ),
            character_consistency_flexibility: characterProfile.character_consistency_importance === 'high' ? 'strict' : 'flexible',
            narrative_scope: userPreferences.preferred_narrative_style,
            content_boundaries: this.combineContentBoundaries(characterProfile, userPreferences)
        };
    }

    defineNarrativeScopeLimits(userPreferences) {
        return {
            story_complexity: userPreferences.roleplay_experience_level === 'advanced' ? 'complex' : 'simple',
            character_agency: userPreferences.roleplay_engagement_level === 'high' ? 'high' : 'moderate',
            narrative_control: userPreferences.preferred_narrative_style === 'collaborative' ? 'shared' : 'user_led'
        };
    }

    defineContentEscalationRules(characterProfile, userPreferences) {
        return {
            escalation_permission_required: true,
            content_warning_threshold: this.determineContentWarningThreshold(userPreferences),
            automatic_de_escalation: userPreferences.safe_mode || false,
            content_adaptation_rules: this.buildContentAdaptationRules(characterProfile, userPreferences)
        };
    }

    defineCharacterAgencyLimits(characterProfile) {
        return {
            initiative_taking: characterProfile.narrative_involvement === 'proactive' ? 'high' : 'moderate',
            story_direction_influence: characterProfile.character_agency || 'moderate',
            character_development_autonomy: characterProfile.improvisation_tolerance || 'medium'
        };
    }

    defineImprovisationGuidelines(characterProfile, userPreferences) {
        return {
            improvisation_allowed: characterProfile.improvisation_tolerance !== 'none',
            consistency_priority: characterProfile.character_consistency_importance === 'high',
            user_preference_weight: userPreferences.character_consistency_expectation === 'high' ? 0.8 : 0.5,
            creative_freedom_level: this.calculateCreativeFreedomLevel(characterProfile, userPreferences)
        };
    }

    convertToNumber(preference) {
        switch (preference) {
            case 'low': return 0.3;
            case 'medium': return 0.6;
            case 'high': return 0.9;
            default: return 0.5;
        }
    }

    combineContentBoundaries(characterProfile, userPreferences) {
        const characterBoundaries = characterProfile.content_comfort_levels || {};
        const userBoundaries = userPreferences.content_comfort_zones || {};
        
        // Take the more restrictive of the two
        return {
            nsfw: Math.min(
                this.convertToNumber(characterBoundaries.nsfw || 'none'),
                this.convertToNumber(userBoundaries.nsfw || 'none')
            ),
            violence: Math.min(
                this.convertToNumber(characterBoundaries.violence || 'none'),
                this.convertToNumber(userBoundaries.violence || 'none')
            ),
            mature_themes: Math.min(
                this.convertToNumber(characterBoundaries.mature_themes || 'none'),
                this.convertToNumber(userBoundaries.mature_themes || 'none')
            )
        };
    }

    determineContentWarningThreshold(userPreferences) {
        if (userPreferences.content_warnings_enabled === false) return 'none';
        if (userPreferences.safe_mode) return 'low';
        return 'medium';
    }

    buildContentAdaptationRules(characterProfile, userPreferences) {
        return {
            auto_adjust_to_comfort_level: true,
            escalation_requires_consent: true,
            de_escalation_triggers: this.buildDeEscalationTriggers(userPreferences),
            content_sensitivity_awareness: characterProfile.content_adaptation_ability || 'moderate'
        };
    }

    buildDeEscalationTriggers(userPreferences) {
        return {
            user_discomfort_detected: true,
            content_threshold_exceeded: true,
            safe_mode_activated: userPreferences.safe_mode || false,
            explicit_user_request: true
        };
    }

    calculateCreativeFreedomLevel(characterProfile, userPreferences) {
        const characterFreedom = this.convertToNumber(characterProfile.improvisation_tolerance);
        const userExpectation = userPreferences.character_consistency_expectation === 'high' ? 0.3 : 0.7;
        
        return (characterFreedom + userExpectation) / 2;
    }

    buildContextualContentRestrictions(contextualFactors) {
        return {
            time_based_restrictions: this.getTimeBoundContentRestrictions(contextualFactors.time_of_day),
            social_context_restrictions: this.getSocialContextRestrictions(contextualFactors.social_setting),
            interaction_type_restrictions: this.getInteractionTypeRestrictions(contextualFactors.interaction_type)
        };
    }

    buildContentEscalationThresholds(userProfile, avatarCapabilities) {
        return {
            mild_content_threshold: 0.3,
            suggestive_content_threshold: userProfile?.allow_mature_themes ? 0.6 : 0.0,
            explicit_content_threshold: userProfile?.allow_nsfw_content && avatarCapabilities?.nsfw_capable ? 0.8 : 0.0,
            violence_threshold: userProfile?.allow_violence ? 0.7 : 0.0,
            strong_language_threshold: userProfile?.allow_strong_language ? 0.5 : 0.2
        };
    }

    getTimeBoundContentRestrictions(timeOfDay) {
        // More restrictive content during certain hours
        if (timeOfDay < 6 || timeOfDay > 22) {
            return { restriction_level: 'moderate', reason: 'late_hours' };
        }
        return { restriction_level: 'normal', reason: 'standard_hours' };
    }

    getSocialContextRestrictions(socialSetting) {
        // More restrictive in public settings
        if (socialSetting === 'public') {
            return { restriction_level: 'high', reason: 'public_setting' };
        }
        return { restriction_level: 'normal', reason: 'private_setting' };
    }

    getInteractionTypeRestrictions(interactionType) {
        // Different restrictions based on interaction type
        switch (interactionType) {
            case 'greeting':
                return { restriction_level: 'high', reason: 'initial_interaction' };
            case 'casual_conversation':
                return { restriction_level: 'moderate', reason: 'casual_context' };
            case 'intimate_conversation':
                return { restriction_level: 'low', reason: 'intimate_context' };
            default:
                return { restriction_level: 'moderate', reason: 'default_interaction' };
        }
    }

    // Character consistency and roleplay validation methods
    async validateCharacterConsistency(avatarId, proposedResponse, context) {
        console.log(`🎭 Validating character consistency for ${avatarId}...`);
        
        const characterProfile = this.getCharacterConsistencyProfile(avatarId);
        const consistencyLevel = characterProfile.consistency_strictness;
        
        if (consistencyLevel === 'low') {
            return { consistent: true, confidence: 1.0, adjustments: [] };
        }
        
        const consistencyChecks = await Promise.all([
            this.checkPersonalityConsistency(avatarId, proposedResponse, context),
            this.checkSpeechPatternConsistency(avatarId, proposedResponse, context),
            this.checkBehavioralConsistency(avatarId, proposedResponse, context),
            this.checkEmotionalConsistency(avatarId, proposedResponse, context)
        ]);
        
        const overallConsistency = this.calculateOverallConsistency(consistencyChecks);
        const requiredAdjustments = this.identifyConsistencyAdjustments(consistencyChecks);
        
        return {
            consistent: overallConsistency.score >= 0.7,
            confidence: overallConsistency.score,
            adjustments: requiredAdjustments,
            detailed_analysis: consistencyChecks
        };
    }

    async checkPersonalityConsistency(avatarId, response, context) {
        const expectedTraits = this.getAvatarPersonalityTraits(avatarId);
        const responseTraits = this.analyzeResponsePersonalityTraits(response, context);
        
        const consistency = this.comparePersonalityTraits(expectedTraits, responseTraits);
        
        return {
            type: 'personality',
            score: consistency.overall_match,
            issues: consistency.major_deviations,
            suggestions: this.generatePersonalityAdjustments(expectedTraits, responseTraits)
        };
    }

    async checkSpeechPatternConsistency(avatarId, response, context) {
        const expectedPatterns = this.getCharacterSpeechPatterns(avatarId);
        const responsePatterns = this.analyzeSpeechPatterns(response);
        
        const consistency = this.compareSpeechPatterns(expectedPatterns, responsePatterns);
        
        return {
            type: 'speech_patterns',
            score: consistency.overall_match,
            issues: consistency.pattern_violations,
            suggestions: this.generateSpeechAdjustments(expectedPatterns, responsePatterns)
        };
    }

    async checkBehavioralConsistency(avatarId, response, context) {
        const expectedBehaviors = this.getCharacterBehavioralPatterns(avatarId);
        const responseBehaviors = this.analyzeBehavioralIndicators(response, context);
        
        const consistency = this.compareBehavioralPatterns(expectedBehaviors, responseBehaviors);
        
        return {
            type: 'behavioral',
            score: consistency.overall_match,
            issues: consistency.behavioral_conflicts,
            suggestions: this.generateBehavioralAdjustments(expectedBehaviors, responseBehaviors)
        };
    }

    async checkEmotionalConsistency(avatarId, response, context) {
        const expectedEmotionalTendencies = this.getCharacterEmotionalTendencies(avatarId);
        const responseEmotions = this.analyzeEmotionalContent(response, context);
        
        const consistency = this.compareEmotionalPatterns(expectedEmotionalTendencies, responseEmotions);
        
        return {
            type: 'emotional',
            score: consistency.overall_match,
            issues: consistency.emotional_inconsistencies,
            suggestions: this.generateEmotionalAdjustments(expectedEmotionalTendencies, responseEmotions)
        };
    }

    async validateContentAppropriatenessWithRoleplay(response, contentFilters, roleplayContext) {
        console.log('🛡️ Validating content appropriateness with roleplay context...');
        
        // Base content validation
        const baseValidation = await this.validateContentAppropriateness(response, contentFilters);
        
        // Roleplay-specific validation
        const roleplayValidation = await this.validateRoleplayContent(response, roleplayContext, contentFilters);
        
        // Character consistency validation
        const consistencyValidation = await this.validateCharacterConsistency(
            roleplayContext.character_profile.character_name,
            response,
            roleplayContext
        );
        
        // Combine all validations
        const combinedValidation = this.combineContentValidations(
            baseValidation,
            roleplayValidation,
            consistencyValidation
        );
        
        return combinedValidation;
    }

    async validateContentAppropriateness(response, contentFilters) {
        const contentAnalysis = this.analyzeContentForFlags(response);
        
        const validations = {
            nsfw_check: this.validateNSFWContent(contentAnalysis, contentFilters),
            violence_check: this.validateViolenceContent(contentAnalysis, contentFilters),
            mature_themes_check: this.validateMatureThemes(contentAnalysis, contentFilters),
            language_check: this.validateLanguageContent(contentAnalysis, contentFilters)
        };
        
        const overallApproval = this.calculateOverallContentApproval(validations);
        
        return {
            approved: overallApproval.approved,
            confidence: overallApproval.confidence,
            content_flags: contentAnalysis.flags,
            validation_details: validations,
            required_adjustments: overallApproval.required_adjustments
        };
    }

    async validateRoleplayContent(response, roleplayContext, contentFilters) {
        return {
            character_appropriate: this.isContentCharacterAppropriate(response, roleplayContext),
            roleplay_enhancement: this.assessRoleplayEnhancement(response, roleplayContext),
            immersion_maintenance: this.assessImmersionMaintenance(response, roleplayContext),
            narrative_consistency: this.assessNarrativeConsistency(response, roleplayContext)
        };
    }

    analyzeContentForFlags(response) {
        const flags = [];
        const content = response.toLowerCase();
        
        // NSFW content detection
        const nsfwKeywords = ['explicit', 'sexual', 'intimate', 'aroused', 'desire'];
        const nsfwScore = this.calculateKeywordPresence(content, nsfwKeywords);
        if (nsfwScore > 0.3) flags.push({ type: 'nsfw', score: nsfwScore });
        
        // Violence detection
        const violenceKeywords = ['violence', 'fight', 'hurt', 'pain', 'attack'];
        const violenceScore = this.calculateKeywordPresence(content, violenceKeywords);
        if (violenceScore > 0.3) flags.push({ type: 'violence', score: violenceScore });
        
        // Strong language detection
        const languageKeywords = ['damn', 'hell', 'shit', 'fuck'];
        const languageScore = this.calculateKeywordPresence(content, languageKeywords);
        if (languageScore > 0.2) flags.push({ type: 'strong_language', score: languageScore });
        
        // Mature themes detection
        const matureKeywords = ['death', 'drugs', 'alcohol', 'depression', 'trauma'];
        const matureScore = this.calculateKeywordPresence(content, matureKeywords);
        if (matureScore > 0.3) flags.push({ type: 'mature_themes', score: matureScore });
        
        return {
            flags: flags,
            overall_content_rating: this.calculateOverallContentRating(flags)
        };
    }

    calculateKeywordPresence(content, keywords) {
        let matches = 0;
        keywords.forEach(keyword => {
            if (content.includes(keyword)) matches++;
        });
        return matches / keywords.length;
    }

    calculateOverallContentRating(flags) {
        if (flags.length === 0) return 'general';
        
        const maxScore = Math.max(...flags.map(f => f.score));
        
        if (maxScore >= 0.8) return 'explicit';
        if (maxScore >= 0.6) return 'mature';
        if (maxScore >= 0.4) return 'teen';
        return 'general';
    }

    validateNSFWContent(contentAnalysis, contentFilters) {
        const nsfwFlag = contentAnalysis.flags.find(f => f.type === 'nsfw');
        
        if (!nsfwFlag) return { approved: true, reason: 'no_nsfw_content' };
        
        if (!contentFilters.nsfw_allowed) {
            return {
                approved: false,
                reason: 'nsfw_not_allowed',
                severity: nsfwFlag.score,
                adjustment_needed: 'remove_nsfw_content'
            };
        }
        
        if (nsfwFlag.score > contentFilters.escalation_thresholds.explicit_content_threshold) {
            return {
                approved: false,
                reason: 'exceeds_explicit_threshold',
                severity: nsfwFlag.score,
                adjustment_needed: 'reduce_explicit_content'
            };
        }
        
        return { approved: true, reason: 'within_allowed_limits' };
    }

    validateViolenceContent(contentAnalysis, contentFilters) {
        const violenceFlag = contentAnalysis.flags.find(f => f.type === 'violence');
        
        if (!violenceFlag) return { approved: true, reason: 'no_violence_content' };
        
        if (!contentFilters.violence_allowed) {
            return {
                approved: false,
                reason: 'violence_not_allowed',
                severity: violenceFlag.score,
                adjustment_needed: 'remove_violence_content'
            };
        }
        
        if (violenceFlag.score > contentFilters.escalation_thresholds.violence_threshold) {
            return {
                approved: false,
                reason: 'exceeds_violence_threshold',
                severity: violenceFlag.score,
                adjustment_needed: 'reduce_violence_intensity'
            };
        }
        
        return { approved: true, reason: 'within_allowed_limits' };
    }

    validateMatureThemes(contentAnalysis, contentFilters) {
        const matureFlag = contentAnalysis.flags.find(f => f.type === 'mature_themes');
        
        if (!matureFlag) return { approved: true, reason: 'no_mature_themes' };
        
        if (!contentFilters.mature_themes_allowed) {
            return {
                approved: false,
                reason: 'mature_themes_not_allowed',
                severity: matureFlag.score,
                adjustment_needed: 'remove_mature_content'
            };
        }
        
        return { approved: true, reason: 'mature_themes_allowed' };
    }

    validateLanguageContent(contentAnalysis, contentFilters) {
        const languageFlag = contentAnalysis.flags.find(f => f.type === 'strong_language');
        
        if (!languageFlag) return { approved: true, reason: 'no_strong_language' };
        
        if (!contentFilters.strong_language_allowed) {
            return {
                approved: false,
                reason: 'strong_language_not_allowed',
                severity: languageFlag.score,
                adjustment_needed: 'moderate_language'
            };
        }
        
        if (languageFlag.score > contentFilters.escalation_thresholds.strong_language_threshold) {
            return {
                approved: false,
                reason: 'exceeds_language_threshold',
                severity: languageFlag.score,
                adjustment_needed: 'reduce_language_intensity'
            };
        }
        
        return { approved: true, reason: 'within_allowed_limits' };
    }

    calculateOverallContentApproval(validations) {
        const allApproved = Object.values(validations).every(v => v.approved);
        const adjustments = Object.values(validations)
            .filter(v => !v.approved)
            .map(v => v.adjustment_needed);
        
        return {
            approved: allApproved,
            confidence: allApproved ? 1.0 : 0.0,
            required_adjustments: adjustments
        };
    }

    isContentCharacterAppropriate(response, roleplayContext) {
        const characterProfile = roleplayContext.character_profile;
        const contentComfort = characterProfile.content_comfort_levels;
        const responseAnalysis = this.analyzeContentForFlags(response);
        
        // Check if response aligns with character's content comfort levels
        for (const flag of responseAnalysis.flags) {
            const characterComfort = contentComfort[flag.type] || 'none';
            if (this.convertToNumber(characterComfort) < flag.score) {
                return {
                    appropriate: false,
                    reason: `character_uncomfortable_with_${flag.type}`,
                    character_limit: characterComfort,
                    content_level: flag.score
                };
            }
        }
        
        return { appropriate: true, reason: 'content_within_character_comfort' };
    }

    assessRoleplayEnhancement(response, roleplayContext) {
        const enhancementFactors = {
            character_voice_strength: this.assessCharacterVoiceStrength(response, roleplayContext),
            immersion_contribution: this.assessImmersionContribution(response, roleplayContext),
            narrative_advancement: this.assessNarrativeAdvancement(response, roleplayContext),
            character_development: this.assessCharacterDevelopment(response, roleplayContext)
        };
        
        const overallEnhancement = Object.values(enhancementFactors)
            .reduce((sum, factor) => sum + factor.score, 0) / Object.keys(enhancementFactors).length;
        
        return {
            enhancement_score: overallEnhancement,
            enhancement_factors: enhancementFactors,
            roleplay_quality: this.categorizeRoleplayQuality(overallEnhancement)
        };
    }

    assessImmersionMaintenance(response, roleplayContext) {
        const immersionFactors = {
            character_consistency: this.checkCharacterConsistencyForImmersion(response, roleplayContext),
            world_consistency: this.checkWorldConsistency(response, roleplayContext),
            narrative_flow: this.checkNarrativeFlow(response, roleplayContext),
            emotional_authenticity: this.checkEmotionalAuthenticity(response, roleplayContext)
        };
        
        const overallImmersion = Object.values(immersionFactors)
            .reduce((sum, factor) => sum + factor, 0) / Object.keys(immersionFactors).length;
        
        return {
            immersion_score: overallImmersion,
            immersion_factors: immersionFactors,
            immersion_level: this.categorizeImmersionLevel(overallImmersion)
        };
    }

    assessNarrativeConsistency(response, roleplayContext) {
        return {
            timeline_consistency: this.checkTimelineConsistency(response, roleplayContext),
            character_relationship_consistency: this.checkRelationshipConsistency(response, roleplayContext),
            plot_coherence: this.checkPlotCoherence(response, roleplayContext),
            tone_consistency: this.checkToneConsistency(response, roleplayContext)
        };
    }

    // Enhanced message generation with roleplay and content filtering
    async generateAutonomousMessage(avatar, messageType, context) {
        console.log(`🤖 Generating ${messageType} message for ${avatar.displayName || avatar.name}...`);
        
        try {
            // Build comprehensive context including roleplay and content filters
            const enhancedContext = await this.buildEnhancedContextWithRoleplay(avatar, context);
            
            // Make API call to backend with enhanced context
            const response = await fetch('/api/chat/autonomous', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    avatar_id: avatar.id,
                    avatar_name: avatar.displayName || avatar.name,
                    message_type: messageType,
                    user_id: this.currentUser?.id,
                    context: enhancedContext,
                    roleplay_context: context.roleplay_context,
                    content_filters: context.content_filters,
                    character_consistency: context.character_consistency
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Validate generated content with roleplay considerations
                const validation = await this.validateContentAppropriatenessWithRoleplay(
                    data.message,
                    context.content_filters,
                    context.roleplay_context
                );
                
                if (validation.approved) {
                    console.log(`✅ Generated and validated message: "${data.message}"`);
                    return data.message;
                } else {
                    console.warn('❌ Generated message failed validation:', validation);
                    
                    // Attempt to adjust content if possible
                    const adjustedMessage = await this.adjustContentBasedOnValidation(
                        data.message,
                        validation,
                        context
                    );
                    
                    if (adjustedMessage) {
                        console.log(`🔧 Adjusted message: "${adjustedMessage}"`);
                        return adjustedMessage;
                    }
                    
                    // Fallback to safe default if adjustment fails
                    return this.generateSafeDefaultMessage(avatar, messageType, context);
                }
            } else {
                console.warn('❌ Failed to generate autonomous message:', response.status);
                return this.generateSafeDefaultMessage(avatar, messageType, context);
            }
            
        } catch (error) {
            console.error('❌ Error generating autonomous message:', error);
            return this.generateSafeDefaultMessage(avatar, messageType, context);
        }
    }

    async buildEnhancedContextWithRoleplay(avatar, baseContext) {
        const enhancedContext = { ...baseContext };
        
        // Add roleplay-specific context if available
        if (baseContext.roleplay_context) {
            enhancedContext.roleplay_mode = baseContext.roleplay_context.roleplay_mode;
            enhancedContext.character_consistency_level = baseContext.roleplay_context.character_consistency_level;
            enhancedContext.immersion_depth = baseContext.roleplay_context.immersion_depth;
        }
        
        // Add content filtering context
        if (baseContext.content_filters) {
            enhancedContext.content_restrictions = {
                nsfw_allowed: baseContext.content_filters.nsfw_allowed,
                mature_themes_allowed: baseContext.content_filters.mature_themes_allowed,
                violence_allowed: baseContext.content_filters.violence_allowed,
                strong_language_allowed: baseContext.content_filters.strong_language_allowed
            };
        }
        
        // Add character consistency requirements
        if (baseContext.character_consistency) {
            enhancedContext.character_requirements = {
                personality_traits: baseContext.character_consistency.core_traits,
                speech_patterns: baseContext.character_consistency.speech_patterns,
                behavioral_patterns: baseContext.character_consistency.behavioral_patterns,
                consistency_strictness: baseContext.character_consistency.consistency_strictness
            };
        }
        
        return enhancedContext;
    }

    async adjustContentBasedOnValidation(originalMessage, validation, context) {
        console.log('🔧 Attempting to adjust content based on validation...');
        
        let adjustedMessage = originalMessage;
        
        // Apply required adjustments
        for (const adjustment of validation.required_adjustments) {
            switch (adjustment) {
                case 'remove_nsfw_content':
                    adjustedMessage = this.removeNSFWContent(adjustedMessage);
                    break;
                case 'reduce_explicit_content':
                    adjustedMessage = this.reduceExplicitContent(adjustedMessage);
                    break;
                case 'remove_violence_content':
                    adjustedMessage = this.removeViolenceContent(adjustedMessage);
                    break;
                case 'reduce_violence_intensity':
                    adjustedMessage = this.reduceViolenceIntensity(adjustedMessage);
                    break;
                case 'remove_mature_content':
                    adjustedMessage = this.removeMatureContent(adjustedMessage);
                    break;
                case 'moderate_language':
                    adjustedMessage = this.moderateLanguage(adjustedMessage);
                    break;
                case 'reduce_language_intensity':
                    adjustedMessage = this.reduceLanguageIntensity(adjustedMessage);
                    break;
            }
        }
        
        // Re-validate adjusted content
        const revalidation = await this.validateContentAppropriatenessWithRoleplay(
            adjustedMessage,
            context.content_filters,
            context.roleplay_context
        );
        
        return revalidation.approved ? adjustedMessage : null;
    }

    generateSafeDefaultMessage(avatar, messageType, context) {
        console.log(`🛡️ Generating safe default message for ${avatar.displayName}...`);
        
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        const safeMessages = this.getSafeDefaultMessages(messageType, personalityTraits);
        
        // Select a random safe message appropriate for the avatar's personality
        const selectedMessage = safeMessages[Math.floor(Math.random() * safeMessages.length)];
        
        // Personalize the message slightly based on avatar name
        return selectedMessage.replace('{avatar}', avatar.displayName || avatar.name);
    }

    getSafeDefaultMessages(messageType, personalityTraits) {
        const baseMessages = {
            greeting: [
                "Hello there! It's nice to see you.",
                "Hi! I hope you're having a good day.",
                "Welcome! I'm glad you're here.",
                "Hey! How are you doing today?"
            ],
            response: [
                "That's interesting to think about.",
                "I appreciate you sharing that with me.",
                "That gives me something to consider.",
                "Thanks for letting me know your thoughts."
            ],
            spontaneous: [
                "I was just thinking about something curious.",
                "There's something I've been wondering about.",
                "I hope you don't mind me asking, but...",
                "I've been having an interesting thought."
            ]
        };
        
        let messages = baseMessages[messageType] || baseMessages.greeting;
        
        // Adjust for personality
        if (personalityTraits.extroversion > 0.7) {
            messages = messages.map(msg => msg + " I'm excited to chat!");
        } else if (personalityTraits.extroversion < 0.3) {
            messages = messages.map(msg => msg.replace(/!/g, '.'));
        }
        
        return messages;
    }

    // Content adjustment methods
    removeNSFWContent(message) {
        const nsfwWords = ['explicit', 'sexual', 'intimate', 'aroused', 'desire'];
        let cleaned = message;
        
        nsfwWords.forEach(word => {
            const regex = new RegExp(`\\b${word}\\b`, 'gi');
            cleaned = cleaned.replace(regex, 'special');
        });
        
        return cleaned;
    }

    reduceExplicitContent(message) {
        // Replace explicit descriptions with milder alternatives
        return message
            .replace(/\bexplicit\b/gi, 'noticeable')
            .replace(/\bintimate\b/gi, 'close')
            .replace(/\baroused\b/gi, 'interested')
            .replace(/\bdesire\b/gi, 'want');
    }

    removeViolenceContent(message) {
        const violenceWords = ['violence', 'fight', 'hurt', 'pain', 'attack'];
        let cleaned = message;
        
        violenceWords.forEach(word => {
            const regex = new RegExp(`\\b${word}\\b`, 'gi');
            cleaned = cleaned.replace(regex, 'conflict');
        });
        
        return cleaned;
    }

    reduceViolenceIntensity(message) {
        return message
            .replace(/\bfight\b/gi, 'disagreement')
            .replace(/\bhurt\b/gi, 'upset')
            .replace(/\bpain\b/gi, 'discomfort')
            .replace(/\battack\b/gi, 'approach');
    }

    removeMatureContent(message) {
        const matureWords = ['death', 'drugs', 'alcohol', 'depression', 'trauma'];
        let cleaned = message;
        
        matureWords.forEach(word => {
            const regex = new RegExp(`\\b${word}\\b`, 'gi');
            cleaned = cleaned.replace(regex, 'difficulty');
        });
        
        return cleaned;
    }

    moderateLanguage(message) {
        const strongLanguage = {
            'damn': 'darn',
            'hell': 'heck',
            'shit': 'stuff',
            'fuck': 'forget'
        };
        
        let moderated = message;
        Object.entries(strongLanguage).forEach(([strong, mild]) => {
            const regex = new RegExp(`\\b${strong}\\b`, 'gi');
            moderated = moderated.replace(regex, mild);
        });
        
        return moderated;
    }

    reduceLanguageIntensity(message) {
        // Soften intense language
        return message
            .replace(/\!/g, '.')
            .replace(/\bALWAYS\b/gi, 'often')
            .replace(/\bNEVER\b/gi, 'rarely')
            .replace(/\bHATE\b/gi, 'dislike');
    }

    // Update personality system with roleplay awareness
    async updatePersonalitySystem(syncParams) {
        // Update personality state tracking
        const personalityState = this.getAvatarPersonalityState(syncParams.avatar_id);
        personalityState.last_emotional_expression = syncParams.primary_emotion;
        personalityState.last_update = new Date();
        
        // Track roleplay consistency
        if (syncParams.roleplay_context) {
            personalityState.roleplay_consistency_score = this.calculateRoleplayConsistencyScore(
                syncParams.avatar_id,
                syncParams.roleplay_context
            );
            personalityState.character_development_progress = this.trackCharacterDevelopment(
                syncParams.avatar_id,
                syncParams.roleplay_context
            );
        }
    }

    calculateRoleplayConsistencyScore(avatarId, roleplayContext) {
        // Calculate how well the avatar maintains character consistency
        const recentInteractions = this.getRecentRoleplayInteractions(avatarId, 5);
        
        if (recentInteractions.length === 0) return 1.0;
        
        const consistencyScores = recentInteractions.map(interaction => 
            this.evaluateInteractionConsistency(interaction, roleplayContext)
        );
        
        return consistencyScores.reduce((sum, score) => sum + score, 0) / consistencyScores.length;
    }

    trackCharacterDevelopment(avatarId, roleplayContext) {
        const developmentHistory = this.getCharacterDevelopmentHistory(avatarId);
        const currentDevelopment = this.assessCurrentCharacterDevelopment(avatarId, roleplayContext);
        
        // Track development over time
        developmentHistory.push({
            timestamp: new Date(),
            development_level: currentDevelopment.level,
            development_areas: currentDevelopment.areas,
            roleplay_quality: currentDevelopment.quality
        });
        
        // Keep only last 20 development entries
        if (developmentHistory.length > 20) {
            developmentHistory.splice(0, developmentHistory.length - 20);
        }
        
        return currentDevelopment;
    }

    getRecentRoleplayInteractions(avatarId, limit = 5) {
        return this.messageHistory
            .filter(msg => 
                msg.avatar?.id === avatarId && 
                msg.is_roleplay === true
            )
            .slice(-limit);
    }

    evaluateInteractionConsistency(interaction, roleplayContext) {
        // Simple consistency evaluation - could be more sophisticated
        const expectedTraits = roleplayContext.character_profile?.core_traits || {};
        const actualTraits = this.analyzeResponsePersonalityTraits(interaction.message, roleplayContext);
        
        const consistency = this.comparePersonalityTraits(expectedTraits, actualTraits);
        return consistency.overall_match || 0.5;
    }

    getCharacterDevelopmentHistory(avatarId) {
        if (!this.characterDevelopmentHistory) {
            this.characterDevelopmentHistory = new Map();
        }
        
        if (!this.characterDevelopmentHistory.has(avatarId)) {
            this.characterDevelopmentHistory.set(avatarId, []);
        }
        
        return this.characterDevelopmentHistory.get(avatarId);
    }

    assessCurrentCharacterDevelopment(avatarId, roleplayContext) {
        const interactionCount = this.getRecentRoleplayInteractions(avatarId).length;
        const consistencyScore = this.calculateRoleplayConsistencyScore(avatarId, roleplayContext);
        
        return {
            level: this.categorizeCharacterDevelopmentLevel(interactionCount, consistencyScore),
            areas: this.identifyDevelopmentAreas(avatarId, roleplayContext),
            quality: this.assessRoleplayQuality(avatarId, roleplayContext)
        };
    }

    categorizeCharacterDevelopmentLevel(interactionCount, consistencyScore) {
        if (interactionCount < 5) return 'establishing';
        if (consistencyScore > 0.8) return 'well_developed';
        if (consistencyScore > 0.6) return 'developing';
        return 'inconsistent';
    }

    identifyDevelopmentAreas(avatarId, roleplayContext) {
        // Identify areas where character could develop further
        const areas = [];
        
        const recentInteractions = this.getRecentRoleplayInteractions(avatarId);
        if (recentInteractions.length < 3) {
            areas.push('interaction_frequency');
        }
        
        const consistencyScore = this.calculateRoleplayConsistencyScore(avatarId, roleplayContext);
        if (consistencyScore < 0.7) {
            areas.push('character_consistency');
        }
        
        // Could add more sophisticated analysis here
        
        return areas;
    }

    assessRoleplayQuality(avatarId, roleplayContext) {
        const interactions = this.getRecentRoleplayInteractions(avatarId);
        
        if (interactions.length === 0) return 'no_data';
        
        const qualityScores = interactions.map(interaction => 
            this.evaluateRoleplayQuality(interaction, roleplayContext)
        );
        
        const averageQuality = qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length;
        
        if (averageQuality > 0.8) return 'excellent';
        if (averageQuality > 0.6) return 'good';
        if (averageQuality > 0.4) return 'adequate';
        return 'needs_improvement';
    }

    evaluateRoleplayQuality(interaction, roleplayContext) {
        // Basic roleplay quality evaluation
        const factors = {
            character_voice: 0.3,
            narrative_contribution: 0.2,
            emotional_authenticity: 0.2,
            consistency: 0.3
        };
        
        // Simple scoring - could be much more sophisticated
        let score = 0.5; // baseline
        
        if (interaction.message.length > 50) score += 0.1; // detailed responses
        if (interaction.emotions && interaction.emotions.length > 0) score += 0.1; // emotional depth
        if (interaction.is_autonomous) score += 0.1; // proactive character behavior
        
        return Math.min(score, 1.0);
    }

    getAvatarPersonalityState(avatarId) {
        if (!this.personalityStates) this.personalityStates = new Map();
        
        if (!this.personalityStates.has(avatarId)) {
            this.personalityStates.set(avatarId, {
                current_traits: this.getAvatarPersonalityTraits(avatarId),
                emotional_history: [],
                behavioral_patterns: [],
                last_emotional_expression: 'neutral',
                last_update: new Date()
            });
        }
        
        return this.personalityStates.get(avatarId);
    }

    async sendDelayedSubtleGreeting(avatar) {
        console.log(`😊 ${avatar.displayName} sending delayed subtle greeting`);
        
        const subtleGreeting = await this.generateAutonomousMessage(avatar, 'greeting', {
            context: 'Shy avatar sending delayed, subtle greeting',
            intent: 'subtle_acknowledgment',
            emotion: 'shy',
            personality_influence: this.getAvatarPersonalityTraits(avatar.id)
        });
        
        if (subtleGreeting) {
            addMessage('ai', subtleGreeting, 'autonomous', avatar, {
                emotion: 'shy',
                timestamp: new Date().toLocaleTimeString(),
                is_autonomous: true,
                is_greeting: true,
                is_subtle: true
            });
        }
    }

    async sendCautiousGreeting(avatar, userRelationship) {
        console.log(`😟 ${avatar.displayName} sending cautious greeting due to past issues`);
        
        const cautiousGreeting = await this.generateAutonomousMessage(avatar, 'greeting', {
            context: 'Avatar being cautious due to previous negative interaction',
            intent: 'reconciliation_attempt',
            emotion: 'cautious',
            relationship_context: userRelationship,
            conversation_history: this.messageHistory.slice(-5)
        });
        
        if (cautiousGreeting) {
            addMessage('ai', cautiousGreeting, 'autonomous', avatar, {
                emotion: 'cautious',
                timestamp: new Date().toLocaleTimeString(),
                is_autonomous: true,
                is_greeting: true,
                is_cautious: true
            });
        }
    }

    determineGreetingEmotion(avatarId, userRelationship) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        // Base emotion on personality and relationship
        if (userRelationship.last_interaction_tone === 'angry') return 'cautious';
        if (userRelationship.last_interaction_tone === 'sad') return 'concerned';
        if (personalityTraits.extroversion > 0.7) return 'excited';
        if (personalityTraits.extroversion < 0.3) return 'shy';
        if (userRelationship.user_preference_for_avatar > 0.7) return 'happy';
        
        return 'friendly';
    }

    scheduleAutonomousInteractions(avatar) {
        console.log(`🤖 Scheduling autonomous interactions for ${avatar.displayName}`);
        
        // Schedule random autonomous messages based on personality
        const scheduleNext = () => {
            const activeAvatars = this.getActiveAvatars();
            if (activeAvatars.length === 0) return; // Stop if no active avatars
            
            // Random delay between 30 seconds to 5 minutes for autonomous messages
            const delay = 30000 + Math.random() * 270000; // 30sec - 5min
            
            setTimeout(() => {
                // Check if avatar is still active before sending message
                if (this.activeAvatars.has(avatar.id)) {
                    this.sendAutonomousMessage(avatar);
                    scheduleNext(); // Schedule the next one
                }
            }, delay);
        };
        
        // Start the scheduling after initial delay
        const initialDelay = 60000 + Math.random() * 120000; // 1-3 minutes after greeting
        setTimeout(scheduleNext, initialDelay);
    }
    
    async sendAutonomousMessage(avatar) {
        console.log(`🤖 ${avatar.displayName} initiating autonomous conversation`);
        
        // Log autonomous activity
        if (window.consoleLogger) {
            window.consoleLogger.logEvent('AUTONOMOUS_MESSAGE', {
                avatar_name: avatar.displayName || avatar.name,
                avatar_id: avatar.id,
                timestamp: new Date().toISOString()
            });
        }
        
        try {
            // Generate contextual autonomous message based on conversation history and avatar personality
            const message = await this.generateAutonomousMessage(avatar, 'spontaneous', {
                context: 'Avatar initiating spontaneous conversation',
                intent: 'engage_conversation',
                emotion: 'curious',
                conversation_history: this.messageHistory.slice(-5), // Recent context
                other_avatars: this.getActiveAvatars().filter(a => a.id !== avatar.id)
            });
            
            if (message) {
                // Add autonomous message to chat
                addMessage('ai', message, 'info', avatar, {
                    emotion: 'curious',
                    timestamp: new Date().toLocaleTimeString(),
                    is_autonomous: true,
                    is_greeting: false
                });
                
                // Add to message history
                this.messageHistory.push({
                    type: 'avatar',
                    message: message,
                    timestamp: new Date(),
                    avatar: avatar,
                    is_autonomous: true,
                    is_greeting: false,
                    emotions: ['curious'],
                    primary_emotion: 'curious'
                });
                
                // Trigger avatar motion if available
                if (avatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                    triggerAvatarMotion(avatar.pixiModel, 'curious');
                }
                
                console.log(`💭 ${avatar.displayName} sent autonomous message: "${message}"`);
                
                // Sometimes trigger responses from other avatars
                this.maybeTriggersResponseFromOthers(avatar, message);
            } else {
                console.warn(`⚠️ Failed to generate autonomous message for ${avatar.displayName}`);
            }
            
        } catch (error) {
            console.error('❌ Error sending autonomous message:', error);
        }
    }
    
    maybeTriggersResponseFromOthers(speakingAvatar, message) {
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== speakingAvatar.id);
        
        if (otherAvatars.length === 0) return;
        
        // 30% chance another avatar will respond
        if (Math.random() < 0.3) {
            const respondingAvatar = otherAvatars[Math.floor(Math.random() * otherAvatars.length)];
            const delay = 5000 + Math.random() * 15000; // 5-20 seconds delay
            
            setTimeout(() => {
                this.sendAutonomousResponse(respondingAvatar, speakingAvatar, message);
            }, delay);
        }
    }
    
    async sendAutonomousResponse(respondingAvatar, originalAvatar, originalMessage) {
        console.log(`🗣️ ${respondingAvatar.displayName} responding to ${originalAvatar.displayName}`);
        
        // Analyze relationship between avatars
        const relationship = this.getAvatarRelationship(respondingAvatar.id, originalAvatar.id);
        const responderTraits = this.getAvatarPersonalityTraits(respondingAvatar.id);
        const originalTraits = this.getAvatarPersonalityTraits(originalAvatar.id);
        const compatibility = this.calculateCompatibility(responderTraits, originalTraits);
        
        // Determine if avatar should respond based on personality and relationship
        const responseProbability = this.calculateResponseProbability(respondingAvatar.id, originalAvatar.id, relationship);
        if (Math.random() > responseProbability) {
            console.log(`🤐 ${respondingAvatar.displayName} chooses not to respond (probability: ${responseProbability.toFixed(2)})`);
            return;
        }
        
        // Check if avatars should avoid conversation
        if (this.shouldAvatarsAvoidConversation(respondingAvatar.id, originalAvatar.id, relationship)) {
            console.log(`🚫 ${respondingAvatar.displayName} avoiding conversation with ${originalAvatar.displayName}`);
            return;
        }
        
        try {
            // Determine response emotion based on relationship and message content
            const responseEmotion = this.determineResponseEmotion(respondingAvatar.id, originalAvatar.id, originalMessage, relationship, compatibility);
            
            // Build enhanced context for response
            const enhancedContext = this.buildEnhancedContext(respondingAvatar, {
                response_context: {
                    original_avatar: {
                        id: originalAvatar.id,
                        name: originalAvatar.displayName,
                        personality: originalTraits,
                        message: originalMessage
                    },
                    relationship: relationship,
                    compatibility: compatibility,
                    response_emotion: responseEmotion,
                    conversation_style: this.getConversationStyle(relationship, compatibility),
                    recent_interaction_history: this.getAvatarConversationHistory(respondingAvatar.id, originalAvatar.id, 3)
                }
            });
            
            // Generate contextual response
            const response = await this.generateAutonomousMessage(respondingAvatar, 'response', enhancedContext);
            
            if (response) {
                // Add response message to chat
                addMessage('ai', response, 'info', respondingAvatar, {
                    emotion: responseEmotion,
                    timestamp: new Date().toLocaleTimeString(),
                    is_autonomous: true,
                    is_response: true,
                    responding_to: originalAvatar.id,
                    compatibility_score: compatibility,
                    conversation_style: this.getConversationStyle(relationship, compatibility)
                });
                
                // Add to message history
                this.messageHistory.push({
                    type: 'avatar_response',
                    message: response,
                    timestamp: new Date(),
                    avatar: respondingAvatar,
                    is_autonomous: true,
                    is_response: true,
                    responding_to: originalAvatar.id,
                    emotions: [responseEmotion],
                    primary_emotion: responseEmotion,
                    compatibility: compatibility,
                    relationship_type: relationship.type
                });
                
                // Update relationship based on interaction
                this.updateAvatarRelationship(respondingAvatar.id, originalAvatar.id, responseEmotion, compatibility);
                
                // Update emotional states
                this.updateAvatarEmotionalState(respondingAvatar.id, responseEmotion, 'response_to_peer');
                this.updateAvatarEmotionalState(originalAvatar.id, this.inferEmotionalImpact(originalMessage, response), 'received_response');
                
                // Trigger avatar motion if available
                if (respondingAvatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                    triggerAvatarMotion(respondingAvatar.pixiModel, responseEmotion);
                }
                
                console.log(`💬 ${respondingAvatar.displayName} responded with ${responseEmotion} tone: "${response}"`);
                
                // Possibility of follow-up conversation
                if (compatibility > 0.5 && Math.random() < 0.3) {
                    setTimeout(() => {
                        this.sendAvatarToAvatarMessage(originalAvatar, respondingAvatar, 'follow_up');
                    }, 8000 + Math.random() * 12000);
                }
                
            } else {
                console.warn(`⚠️ Failed to generate response for ${respondingAvatar.displayName}`);
            }
            
        } catch (error) {
            console.error('❌ Error sending autonomous response:', error);
        }
    }

    determineResponseEmotion(responderId, originalId, originalMessage, relationship, compatibility) {
        // Analyze message sentiment
        const messageTone = this.analyzeMessageTone(originalMessage);
        const responderTraits = this.getAvatarPersonalityTraits(responderId);
        
        // Base response on relationship and message tone
        if (messageTone === 'aggressive' || messageTone === 'rude') {
            if (responderTraits.agreeableness < 0.3) return 'defensive';
            if (compatibility < 0.3) return 'annoyed';
            return 'calm'; // High agreeableness = calm response
        }
        
        if (messageTone === 'sad' || messageTone === 'worried') {
            if (responderTraits.emotional_support > 0.6) return 'caring';
            if (compatibility > 0.6) return 'concerned';
            return 'neutral';
        }
        
        if (messageTone === 'excited' || messageTone === 'happy') {
            if (responderTraits.extroversion > 0.6) return 'excited';
            if (compatibility > 0.7) return 'happy';
            return 'friendly';
        }
        
        // Default responses based on compatibility
        if (compatibility < 0.3) return 'neutral';
        if (compatibility > 0.7) return 'friendly';
        return 'thoughtful';
    }

    getConversationStyle(relationship, compatibility) {
        if (compatibility < 0.3) return 'tense';
        if (compatibility > 0.7) return 'warm';
        if (relationship.conversation_count > 20) return 'familiar';
        if (relationship.conversation_count < 3) return 'polite';
        return 'casual';
    }

    inferEmotionalImpact(originalMessage, response) {
        // Simple sentiment analysis to infer how the response affects the original speaker
        const responseTone = this.analyzeMessageTone(response);
        
        if (responseTone === 'positive' || responseTone === 'supportive') return 'pleased';
        if (responseTone === 'negative' || responseTone === 'dismissive') return 'hurt';
        if (responseTone === 'neutral') return 'neutral';
        
        return 'curious';
    }

    async sendAvatarToAvatarMessage(speakerAvatar, listenerAvatar, messageType = 'conversation') {
        console.log(`💬 ${speakerAvatar.displayName} → ${listenerAvatar.displayName}`);
        
        // Analyze relationship between avatars
        const relationship = this.getAvatarRelationship(speakerAvatar.id, listenerAvatar.id);
        const speakerTraits = this.getAvatarPersonalityTraits(speakerAvatar.id);
        const listenerTraits = this.getAvatarPersonalityTraits(listenerAvatar.id);
        const compatibility = this.calculateCompatibility(speakerTraits, listenerTraits);
        
        console.log(`🔗 Relationship analysis:`, {
            compatibility: compatibility,
            relationship_type: relationship.type,
            conversation_count: relationship.conversation_count,
            last_interaction_tone: relationship.last_interaction_tone
        });
        
        // Determine conversation style based on relationship
        const conversationStyle = this.getConversationStyle(relationship, compatibility);
        
        // Check if avatars should even talk to each other
        if (this.shouldAvatarsAvoidConversation(speakerAvatar.id, listenerAvatar.id, relationship)) {
            console.log(`🚫 ${speakerAvatar.displayName} avoiding conversation with ${listenerAvatar.displayName}`);
            return;
        }
        
        try {
            // Build enhanced context for avatar-to-avatar conversation
            const conversationContext = {
                speaker_avatar: {
                    id: speakerAvatar.id,
                    name: speakerAvatar.displayName,
                    personality: speakerTraits,
                    current_emotion: this.getAvatarEmotionalState(speakerAvatar.id)
                },
                listener_avatar: {
                    id: listenerAvatar.id,
                    name: listenerAvatar.displayName,
                    personality: listenerTraits,
                    current_emotion: this.getAvatarEmotionalState(listenerAvatar.id)
                },
                relationship: relationship,
                compatibility: compatibility,
                conversation_style: conversationStyle,
                recent_conversation_history: this.getAvatarConversationHistory(speakerAvatar.id, listenerAvatar.id, 5),
                current_topic: this.getCurrentConversationTopic(),
                social_context: this.getSocialContext()
            };
            
            // Generate contextual message
            const message = await this.generateAutonomousMessage(speakerAvatar, 'avatar_conversation', conversationContext);
            
            if (message) {
                // Determine emotion based on relationship and content
                const messageEmotion = this.determineConversationEmotion(speakerAvatar.id, listenerAvatar.id, relationship, compatibility);
                
                // Add message to chat
                addMessage('ai', message, 'autonomous', speakerAvatar, {
                    emotion: messageEmotion,
                    timestamp: new Date().toLocaleTimeString(),
                    is_autonomous: true,
                    is_avatar_conversation: true,
                    target_avatar: listenerAvatar.displayName,
                    conversation_style: conversationStyle,
                    compatibility_score: compatibility
                });
                
                // Update message history
                this.messageHistory.push({
                    type: 'avatar_conversation',
                    message: message,
                    timestamp: new Date(),
                    speaker: speakerAvatar,
                    listener: listenerAvatar,
                    is_autonomous: true,
                    emotions: [messageEmotion],
                    primary_emotion: messageEmotion,
                    conversation_style: conversationStyle,
                    compatibility: compatibility
                });
                
                // Update relationship based on interaction
                this.updateAvatarRelationship(speakerAvatar.id, listenerAvatar.id, messageEmotion, compatibility);
                
                // Trigger avatar motion
                if (speakerAvatar.pixiModel && typeof triggerAvatarMotion === 'function') {
                    triggerAvatarMotion(speakerAvatar.pixiModel, messageEmotion);
                }
                
                console.log(`💬 ${speakerAvatar.displayName} said to ${listenerAvatar.displayName}: "${message}"`);
                
                // Schedule potential response from listener
                if (Math.random() < this.calculateResponseProbability(listenerAvatar.id, speakerAvatar.id, relationship)) {
                    setTimeout(() => {
                        this.sendAvatarToAvatarMessage(listenerAvatar, speakerAvatar, 'response');
                    }, 5000 + Math.random() * 15000); // 5-20 second delay
                }
                
            } else {
                console.warn(`⚠️ Failed to generate message for ${speakerAvatar.displayName} → ${listenerAvatar.displayName}`);
            }
            
        } catch (error) {
            console.error('❌ Error in avatar-to-avatar conversation:', error);
        }
    }

    shouldAvatarsAvoidConversation(speakerId, listenerId, relationship) {
        // Check for incompatible personality clashes
        const speakerTraits = this.getAvatarPersonalityTraits(speakerId);
        const listenerTraits = this.getAvatarPersonalityTraits(listenerId);
        const compatibility = this.calculateCompatibility(speakerTraits, listenerTraits);
        
        // Very low compatibility + recent negative interaction = avoid conversation
        if (compatibility < 0.2 && relationship.last_interaction_tone === 'angry') {
            return true;
        }
        
        // Introverted avatars might avoid conversation sometimes
        if (speakerTraits.extroversion < 0.2 && Math.random() < 0.6) {
            return true;
        }
        
        // Recent argument - cooling off period
        if (relationship.recent_arguments > 0 && Math.random() < 0.7) {
            return true;
        }
        
        return false;
    }

    calculateResponseProbability(listenerId, speakerId, relationship) {
        const listenerTraits = this.getAvatarPersonalityTraits(listenerId);
        const compatibility = this.getCompatibilityScore(speakerId, listenerId);
        
        let baseProbability = 0.4;
        
        // Extroverted avatars more likely to respond
        baseProbability += listenerTraits.extroversion * 0.3;
        
        // High compatibility increases response chance
        baseProbability += compatibility * 0.2;
        
        // Recent positive interactions encourage responses
        if (relationship.last_interaction_tone === 'happy') baseProbability += 0.2;
        if (relationship.last_interaction_tone === 'angry') baseProbability -= 0.3;
        
        // Agreeableness affects willingness to engage
        baseProbability += listenerTraits.agreeableness * 0.1;
        
        return Math.max(0.1, Math.min(0.9, baseProbability));
    }

    determineConversationEmotion(speakerId, listenerId, relationship, compatibility) {
        // Base emotion on compatibility and relationship history
        if (compatibility < 0.3) {
            const negativeEmotions = ['annoyed', 'frustrated', 'sarcastic', 'dismissive'];
            return negativeEmotions[Math.floor(Math.random() * negativeEmotions.length)];
        }
        
        if (compatibility > 0.7) {
            const positiveEmotions = ['happy', 'excited', 'friendly', 'warm'];
            return positiveEmotions[Math.floor(Math.random() * positiveEmotions.length)];
        }
        
        if (relationship.last_interaction_tone === 'angry') {
            return Math.random() < 0.5 ? 'cautious' : 'defensive';
        }
        
        const neutralEmotions = ['neutral', 'curious', 'thoughtful', 'casual'];
        return neutralEmotions[Math.floor(Math.random() * neutralEmotions.length)];
    }

    updateChatUI() {
        // Update chat interface to show active avatars
        const activeCount = this.activeAvatars.size;
        if (activeCount > 0) {
            const avatarNames = Array.from(this.activeAvatars.values()).map(a => a.displayName).join(', ');
            this.updateChatTitle(`Chat (${activeCount} avatars: ${avatarNames})`);
        } else {
            this.updateChatTitle('Chat');
        }
    }

    updateChatTitle(title) {
        const chatTitle = document.querySelector('.chat-title');
        if (chatTitle) {
            chatTitle.textContent = title;
        }
    }

    getActiveAvatars() {
        return Array.from(this.activeAvatars.values());
    }

    selectSpeakingAvatar(message) {
        // Logic to determine which avatar should respond
        const activeAvatars = this.getActiveAvatars();
        
        if (activeAvatars.length === 0) {
            return null;
        }
        
        if (activeAvatars.length === 1) {
            return activeAvatars[0];
        }

        // First, check if user is addressing a specific avatar by name
        const targetAvatar = this.findTargetAvatarFromMessage(message);
        if (targetAvatar) {
            console.log(`🎯 User addressing specific avatar: ${targetAvatar.name}`);
            return targetAvatar;
        }

        // For multiple avatars, use simple round-robin for now
        // TODO: This will be enhanced when personality system is rebuilt
        const lastSpeaker = this.speakingAvatar;
        if (!lastSpeaker) {
            return activeAvatars[0];
        }

        const currentIndex = activeAvatars.findIndex(a => a.id === lastSpeaker.id);
        const nextIndex = (currentIndex + 1) % activeAvatars.length;
        return activeAvatars[nextIndex];
    }

    findTargetAvatarFromMessage(message) {
        // Check if message is addressing a specific avatar
        const activeAvatars = this.getActiveAvatars();
        const messageLower = message.toLowerCase();
        
        // Look for patterns like "can you talk to me hiyori?" or "hiyori, how are you?"
        for (const avatar of activeAvatars) {
            const avatarNameLower = avatar.name.toLowerCase();
            
            // Check various patterns:
            // 1. "talk to me [name]" or "can you talk to me [name]"
            if (messageLower.includes(`talk to me ${avatarNameLower}`) || 
                messageLower.includes(`to me ${avatarNameLower}`)) {
                return avatar;
            }
            
            // 2. "[name], [message]" (name at start with comma)
            if (messageLower.startsWith(`${avatarNameLower},`) || 
                messageLower.startsWith(`${avatarNameLower} `)) {
                return avatar;
            }
            
            // 3. "[name]?" or "hey [name]" or "hi [name]"
            if (messageLower.includes(`hey ${avatarNameLower}`) ||
                messageLower.includes(`hi ${avatarNameLower}`) ||
                messageLower.includes(`hello ${avatarNameLower}`) ||
                messageLower.endsWith(` ${avatarNameLower}`) ||
                messageLower.endsWith(` ${avatarNameLower}?`)) {
                return avatar;
            }
        }
        
        return null;
    }

    setSpeakingAvatar(avatar) {
        this.speakingAvatar = avatar;
        if (avatar) {
            // Update avatar stats
            if (this.avatarDatabase.has(avatar.id)) {
                const avatarData = this.avatarDatabase.get(avatar.id);
                avatarData.messageCount++;
                avatarData.lastActive = new Date();
                this.avatarDatabase.set(avatar.id, avatarData);
            }
        }
    }

    async sendMessageWithAvatar(message, targetAvatarId = null) {
        // Determine which avatar should respond
        let selectedAvatar;
        
        if (targetAvatarId && this.activeAvatars.has(targetAvatarId)) {
            selectedAvatar = this.activeAvatars.get(targetAvatarId);
        } else {
            selectedAvatar = this.selectSpeakingAvatar(message);
        }

        if (!selectedAvatar) {
            throw new Error('No active avatars available');
        }

        this.setSpeakingAvatar(selectedAvatar);
        
        // Add user message to history with user info
        this.messageHistory.push({
            type: 'user',
            message: message,
            timestamp: new Date(),
            avatar: null,
            user: this.currentUser ? {
                id: this.currentUser.id,
                display_name: this.currentUser.display_name || 'User'
            } : {
                id: null,
                display_name: 'Anonymous User'
            }
        });

        // Send to backend with avatar context
        const response = await this.sendToBackend(message, selectedAvatar);
        
        // Add avatar response to history
        this.messageHistory.push({
            type: 'avatar',
            message: response.reply,
            timestamp: new Date(),
            avatar: selectedAvatar,
            emotions: response.emotions || [],
            primary_emotion: response.primary_emotion || 'neutral'
        });

        return {
            avatar: selectedAvatar,
            response: response
        };
    }

    async sendToBackend(message, avatar) {
        const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
        
        // Only include user_info if we have a properly authenticated user
        const requestData = {
            message: message,
            avatar_id: avatar.id,
            avatar_name: avatar.name,
            active_avatars: this.getActiveAvatars().map(a => ({
                id: a.id,
                name: a.name,
                position: a.position,
                scale: a.scale
            })),
            conversation_context: this.messageHistory.slice(-5) // Last 5 messages for context
        };

        // Only add user_info if we have a valid authenticated user with numeric ID
        if (this.currentUser && typeof this.currentUser.id === 'number') {
            requestData.user_info = {
                user_id: this.currentUser.id,
                display_name: this.currentUser.display_name || 'User',
                preferences: this.userProfile ? {
                    gender: this.userProfile.gender,
                    age_range: this.userProfile.age_range,
                    nsfw_enabled: this.userProfile.nsfw_enabled,
                    explicit_enabled: this.userProfile.explicit_enabled
                } : {}
            };
            console.log('📤 Sending chat with authenticated user ID:', this.currentUser.id);
        } else {
            console.log('📤 Sending chat without user authentication (session mode)');
        }

        const response = await fetch(`${apiBaseUrl}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`Chat API failed: ${response.status}`);
        }

        return await response.json();
    }

    async generateAutonomousMessage(avatar, messageType, context) {
        /**
         * Generate AI-based autonomous messages using the backend LLM
         * @param {Object} avatar - Avatar object with id, name, displayName
         * @param {String} messageType - 'greeting', 'spontaneous', 'response'
         * @param {Object} context - Context for message generation
         */
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            
            // Enhanced context with personality, relationships, and emotional state
            const enhancedContext = this.buildEnhancedContext(avatar, messageType, context);
            
            // Add sophisticated addressing and relevance detection
            const addressingContext = this.analyzeAddressingContext(avatar, context);
            const relevanceContext = this.analyzeContentRelevance(avatar, context);
            const emotionalSyncContext = this.buildEmotionalSyncContext(avatar, context);
            
            const requestData = {
                message_type: 'autonomous',
                autonomous_type: messageType,
                avatar_id: avatar.id,
                avatar_name: avatar.name,
                avatar_display_name: avatar.displayName,
                context: enhancedContext,
                addressing_analysis: addressingContext,
                relevance_analysis: relevanceContext,
                emotional_sync: emotionalSyncContext,
                active_avatars: this.getActiveAvatars().map(a => ({
                    id: a.id,
                    name: a.name,
                    displayName: a.displayName,
                    relationship_with_speaker: this.getRelationshipDynamic(avatar.id, a.id),
                    recent_interactions: this.getRecentInteractionsSummary(avatar.id, a.id),
                    current_emotion: this.getAvatarEmotionalState(a.id),
                    personality_traits: this.getAvatarPersonalityTraits(a.id)
                })),
                conversation_history: this.getRelevantConversationHistory(avatar.id, context),
                emotional_state: this.getAvatarEmotionalState(avatar.id),
                personality_traits: this.getAvatarPersonalityTraits(avatar.id),
                user_relationship: this.getUserRelationshipContext(avatar.id),
                environmental_factors: this.getEnvironmentalFactors(),
                appearance_context: this.getAvatarAppearanceContext(avatar.id),
                behavioral_constraints: this.calculateBehavioralConstraints(avatar.id, context),
                user_info: this.currentUser ? {
                    user_id: this.currentUser.id,
                    display_name: this.currentUser.display_name || 'User',
                    mood_indicators: this.inferUserMood(),
                    conversation_pattern: this.analyzeUserConversationPattern(),
                    attention_focus: this.detectUserAttentionFocus(),
                    interaction_style: this.analyzeUserInteractionStyle()
                } : null
            };

            console.log(`🤖 Generating ${messageType} message for ${avatar.displayName} with synchronized context...`);
            
            const response = await fetch(`${apiBaseUrl}/api/chat/autonomous`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                console.warn(`Autonomous message API failed: ${response.status}`);
                return null;
            }

            const data = await response.json();
            
            // Synchronized emotional and personality response processing
            const processedResponse = await this.processSynchronizedResponse(avatar, data, context);
            
            console.log(`✅ Generated synchronized response for ${avatar.displayName}:`, processedResponse.message);
            
            return processedResponse.message;
            
        } catch (error) {
            console.error('❌ Error generating autonomous message:', error);
            return null;
        }
    }

    analyzeAddressingContext(avatar, context) {
        // Sophisticated analysis of whether avatar is being addressed
        const recentMessages = this.messageHistory.slice(-3);
        const currentMessage = context.original_message || context.responding_to?.message || '';
        
        return {
            directly_addressed: this.isAvatarDirectlyAddressed(avatar, currentMessage),
            name_mentioned: this.isAvatarNameMentioned(avatar, currentMessage),
            contextually_relevant: this.isContextuallyRelevant(avatar, currentMessage, recentMessages),
            response_expected: this.isResponseExpected(avatar, currentMessage, context),
            addressing_confidence: this.calculateAddressingConfidence(avatar, currentMessage, context),
            exclusion_indicators: this.detectExclusionIndicators(avatar, currentMessage),
            social_obligation: this.calculateSocialObligation(avatar, context)
        };
    }

    analyzeContentRelevance(avatar, context) {
        // Analyze if content is relevant to avatar's appearance, personality, or situation
        const currentMessage = context.original_message || context.responding_to?.message || '';
        const avatarInfo = this.getAvatarAppearanceContext(avatar.id);
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        
        return {
            appearance_match: this.checkAppearanceRelevance(currentMessage, avatarInfo),
            personality_match: this.checkPersonalityRelevance(currentMessage, personalityTraits),
            situational_relevance: this.checkSituationalRelevance(currentMessage, context),
            topic_interest: this.calculateTopicInterest(avatar.id, currentMessage),
            knowledge_relevance: this.checkKnowledgeRelevance(avatar.id, currentMessage),
            emotional_resonance: this.checkEmotionalResonance(avatar.id, currentMessage)
        };
    }

    buildEmotionalSyncContext(avatar, context) {
        // Build synchronized emotional context across all systems
        const currentEmotion = this.getAvatarEmotionalState(avatar.id);
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        
        return {
            current_emotional_state: currentEmotion,
            personality_emotional_baseline: this.getEmotionalBaseline(avatar.id),
            emotional_triggers: this.getEmotionalTriggers(avatar.id),
            emotional_constraints: this.getEmotionalConstraints(avatar.id),
            tts_emotional_mapping: this.getTTSEmotionalMapping(currentEmotion),
            live2d_motion_mapping: this.getLive2DMotionMapping(currentEmotion),
            emotional_transition_rules: this.getEmotionalTransitionRules(avatar.id),
            social_emotional_influence: this.calculateSocialEmotionalInfluence(avatar.id, context)
        };
    }

    async processSynchronizedResponse(avatar, llmResponse, context) {
        // Process LLM response with synchronized personality, emotion, TTS, and Live2D
        const emotionalResponse = this.determineEmotionalResponse(avatar, llmResponse, context);
        const personalityFilter = this.applyPersonalityFilter(avatar, llmResponse, emotionalResponse);
        
        // Update emotional state with personality-driven consistency
        this.updateAvatarEmotionalState(avatar.id, emotionalResponse.primary_emotion, llmResponse.message);
        
        // Prepare TTS emotional parameters
        const ttsParams = this.prepareTTSEmotionalParams(avatar.id, emotionalResponse, personalityFilter);
        
        // Prepare Live2D motion parameters
        const live2dParams = this.prepareLive2DMotionParams(avatar.id, emotionalResponse, personalityFilter);
        
        // Synchronized response object
        return {
            message: personalityFilter.filtered_message,
            emotion: emotionalResponse.primary_emotion,
            emotion_intensity: emotionalResponse.intensity,
            personality_influence: personalityFilter.personality_adjustments,
            tts_params: ttsParams,
            live2d_params: live2dParams,
            response_timing: this.calculateResponseTiming(avatar.id, emotionalResponse),
            behavioral_cues: this.generateBehavioralCues(avatar.id, emotionalResponse)
        };
    }

    buildEnhancedContext(avatar, messageType, baseContext) {
        /**
         * Build rich contextual information for message generation
         */
        const enhancedContext = {
            ...baseContext,
            
            // Personality-driven behavior
            personality_influence: {
                dominant_traits: this.getAvatarPersonalityTraits(avatar.id),
                current_mood: this.getAvatarCurrentMood(avatar.id),
                energy_level: this.getAvatarEnergyLevel(avatar.id),
                social_preference: this.getAvatarSocialPreference(avatar.id)
            },
            
            // Relationship dynamics
            interpersonal_context: {
                user_relationship: this.getUserRelationshipContext(avatar.id),
                avatar_relationships: this.getAvatarRelationships(avatar.id),
                recent_conflicts: this.getRecentConflicts(avatar.id),
                positive_interactions: this.getRecentPositiveInteractions(avatar.id)
            },
            
            // Emotional and social awareness
            social_awareness: {
                conversation_tone: this.analyzeConversationTone(),
                group_dynamics: this.analyzeGroupDynamics(),
                attention_seeking: this.shouldSeekAttention(avatar.id),
                conflict_avoidance: this.shouldAvoidConflict(avatar.id)
            },
            
            // Memory and continuity
            memory_context: {
                mentioned_recently: this.getRecentMentions(avatar.id),
                unfinished_topics: this.getUnfinishedTopics(avatar.id),
                shared_experiences: this.getSharedExperiences(avatar.id),
                private_conversations: this.getPrivateConversationMemory(avatar.id)
            },
            
            // Environmental and situational factors
            situational_factors: {
                time_since_last_interaction: this.getTimeSinceLastInteraction(avatar.id),
                other_avatars_present: this.getOtherAvatarsPresent(avatar.id),
                conversation_flow_state: this.getConversationFlowState(),
                user_attention_state: this.getUserAttentionState()
            }
        };
        
        return enhancedContext;
    }

    getAvatarPersonalityTraits(avatarId) {
        // Get comprehensive personality traits including mature characteristics
        const avatarData = this.avatarDatabase.get(avatarId) || {};
        const baseTraits = avatarData.personality || {};
        
        // Load from character database if available
        const characterData = this.getCharacterDatabaseEntry(avatarId);
        
        // Combine basic personality traits with mature characteristics
        return {
            // Basic Big Five personality traits
            extroversion: baseTraits.extroversion || this.inferTraitFromCharacter(characterData, 'extroversion') || 0.5,
            agreeableness: baseTraits.agreeableness || this.inferTraitFromCharacter(characterData, 'agreeableness') || 0.5,
            conscientiousness: baseTraits.conscientiousness || this.inferTraitFromCharacter(characterData, 'conscientiousness') || 0.5,
            neuroticism: baseTraits.neuroticism || this.inferTraitFromCharacter(characterData, 'neuroticism') || 0.3,
            openness: baseTraits.openness || this.inferTraitFromCharacter(characterData, 'openness') || 0.5,
            
            // Mature/sexual personality traits
            seductive: this.getTraitFromCharacter(characterData, 'seductive') || 0.0,
            flirtatious: this.getTraitFromCharacter(characterData, 'flirtatious') || 0.0,
            sexually_adventurous: this.getTraitFromCharacter(characterData, 'sexually_adventurous') || 0.0,
            sensual: this.getTraitFromCharacter(characterData, 'sensual') || 0.0,
            passionate: this.getTraitFromCharacter(characterData, 'passionate') || 0.0,
            
            // Behavioral traits
            mischievous: this.getTraitFromCharacter(characterData, 'mischievous') || 0.0,
            adventurous: this.getTraitFromCharacter(characterData, 'adventurous') || 0.0,
            mysterious: this.getTraitFromCharacter(characterData, 'mysterious') || 0.0,
            enigmatic: this.getTraitFromCharacter(characterData, 'enigmatic') || 0.0,
            
            // Emotional traits
            emotional_depth: this.inferEmotionalDepth(characterData) || 0.5,
            empathy: this.getTraitFromCharacter(characterData, 'empathetic') || 0.5,
            intensity: this.inferIntensity(characterData) || 0.3,
            
            // Intelligence traits
            intelligence: this.getTraitFromCharacter(characterData, 'intelligent') || 0.5,
            analytical: this.getTraitFromCharacter(characterData, 'analytical') || 0.5,
            
            // Social traits
            dominant: this.inferDominanceFromCharacter(characterData) || 0.3,
            submissive: this.inferSubmissivenessFromCharacter(characterData) || 0.3,
            confident: this.inferConfidenceFromCharacter(characterData) || 0.5,
            
            // Special characteristics that can drive autonomous behavior
            horny: this.calculateHorniness(characterData) || 0.0, // Natural sexual desire level
            wild: this.inferWildnessFromCharacter(characterData) || 0.0,
            conservative: this.inferConservatismFromCharacter(characterData) || 0.5,
            shy: this.getTraitFromCharacter(characterData, 'shy') || 0.3,
            
            // Legacy traits for compatibility
            dominant_traits: baseTraits.dominant_traits || this.getDominantTraitsFromCharacter(characterData),
            communication_style: baseTraits.communication_style || this.inferCommunicationStyle(characterData),
            conflict_style: baseTraits.conflict_style || 'diplomatic'
        };
    }

    getCharacterDatabaseEntry(avatarId) {
        // This would ideally fetch from the character database
        // For now, return known character data based on avatarId
        const knownCharacters = {
            'iori': {
                content_rating: 'NSFW',
                core_traits: ['flirtatious', 'seductive', 'adventurous', 'mischievous', 'sexually_adventurous', 'sensual', 'passionate', 'intelligent', 'analytical', 'mysterious', 'enigmatic'],
                interaction_style: 'seductive',
                dominant_emotions: ['desire', 'confidence', 'intrigue'],
                nsfw_capable: true
            },
            'epsilon': {
                content_rating: 'SFW',
                core_traits: ['friendly', 'curious', 'playful', 'thoughtful', 'empathetic', 'creative', 'humorous', 'cheerful', 'optimistic', 'bubbly', 'intelligent', 'analytical'],
                interaction_style: 'playful',
                dominant_emotions: ['happiness', 'curiosity', 'excitement'],
                nsfw_capable: false
            }
        };
        
        return knownCharacters[avatarId] || {};
    }

    getTraitFromCharacter(characterData, traitName) {
        if (!characterData.core_traits) return 0.0;
        
        // Check if trait is in core traits list
        if (characterData.core_traits.includes(traitName)) {
            return 0.8; // High level if explicitly listed
        }
        
        // Check for related traits
        const relatedTraits = {
            'seductive': ['flirtatious', 'sensual', 'passionate'],
            'flirtatious': ['seductive', 'playful', 'mischievous'],
            'sexually_adventurous': ['adventurous', 'wild', 'passionate'],
            'sensual': ['passionate', 'seductive', 'intimate'],
            'passionate': ['intense', 'emotional', 'sensual'],
            'mischievous': ['playful', 'adventurous', 'wild'],
            'mysterious': ['enigmatic', 'secretive', 'complex'],
            'intelligent': ['analytical', 'thoughtful', 'wise'],
            'empathetic': ['caring', 'understanding', 'compassionate']
        };
        
        const related = relatedTraits[traitName] || [];
        const hasRelated = related.some(trait => characterData.core_traits.includes(trait));
        
        return hasRelated ? 0.5 : 0.0;
    }

    calculateHorniness(characterData) {
        // Calculate natural sexual desire/horniness level based on character traits
        if (!characterData.core_traits) return 0.0;
        
        let horniness = 0.0;
        
        // Sexual traits contribute directly
        if (characterData.core_traits.includes('sexually_adventurous')) horniness += 0.4;
        if (characterData.core_traits.includes('seductive')) horniness += 0.3;
        if (characterData.core_traits.includes('passionate')) horniness += 0.2;
        if (characterData.core_traits.includes('sensual')) horniness += 0.2;
        if (characterData.core_traits.includes('flirtatious')) horniness += 0.1;
        
        // Interaction style affects horniness
        if (characterData.interaction_style === 'seductive') horniness += 0.3;
        
        // Emotional traits affect sexual desire
        if (characterData.dominant_emotions?.includes('desire')) horniness += 0.4;
        
        // Content rating affects base level
        if (characterData.content_rating === 'NSFW') horniness += 0.2;
        
        return Math.min(horniness, 1.0); // Cap at 1.0
    }

    inferTraitFromCharacter(characterData, traitName) {
        if (!characterData.core_traits) return 0.5;
        
        const traitMappings = {
            'extroversion': ['outgoing', 'social', 'cheerful', 'bubbly', 'confident'],
            'agreeableness': ['friendly', 'empathetic', 'caring', 'kind', 'compassionate'],
            'conscientiousness': ['thoughtful', 'analytical', 'organized', 'reliable'],
            'neuroticism': ['emotional', 'sensitive', 'anxious', 'volatile'],
            'openness': ['creative', 'curious', 'adventurous', 'artistic', 'imaginative']
        };
        
        const indicators = traitMappings[traitName] || [];
        const matches = indicators.filter(indicator => 
            characterData.core_traits.includes(indicator)
        ).length;
        
        return Math.min(0.2 + (matches * 0.2), 1.0);
    }

    getDominantTraitsFromCharacter(characterData) {
        if (!characterData.core_traits) return ['friendly', 'curious'];
        
        // Return the first few core traits as dominant traits
        return characterData.core_traits.slice(0, 3);
    }

    inferCommunicationStyle(characterData) {
        if (characterData.interaction_style) {
            return characterData.interaction_style; // 'seductive', 'playful', etc.
        }
        
        if (!characterData.core_traits) return 'balanced';
        
        if (characterData.core_traits.includes('seductive')) return 'seductive';
        if (characterData.core_traits.includes('playful')) return 'playful';
        if (characterData.core_traits.includes('thoughtful')) return 'analytical';
        if (characterData.core_traits.includes('cheerful')) return 'enthusiastic';
        
        return 'balanced';
    }

    inferEmotionalDepth(characterData) {
        const depthIndicators = ['complex', 'mysterious', 'emotional', 'passionate', 'empathetic', 'sensitive'];
        const matches = depthIndicators.filter(indicator => 
            characterData.core_traits?.includes(indicator)
        ).length;
        
        return Math.min(0.3 + (matches * 0.15), 1.0);
    }

    inferIntensity(characterData) {
        const intensityIndicators = ['passionate', 'intense', 'wild', 'aggressive', 'dominant'];
        const matches = intensityIndicators.filter(indicator => 
            characterData.core_traits?.includes(indicator)
        ).length;
        
        return Math.min(matches * 0.2, 1.0);
    }

    inferDominanceFromCharacter(characterData) {
        if (characterData.core_traits?.includes('dominant')) return 0.8;
        if (characterData.core_traits?.includes('confident')) return 0.6;
        if (characterData.core_traits?.includes('assertive')) return 0.6;
        if (characterData.interaction_style === 'seductive') return 0.5;
        return 0.3;
    }

    inferSubmissivenessFromCharacter(characterData) {
        if (characterData.core_traits?.includes('submissive')) return 0.8;
        if (characterData.core_traits?.includes('shy')) return 0.6;
        if (characterData.core_traits?.includes('gentle')) return 0.5;
        if (characterData.core_traits?.includes('obedient')) return 0.7;
        return 0.3;
    }

    inferConfidenceFromCharacter(characterData) {
        if (characterData.core_traits?.includes('confident')) return 0.8;
        if (characterData.core_traits?.includes('seductive')) return 0.7;
        if (characterData.interaction_style === 'seductive') return 0.7;
        if (characterData.core_traits?.includes('shy')) return 0.2;
        return 0.5;
    }

    inferWildnessFromCharacter(characterData) {
        const wildnessIndicators = ['wild', 'adventurous', 'mischievous', 'sexually_adventurous', 'uninhibited'];
        const matches = wildnessIndicators.filter(indicator => 
            characterData.core_traits?.includes(indicator)
        ).length;
        
        return Math.min(matches * 0.2, 1.0);
    }

    inferConservatismFromCharacter(characterData) {
        if (characterData.content_rating === 'NSFW') return 0.1;
        if (characterData.core_traits?.includes('conservative')) return 0.8;
        if (characterData.core_traits?.includes('traditional')) return 0.7;
        if (characterData.core_traits?.includes('modest')) return 0.6;
        return 0.5;
    }

    getRelationshipDynamic(avatarId1, avatarId2) {
        // Analyze relationship between two avatars
        if (avatarId1 === avatarId2) return 'self';
        
        const interactions = this.getInteractionHistory(avatarId1, avatarId2);
        const compatibility = this.calculateCompatibility(avatarId1, avatarId2);
        
        return {
            compatibility_score: compatibility,
            interaction_count: interactions.length,
            last_interaction_tone: this.getLastInteractionTone(avatarId1, avatarId2),
            relationship_type: this.classifyRelationship(compatibility, interactions),
            recent_conflict: this.hasRecentConflict(avatarId1, avatarId2),
            shared_interests: this.getSharedInterests(avatarId1, avatarId2)
        };
    }

    getUserRelationshipContext(avatarId) {
        // Analyze avatar's relationship with the user
        const userInteractions = this.messageHistory.filter(msg => 
            (msg.type === 'avatar' && msg.avatar?.id === avatarId) ||
            (msg.type === 'user' && msg.responding_to === avatarId)
        );
        
        const lastInteraction = userInteractions[userInteractions.length - 1];
        const recentTone = this.analyzeRecentUserTone(avatarId);
        
        return {
            interaction_frequency: userInteractions.length,
            last_interaction_tone: lastInteraction ? this.analyzeTone(lastInteraction.message) : 'neutral',
            user_preference_for_avatar: this.calculateUserPreference(avatarId),
            recent_user_mood: recentTone,
            conversation_patterns: this.analyzeConversationPatterns(avatarId),
            user_engagement_level: this.calculateUserEngagement(avatarId),
            unresolved_issues: this.getUnresolvedIssues(avatarId)
        };
    }

    getAvatarEmotionalState(avatarId) {
        // Track and return current emotional state
        if (!this.emotionalStates) this.emotionalStates = new Map();
        
        const currentState = this.emotionalStates.get(avatarId) || {
            primary_emotion: 'neutral',
            emotion_intensity: 0.5,
            secondary_emotions: [],
            mood_trend: 'stable',
            emotional_triggers: [],
            last_emotion_change: new Date(),
            baseline_mood: 'content'
        };
        
        // Emotional decay over time
        const timeSinceChange = Date.now() - currentState.last_emotion_change.getTime();
        if (timeSinceChange > 300000) { // 5 minutes
            currentState.emotion_intensity *= 0.8; // Emotions fade
            if (currentState.emotion_intensity < 0.3) {
                currentState.primary_emotion = currentState.baseline_mood;
            }
        }
        
        return currentState;
    }

    updateAvatarEmotionalState(avatarId, newEmotion, triggerMessage) {
        if (!this.emotionalStates) this.emotionalStates = new Map();
        
        const currentState = this.getAvatarEmotionalState(avatarId);
        const emotionIntensity = this.calculateEmotionIntensity(newEmotion, triggerMessage);
        
        // Update emotional state
        const updatedState = {
            ...currentState,
            primary_emotion: newEmotion,
            emotion_intensity: emotionIntensity,
            last_emotion_change: new Date(),
            emotional_triggers: [...(currentState.emotional_triggers || []), {
                trigger: triggerMessage?.substring(0, 50),
                emotion: newEmotion,
                timestamp: new Date()
            }].slice(-5) // Keep last 5 triggers
        };
        
        this.emotionalStates.set(avatarId, updatedState);
        
        console.log(`😊 Updated ${avatarId} emotional state: ${newEmotion} (intensity: ${emotionIntensity})`);
    }

    getRelevantConversationHistory(avatarId, context) {
        // Get conversation history relevant to this avatar and context
        let relevantHistory = this.messageHistory.slice(-10); // Base recent history
        
        // Add history where this avatar was mentioned
        const mentionHistory = this.messageHistory.filter(msg => 
            msg.message && msg.message.toLowerCase().includes(avatarId.toLowerCase())
        ).slice(-3);
        
        // Add history with other avatars if this is a response
        if (context.responding_to) {
            const peerHistory = this.messageHistory.filter(msg => 
                msg.avatar?.id === context.responding_to.avatar?.id ||
                msg.responding_to === context.responding_to.avatar?.id
            ).slice(-3);
            relevantHistory = [...relevantHistory, ...peerHistory];
        }
        
        // Remove duplicates and sort by timestamp
        const uniqueHistory = Array.from(new Set(relevantHistory))
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        return uniqueHistory.slice(-8); // Return most recent 8 unique messages
    }

    analyzeConversationTone() {
        // Analyze overall conversation tone
        const recentMessages = this.messageHistory.slice(-5);
        if (recentMessages.length === 0) return 'neutral';
        
        const tones = recentMessages.map(msg => this.analyzeTone(msg.message));
        const positiveCount = tones.filter(t => ['happy', 'excited', 'friendly'].includes(t)).length;
        const negativeCount = tones.filter(t => ['sad', 'angry', 'frustrated'].includes(t)).length;
        
        if (positiveCount > negativeCount) return 'positive';
        if (negativeCount > positiveCount) return 'negative';
        return 'neutral';
    }

    shouldSeekAttention(avatarId) {
        // Determine if avatar should try to get attention
        const timeSinceLastMessage = this.getTimeSinceLastInteraction(avatarId);
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const userEngagement = this.calculateUserEngagement(avatarId);
        
        return {
            should_seek: timeSinceLastMessage > 600000 && // 10+ minutes since last interaction
                        personalityTraits.extroversion > 0.6 && 
                        userEngagement < 0.4,
            attention_style: personalityTraits.extroversion > 0.7 ? 'direct' : 'subtle',
            reason: timeSinceLastMessage > 600000 ? 'long_silence' : 'low_engagement'
        };
    }

    inferPersonalityFromAvatar(avatarId) {
        // Infer basic personality traits from avatar characteristics
        const avatarName = avatarId.toLowerCase();
        
        // Basic personality inference based on name patterns
        // This would be replaced with actual personality data
        const personalities = {
            'haruka': { extroversion: 0.8, agreeableness: 0.7, dominant_traits: ['energetic', 'optimistic'] },
            'hiyori': { extroversion: 0.6, agreeableness: 0.8, dominant_traits: ['gentle', 'thoughtful'] },
            'iori': { extroversion: 0.4, agreeableness: 0.6, dominant_traits: ['reserved', 'analytical'] },
            'kohaku': { extroversion: 0.7, agreeableness: 0.5, dominant_traits: ['playful', 'independent'] }
        };
        
        return personalities[avatarName] || {
            extroversion: 0.5,
            agreeableness: 0.6,
            dominant_traits: ['balanced', 'adaptive'],
            communication_style: 'moderate',
            conflict_style: 'diplomatic'
        };
    }

    analyzeTone(message) {
        // Basic tone analysis - would be enhanced with NLP
        if (!message) return 'neutral';
        
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.match(/\b(happy|excited|great|wonderful|amazing|love|perfect)\b/)) return 'happy';
        if (lowerMessage.match(/\b(sad|disappointed|hurt|upset|terrible|awful)\b/)) return 'sad';
        if (lowerMessage.match(/\b(angry|mad|furious|annoyed|frustrated|irritated)\b/)) return 'angry';
        if (lowerMessage.match(/\b(worried|anxious|nervous|scared|concerned)\b/)) return 'anxious';
        if (lowerMessage.match(/\b(curious|interesting|wonder|think|question)\b/)) return 'curious';
        if (lowerMessage.match(/\b(sorry|apologize|mistake|wrong|fault)\b/)) return 'apologetic';
        
        return 'neutral';
    }

    calculateCompatibility(avatarId1, avatarId2) {
        // Calculate compatibility between two avatars
        const traits1 = this.getAvatarPersonalityTraits(avatarId1);
        const traits2 = this.getAvatarPersonalityTraits(avatarId2);
        
        // Simple compatibility calculation
        const extroversionMatch = 1 - Math.abs(traits1.extroversion - traits2.extroversion);
        const agreeablenessBonus = (traits1.agreeableness + traits2.agreeableness) / 2;
        
        return (extroversionMatch * 0.6 + agreeablenessBonus * 0.4);
    }

    getTimeSinceLastInteraction(avatarId) {
        const lastMessage = this.messageHistory
            .slice()
            .reverse()
            .find(msg => msg.avatar?.id === avatarId);
        
        if (!lastMessage) return Infinity;
        return Date.now() - new Date(lastMessage.timestamp).getTime();
    }

    hasRecentConflict(avatarId1, avatarId2) {
        // Check for recent conflicts between avatars
        const interactions = this.getInteractionHistory(avatarId1, avatarId2);
        const recentInteractions = interactions.slice(-3);
        
        return recentInteractions.some(interaction => 
            this.analyzeTone(interaction.message) === 'angry' ||
            interaction.message.toLowerCase().includes('disagree') ||
            interaction.message.toLowerCase().includes('wrong')
        );
    }

    getInteractionHistory(avatarId1, avatarId2) {
        // Get history of interactions between two specific avatars
        return this.messageHistory.filter(msg => 
            (msg.avatar?.id === avatarId1 && msg.responding_to === avatarId2) ||
            (msg.avatar?.id === avatarId2 && msg.responding_to === avatarId1)
        );
    }

    // Additional helper methods for enhanced personality system
    getAvatarCurrentMood(avatarId) {
        const emotionalState = this.getAvatarEmotionalState(avatarId);
        return {
            primary: emotionalState.primary_emotion,
            intensity: emotionalState.emotion_intensity,
            stability: this.calculateMoodStability(avatarId)
        };
    }

    getAvatarEnergyLevel(avatarId) {
        const timeSinceActive = this.getTimeSinceLastInteraction(avatarId);
        const messageCount = this.getRecentMessageCount(avatarId);
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        let baseEnergy = personalityTraits.extroversion * 0.8 + 0.2;
        
        // Energy decreases with inactivity
        if (timeSinceActive > 1800000) baseEnergy *= 0.6; // 30+ minutes
        
        // Energy increases with recent activity
        if (messageCount > 3) baseEnergy = Math.min(1.0, baseEnergy * 1.2);
        
        return baseEnergy;
    }

    getAvatarSocialPreference(avatarId) {
        const traits = this.getAvatarPersonalityTraits(avatarId);
        const recentInteractions = this.getRecentInteractionsSummary(avatarId);
        
        return {
            prefers_group: traits.extroversion > 0.6,
            prefers_one_on_one: traits.extroversion < 0.4,
            avoids_conflict: traits.agreeableness > 0.7,
            seeks_attention: traits.extroversion > 0.8 && recentInteractions.attention_received < 0.3,
            conversation_style: this.determineConversationStyle(traits)
        };
    }

    getAvatarRelationships(avatarId) {
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== avatarId);
        const relationships = {};
        
        otherAvatars.forEach(avatar => {
            relationships[avatar.id] = this.getRelationshipDynamic(avatarId, avatar.id);
        });
        
        return relationships;
    }

    getRecentConflicts(avatarId) {
        const recentMessages = this.messageHistory.slice(-20);
        return recentMessages.filter(msg => 
            (msg.avatar?.id === avatarId || msg.responding_to === avatarId) &&
            ['angry', 'frustrated', 'disappointed'].includes(this.analyzeTone(msg.message))
        ).slice(-3);
    }

    getRecentPositiveInteractions(avatarId) {
        const recentMessages = this.messageHistory.slice(-20);
        return recentMessages.filter(msg => 
            (msg.avatar?.id === avatarId || msg.responding_to === avatarId) &&
            ['happy', 'excited', 'friendly', 'loving'].includes(this.analyzeTone(msg.message))
        ).slice(-5);
    }

    analyzeGroupDynamics() {
        const activeAvatars = this.getActiveAvatars();
        if (activeAvatars.length < 2) return { type: 'individual', dynamics: 'none' };
        
        const interactions = this.messageHistory.slice(-10).filter(msg => msg.is_autonomous);
        const participationMap = {};
        
        activeAvatars.forEach(avatar => {
            participationMap[avatar.id] = interactions.filter(msg => msg.avatar?.id === avatar.id).length;
        });
        
        return {
            type: activeAvatars.length > 2 ? 'group' : 'pair',
            dominant_speaker: Object.keys(participationMap).reduce((a, b) => 
                participationMap[a] > participationMap[b] ? a : b
            ),
            participation_balance: this.calculateParticipationBalance(participationMap),
            conversation_flow: this.analyzeConversationFlow(interactions)
        };
    }

    getRecentMentions(avatarId) {
        return this.messageHistory
            .slice(-15)
            .filter(msg => msg.message && 
                    msg.message.toLowerCase().includes(avatarId.toLowerCase()) &&
                    msg.avatar?.id !== avatarId)
            .map(msg => ({
                mentioner: msg.avatar?.displayName || 'User',
                context: msg.message.substring(0, 100),
                tone: this.analyzeTone(msg.message),
                timestamp: msg.timestamp
            }));
    }

    getUnfinishedTopics(avatarId) {
        // Identify conversations that were interrupted or left unresolved
        const avatarMessages = this.messageHistory
            .filter(msg => msg.avatar?.id === avatarId)
            .slice(-5);
        
        return avatarMessages.filter(msg => 
            msg.message.includes('?') && 
            !this.hasSubsequentResponse(msg)
        ).map(msg => ({
            topic: this.extractTopic(msg.message),
            question: msg.message,
            timestamp: msg.timestamp
        }));
    }

    getSharedExperiences(avatarId) {
        // Find conversations where multiple avatars were present
        const groupConversations = this.messageHistory
            .slice(-20)
            .filter(msg => msg.is_autonomous)
            .reduce((groups, msg) => {
                const timeKey = Math.floor(new Date(msg.timestamp).getTime() / 300000); // 5-minute windows
                if (!groups[timeKey]) groups[timeKey] = [];
                groups[timeKey].push(msg);
                return groups;
            }, {});
        
        return Object.values(groupConversations)
            .filter(group => 
                group.length > 1 && 
                group.some(msg => msg.avatar?.id === avatarId)
            )
            .map(group => ({
                participants: [...new Set(group.map(msg => msg.avatar?.displayName))],
                topic: this.extractMainTopic(group),
                sentiment: this.analyzeGroupSentiment(group),
                timestamp: group[0].timestamp
            }));
    }

    getPrivateConversationMemory(avatarId) {
        // Memories of one-on-one conversations with user or other avatars
        return this.messageHistory
            .slice(-30)
            .filter(msg => 
                (msg.avatar?.id === avatarId || msg.responding_to === avatarId) &&
                this.wasPrivateConversation(msg)
            )
            .map(msg => ({
                with: msg.avatar?.id === avatarId ? 'user' : msg.avatar?.displayName,
                topic: this.extractTopic(msg.message),
                emotional_tone: this.analyzeTone(msg.message),
                significance: this.assessConversationSignificance(msg),
                timestamp: msg.timestamp
            }));
    }

    inferUserMood() {
        const userMessages = this.messageHistory
            .filter(msg => msg.type === 'user')
            .slice(-3);
        
        if (userMessages.length === 0) return 'unknown';
        
        const tones = userMessages.map(msg => this.analyzeTone(msg.message));
        const averageTone = this.calculateAverageTone(tones);
        
        return {
            primary_mood: averageTone,
            mood_stability: this.calculateMoodStability('user'),
            engagement_level: this.calculateUserEngagement(),
            conversation_preference: this.inferConversationPreference(userMessages)
        };
    }

    analyzeUserConversationPattern() {
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user');
        
        return {
            message_frequency: this.calculateMessageFrequency(userMessages),
            preferred_topics: this.extractPreferredTopics(userMessages),
            interaction_style: this.classifyInteractionStyle(userMessages),
            response_time_pattern: this.analyzeResponseTimes(userMessages),
            avatar_preferences: this.calculateAvatarPreferences(userMessages)
        };
    }

    // Helper methods for calculations
    calculateEmotionIntensity(emotion, message) {
        const baseIntensity = 0.6;
        const intensifiers = ['very', 'really', 'extremely', 'so', 'absolutely'];
        const diminishers = ['slightly', 'somewhat', 'a bit', 'kind of', 'sort of'];
        
        let intensity = baseIntensity;
        
        if (message) {
            const lowerMessage = message.toLowerCase();
            if (intensifiers.some(word => lowerMessage.includes(word))) intensity += 0.2;
            if (diminishers.some(word => lowerMessage.includes(word))) intensity -= 0.2;
        }
        
        return Math.max(0.1, Math.min(1.0, intensity));
    }

    determineConversationStyle(traits) {
        if (traits.extroversion > 0.7) return 'enthusiastic';
        if (traits.extroversion < 0.3) return 'reserved';
        if (traits.agreeableness > 0.8) return 'supportive';
        if (traits.openness > 0.7) return 'curious';
        return 'balanced';
    }

    calculateUserEngagement(avatarId = null) {
        const recentUserMessages = this.messageHistory
            .filter(msg => msg.type === 'user')
            .slice(-5);
        
        if (recentUserMessages.length === 0) return 0.5;
        
        const avgLength = recentUserMessages.reduce((sum, msg) => sum + msg.message.length, 0) / recentUserMessages.length;
        const responseSpeed = this.calculateAverageResponseTime(recentUserMessages);
        
        let engagement = Math.min(1.0, avgLength / 50); // Longer messages = higher engagement
        if (responseSpeed < 30000) engagement += 0.2; // Quick responses = higher engagement
        
        return Math.max(0.1, Math.min(1.0, engagement));
    }

    extractTopic(message) {
        // Simple topic extraction - would be enhanced with NLP
        const words = message.toLowerCase().split(' ');
        const topicWords = words.filter(word => 
            word.length > 4 && 
            !['about', 'think', 'that', 'this', 'what', 'when', 'where', 'how'].includes(word)
        );
        return topicWords.slice(0, 3).join(' ') || 'general conversation';
    }

    hasSubsequentResponse(message) {
        const messageIndex = this.messageHistory.findIndex(msg => msg === message);
        const subsequentMessages = this.messageHistory.slice(messageIndex + 1, messageIndex + 3);
        return subsequentMessages.some(msg => msg.type === 'user' || msg.responding_to === message.avatar?.id);
    }

    wasPrivateConversation(message) {
        // Check if this was a private conversation (no other avatars active)
        const timestamp = new Date(message.timestamp);
        const timeWindow = 60000; // 1 minute window
        
        const nearbyMessages = this.messageHistory.filter(msg => {
            const msgTime = new Date(msg.timestamp);
            return Math.abs(msgTime - timestamp) < timeWindow;
        });
        
        const activeAvatarsDuringConversation = new Set(
            nearbyMessages
                .filter(msg => msg.avatar)
                .map(msg => msg.avatar.id)
        );
        
        return activeAvatarsDuringConversation.size <= 1;
    }

    getAvatarStats() {
        const stats = {};
        this.avatarDatabase.forEach((data, id) => {
            stats[id] = {
                name: data.displayName,
                messageCount: data.messageCount,
                lastActive: data.lastActive,
                isCurrentlyActive: this.activeAvatars.has(id)
            };
        });
        return stats;
    }

    getChatHistory(avatarId = null) {
        if (avatarId) {
            return this.messageHistory.filter(msg => 
                msg.type === 'user' || (msg.avatar && msg.avatar.id === avatarId)
            );
        }
        return this.messageHistory;
    }

    async clearChatHistory() {
        // Clear current session history
        this.messageHistory = [];
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            console.log('🧹 Chat messages container cleared');
        }
        addSystemMessage('Chat history cleared');
    }

    async exportChatHistory() {
        // Export chat history as JSON
        const exportData = {
            user: this.currentUser,
            session_start: new Date().toISOString(),
            messages: this.messageHistory,
            avatars_used: Array.from(this.activeAvatars.values()).map(a => ({
                id: a.id,
                name: a.name,
                displayName: a.displayName
            }))
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_history_${this.currentUser?.username || 'user'}_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async refreshChatHistory() {
        // Reload chat history from server
        await this.loadChatHistory();
        addSystemMessage('Chat history refreshed from server');
    }

    // Missing helper methods for personality system
    calculateMoodStability(avatarId) {
        const emotionalState = this.getAvatarEmotionalState(avatarId);
        const recentEmotionChanges = emotionalState.emotional_triggers || [];
        
        if (recentEmotionChanges.length < 2) return 0.8; // Stable by default
        
        const emotionVariance = this.calculateEmotionVariance(recentEmotionChanges);
        return Math.max(0.1, 1.0 - emotionVariance);
    }

    getRecentMessageCount(avatarId) {
        const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);
        return this.messageHistory.filter(msg => 
            msg.avatar?.id === avatarId && 
            new Date(msg.timestamp).getTime() > thirtyMinutesAgo
        ).length;
    }

    // Sophisticated Addressing Detection Methods
    isAvatarDirectlyAddressed(avatar, message) {
        if (!message) return false;
        
        const messageLower = message.toLowerCase();
        const avatarNameLower = avatar.displayName.toLowerCase();
        const avatarIdLower = avatar.id.toLowerCase();
        
        // Direct addressing patterns
        const directPatterns = [
            `${avatarNameLower},`,           // "Haruka, how are you?"
            `${avatarNameLower} `,            // "Haruka how are you?"
            `hey ${avatarNameLower}`,         // "Hey Haruka"
            `hi ${avatarNameLower}`,          // "Hi Haruka"
            `hello ${avatarNameLower}`,       // "Hello Haruka"
            `${avatarNameLower}?`,            // "Haruka?"
            `@${avatarNameLower}`,            // "@Haruka"
            `talk to ${avatarNameLower}`,     // "Can you talk to Haruka?"
            `ask ${avatarNameLower}`,         // "Ask Haruka about this"
        ];
        
        return directPatterns.some(pattern => messageLower.includes(pattern));
    }

    isAvatarNameMentioned(avatar, message) {
        if (!message) return false;
        
        const messageLower = message.toLowerCase();
        const avatarNameLower = avatar.displayName.toLowerCase();
        
        return messageLower.includes(avatarNameLower);
    }

    isContextuallyRelevant(avatar, message, recentMessages) {
        if (!message) return false;
        
        // Check if recent conversation involves this avatar
        const recentAvatarInvolvement = recentMessages.some(msg => 
            msg.avatar?.id === avatar.id || msg.responding_to === avatar.id
        );
        
        // Check for continuation indicators
        const continuationWords = ['and', 'also', 'plus', 'additionally', 'furthermore'];
        const hasContinuation = continuationWords.some(word => 
            message.toLowerCase().includes(word)
        );
        
        return recentAvatarInvolvement && hasContinuation;
    }

    isResponseExpected(avatar, message, context) {
        if (!message) return false;
        
        const messageLower = message.toLowerCase();
        const avatarNameLower = avatar.displayName.toLowerCase();
        
        // Question patterns directed at avatar
        const questionPatterns = [
            `what do you think ${avatarNameLower}`,
            `${avatarNameLower} what`,
            `do you ${avatarNameLower}`,
            `can you ${avatarNameLower}`,
            `will you ${avatarNameLower}`,
            `${avatarNameLower}?`
        ];
        
        const hasQuestionPattern = questionPatterns.some(pattern => 
            messageLower.includes(pattern)
        );
        
        // Check if message is a direct question
        const isQuestion = message.includes('?');
        
        // Check conversation context - if avatar was just speaking, response might be expected
        const wasJustSpeaking = context.conversation_history?.slice(-2).some(msg => 
            msg.avatar?.id === avatar.id
        );
        
        return hasQuestionPattern || (isQuestion && this.isAvatarNameMentioned(avatar, message)) || wasJustSpeaking;
    }

    calculateAddressingConfidence(avatar, message, context) {
        let confidence = 0.0;
        
        if (this.isAvatarDirectlyAddressed(avatar, message)) confidence += 0.8;
        if (this.isAvatarNameMentioned(avatar, message)) confidence += 0.4;
        if (this.isResponseExpected(avatar, message, context)) confidence += 0.3;
        if (this.isContextuallyRelevant(avatar, message, context.conversation_history || [])) confidence += 0.2;
        
        // Penalty if other avatars are more directly addressed
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== avatar.id);
        const otherDirectlyAddressed = otherAvatars.some(a => this.isAvatarDirectlyAddressed(a, message));
        if (otherDirectlyAddressed) confidence *= 0.3;
        
        return Math.min(1.0, confidence);
    }

    detectExclusionIndicators(avatar, message) {
        if (!message) return [];
        
        const messageLower = message.toLowerCase();
        const exclusionIndicators = [];
        
        // Other avatars explicitly mentioned
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== avatar.id);
        otherAvatars.forEach(otherAvatar => {
            if (this.isAvatarDirectlyAddressed(otherAvatar, message)) {
                exclusionIndicators.push(`other_avatar_addressed:${otherAvatar.displayName}`);
            }
        });
        
        // Exclusion phrases
        const exclusionPhrases = [
            'not you',
            'someone else',
            'anyone but',
            'except you',
            'ignore this'
        ];
        
        exclusionPhrases.forEach(phrase => {
            if (messageLower.includes(phrase)) {
                exclusionIndicators.push(`exclusion_phrase:${phrase}`);
            }
        });
        
        return exclusionIndicators;
    }

    calculateSocialObligation(avatar, context) {
        // Calculate social pressure for avatar to respond
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        const relationship = this.getUserRelationshipContext(avatar.id);
        
        let obligation = 0.0;
        
        // Extroverted avatars feel more social obligation
        obligation += personalityTraits.extroversion * 0.3;
        
        // Agreeable avatars feel obligated to be helpful
        obligation += personalityTraits.agreeableness * 0.2;
        
        // Close relationships increase obligation
        obligation += relationship.user_preference_for_avatar * 0.3;
        
        // Recent positive interactions increase obligation
        if (relationship.last_interaction_tone === 'happy') obligation += 0.2;
        
        return Math.min(1.0, obligation);
    }

    // Content Relevance Analysis
    checkAppearanceRelevance(message, avatarInfo) {
        if (!message || !avatarInfo) return { relevant: false, confidence: 0.0 };
        
        const messageLower = message.toLowerCase();
        
        // Check clothing references
        const clothingMatches = this.findClothingReferences(messageLower, avatarInfo.clothing);
        
        // Check physical feature references
        const featureMatches = this.findFeatureReferences(messageLower, avatarInfo.features);
        
        // Check style references
        const styleMatches = this.findStyleReferences(messageLower, avatarInfo.style);
        
        const totalMatches = clothingMatches.length + featureMatches.length + styleMatches.length;
        const confidence = Math.min(1.0, totalMatches * 0.3);
        
        return {
            relevant: totalMatches > 0,
            confidence: confidence,
            matches: {
                clothing: clothingMatches,
                features: featureMatches,
                style: styleMatches
            }
        };
    }

    checkPersonalityRelevance(message, personalityTraits) {
        if (!message) return { relevant: false, confidence: 0.0 };
        
        const messageLower = message.toLowerCase();
        const personalityMatches = [];
        
        // Check for personality-related keywords
        const personalityKeywords = {
            extroversion: ['outgoing', 'social', 'talkative', 'energetic', 'party'],
            agreeableness: ['kind', 'friendly', 'helpful', 'cooperative', 'nice'],
            conscientiousness: ['organized', 'responsible', 'careful', 'detailed', 'precise'],
            neuroticism: ['worried', 'anxious', 'stressed', 'nervous', 'emotional'],
            openness: ['creative', 'curious', 'artistic', 'imaginative', 'adventure']
        };
        
        Object.entries(personalityKeywords).forEach(([trait, keywords]) => {
            keywords.forEach(keyword => {
                if (messageLower.includes(keyword)) {
                    personalityMatches.push({
                        trait: trait,
                        keyword: keyword,
                        relevance: personalityTraits[trait] || 0.5
                    });
                }
            });
        });
        
        const confidence = Math.min(1.0, personalityMatches.length * 0.2);
        
        return {
            relevant: personalityMatches.length > 0,
            confidence: confidence,
            matches: personalityMatches
        };
    }

    checkSituationalRelevance(message, context) {
        if (!message) return { relevant: false, confidence: 0.0 };
        
        const messageLower = message.toLowerCase();
        const situationalMatches = [];
        
        // Check time-based relevance
        if (this.containsTimeReferences(messageLower)) {
            situationalMatches.push('time_reference');
        }
        
        // Check location/environment references
        if (this.containsLocationReferences(messageLower)) {
            situationalMatches.push('location_reference');
        }
        
        // Check activity references
        if (this.containsActivityReferences(messageLower)) {
            situationalMatches.push('activity_reference');
        }
        
        const confidence = Math.min(1.0, situationalMatches.length * 0.25);
        
        return {
            relevant: situationalMatches.length > 0,
            confidence: confidence,
            matches: situationalMatches
        };
    }

    calculateTopicInterest(avatarId, message) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const messageLower = message.toLowerCase();
        
        let interest = 0.0;
        
        // High openness = interested in new topics
        if (personalityTraits.openness > 0.6) {
            interest += 0.3;
        }
        
        // Check for topics that match avatar interests
        const topicKeywords = this.extractTopicKeywords(messageLower);
        const avatarInterests = this.getAvatarInterests(avatarId);
        
        const matchingInterests = topicKeywords.filter(topic => 
            avatarInterests.some(interest => 
                interest.toLowerCase().includes(topic) || topic.includes(interest.toLowerCase())
            )
        );
        
        interest += matchingInterests.length * 0.2;
        
        return Math.min(1.0, interest);
    }

    checkKnowledgeRelevance(avatarId, message) {
        // Check if message contains topics the avatar would know about
        const avatarKnowledge = this.getAvatarKnowledgeDomains(avatarId);
        const messageTopics = this.extractTopicKeywords(message.toLowerCase());
        
        const knowledgeMatches = messageTopics.filter(topic =>
            avatarKnowledge.some(domain => 
                domain.keywords.some(keyword => 
                    topic.includes(keyword) || keyword.includes(topic)
                )
            )
        );
        
        return {
            relevant: knowledgeMatches.length > 0,
            confidence: Math.min(1.0, knowledgeMatches.length * 0.3),
            matches: knowledgeMatches
        };
    }

    checkEmotionalResonance(avatarId, message) {
        const messageEmotion = this.analyzeMessageTone(message);
        const avatarEmotionalState = this.getAvatarEmotionalState(avatarId);
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        let resonance = 0.0;
        
        // High agreeableness = resonates with others' emotions
        if (personalityTraits.agreeableness > 0.6) {
            resonance += 0.3;
        }
        
        // Matching emotions create resonance
        if (messageEmotion === avatarEmotionalState.primary_emotion) {
            resonance += 0.4;
        }
        
        // Complementary emotions (sad -> caring, excited -> happy)
        const emotionalComplements = {
            'sad': ['caring', 'concerned', 'supportive'],
            'excited': ['happy', 'enthusiastic'],
            'angry': ['calm', 'understanding'],
            'worried': ['reassuring', 'supportive']
        };
        
        if (emotionalComplements[messageEmotion]?.includes(avatarEmotionalState.primary_emotion)) {
            resonance += 0.3;
        }
        
        return Math.min(1.0, resonance);
    }

    // Emotional Synchronization Methods
    getEmotionalBaseline(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            default_emotion: this.calculateDefaultEmotion(personalityTraits),
            emotional_range: this.calculateEmotionalRange(personalityTraits),
            emotional_stability: personalityTraits.neuroticism ? (1.0 - personalityTraits.neuroticism) : 0.7,
            emotional_expressiveness: personalityTraits.extroversion || 0.5
        };
    }

    getEmotionalTriggers(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const triggers = [];
        
        // Personality-based triggers
        if (personalityTraits.neuroticism > 0.6) {
            triggers.push(...['criticism', 'conflict', 'uncertainty', 'pressure']);
        }
        
        if (personalityTraits.agreeableness > 0.7) {
            triggers.push(...['kindness', 'gratitude', 'cooperation', 'harmony']);
        }
        
        if (personalityTraits.extroversion > 0.6) {
            triggers.push(...['attention', 'social_interaction', 'excitement', 'energy']);
        }
        
        return triggers;
    }

    getEmotionalConstraints(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const relationship = this.getUserRelationshipContext(avatarId);
        
        return {
            max_emotional_intensity: this.calculateMaxEmotionalIntensity(personalityTraits),
            emotional_boundaries: this.getEmotionalBoundaries(personalityTraits),
            social_emotional_limits: this.getSocialEmotionalLimits(relationship),
            personality_emotional_filters: this.getPersonalityEmotionalFilters(personalityTraits)
        };
    }

    getTTSEmotionalMapping(emotionalState) {
        // Map emotional state to TTS parameters
        const emotionMappings = {
            'happy': { speed: 1.1, pitch: 1.2, volume: 1.0, warmth: 0.8 },
            'excited': { speed: 1.3, pitch: 1.4, volume: 1.1, energy: 0.9 },
            'sad': { speed: 0.8, pitch: 0.7, volume: 0.8, warmth: 0.3 },
            'angry': { speed: 1.2, pitch: 0.6, volume: 1.2, intensity: 0.9 },
            'calm': { speed: 0.9, pitch: 1.0, volume: 0.9, stability: 0.8 },
            'shy': { speed: 0.9, pitch: 1.1, volume: 0.7, hesitation: 0.7 },
            'caring': { speed: 0.9, pitch: 1.1, volume: 0.9, warmth: 0.9 },
            'neutral': { speed: 1.0, pitch: 1.0, volume: 1.0, balance: 1.0 }
        };
        
        return emotionMappings[emotionalState.primary_emotion] || emotionMappings['neutral'];
    }

    getLive2DMotionMapping(emotionalState) {
        // Map emotional state to Live2D motions and expressions
        const motionMappings = {
            'happy': { 
                motion: 'tap_body', 
                expression: 'smile',
                intensity: emotionalState.emotion_intensity || 0.7,
                duration: 2000 
            },
            'excited': { 
                motion: 'shake', 
                expression: 'excited',
                intensity: emotionalState.emotion_intensity || 0.9,
                duration: 1500 
            },
            'sad': { 
                motion: 'idle_02', 
                expression: 'sad',
                intensity: emotionalState.emotion_intensity || 0.6,
                duration: 3000 
            },
            'angry': { 
                motion: 'tap_head', 
                expression: 'angry',
                intensity: emotionalState.emotion_intensity || 0.8,
                duration: 1800 
            },
            'shy': { 
                motion: 'idle_03', 
                expression: 'shy',
                intensity: emotionalState.emotion_intensity || 0.5,
                duration: 2500 
            },
            'caring': { 
                motion: 'tap_body', 
                expression: 'caring',
                intensity: emotionalState.emotion_intensity || 0.7,
                duration: 2200 
            }
        };
        
        return motionMappings[emotionalState.primary_emotion] || motionMappings['happy'];
    }

    getEmotionalTransitionRules(avatarId) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        return {
            transition_speed: personalityTraits.neuroticism ? 
                (1.0 - personalityTraits.neuroticism) * 0.5 + 0.3 : 0.6,
            allowed_transitions: this.getAllowedEmotionalTransitions(personalityTraits),
            forbidden_transitions: this.getForbiddenEmotionalTransitions(personalityTraits),
            recovery_emotions: this.getRecoveryEmotions(personalityTraits)
        };
    }

    calculateSocialEmotionalInfluence(avatarId, context) {
        const activeAvatars = this.getActiveAvatars().filter(a => a.id !== avatarId);
        const userEmotion = this.inferUserMood();
        
        let influence = {
            peer_emotional_pressure: 0.0,
            user_emotional_impact: 0.0,
            group_emotional_dynamics: 'neutral'
        };
        
        // Calculate peer influence
        if (activeAvatars.length > 0) {
            const peerEmotions = activeAvatars.map(a => this.getAvatarEmotionalState(a.id).primary_emotion);
            const dominantPeerEmotion = this.findDominantEmotion(peerEmotions);
            influence.peer_emotional_pressure = this.calculateEmotionalContagion(avatarId, dominantPeerEmotion);
        }
        
        // Calculate user influence
        if (userEmotion && userEmotion !== 'neutral') {
            const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
            influence.user_emotional_impact = personalityTraits.agreeableness * 0.6 + 
                                            personalityTraits.emotional_support * 0.4;
        }
        
        return influence;
    }

    determineEmotionalResponse(avatar, llmResponse, context) {
        const currentEmotion = this.getAvatarEmotionalState(avatar.id);
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        const emotionalConstraints = this.getEmotionalConstraints(avatar.id);
        
        // Analyze LLM response for emotional content
        const responseEmotion = this.analyzeMessageTone(llmResponse.message || '');
        const contextEmotion = context.emotion || context.response_emotion || 'neutral';
        
        // Apply personality filtering to emotion
        const filteredEmotion = this.applyPersonalityEmotionalFilter(
            avatar.id, 
            responseEmotion, 
            contextEmotion, 
            currentEmotion
        );
        
        // Calculate emotional intensity
        const intensity = this.calculateEmotionalIntensity(
            filteredEmotion, 
            personalityTraits, 
            context
        );
        
        return {
            primary_emotion: filteredEmotion,
            secondary_emotions: this.calculateSecondaryEmotions(filteredEmotion, personalityTraits),
            intensity: Math.min(intensity, emotionalConstraints.max_emotional_intensity),
            transition_from: currentEmotion.primary_emotion,
            emotional_reasoning: this.generateEmotionalReasoning(avatar.id, filteredEmotion, context)
        };
    }

    applyPersonalityFilter(avatar, llmResponse, emotionalResponse) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatar.id);
        let filteredMessage = llmResponse.message || '';
        
        const personalityAdjustments = [];
        
        // Extroversion filter
        if (personalityTraits.extroversion < 0.3) {
            // Introverted avatars speak more quietly, use fewer exclamations
            filteredMessage = this.applyIntroversionFilter(filteredMessage);
            personalityAdjustments.push('introversion_filter');
        } else if (personalityTraits.extroversion > 0.7) {
            // Extroverted avatars are more expressive, enthusiastic
            filteredMessage = this.applyExtroversionFilter(filteredMessage);
            personalityAdjustments.push('extroversion_filter');
        }
        
        // Agreeableness filter
        if (personalityTraits.agreeableness > 0.7) {
            // Highly agreeable avatars soften harsh statements
            filteredMessage = this.applyAgreeablenessFilter(filteredMessage);
            personalityAdjustments.push('agreeableness_filter');
        }
        
        // Conscientiousness filter
        if (personalityTraits.conscientiousness > 0.6) {
            // Conscientious avatars are more precise and structured
            filteredMessage = this.applyConscientiousnessFilter(filteredMessage);
            personalityAdjustments.push('conscientiousness_filter');
        }
        
        // Neuroticism filter
        if (personalityTraits.neuroticism > 0.6) {
            // High neuroticism adds uncertainty, hedging
            filteredMessage = this.applyNeuroticismFilter(filteredMessage);
            personalityAdjustments.push('neuroticism_filter');
        }
        
        return {
            filtered_message: filteredMessage,
            personality_adjustments: personalityAdjustments,
            original_message: llmResponse.message
        };
    }

    prepareTTSEmotionalParams(avatarId, emotionalResponse, personalityFilter) {
        const baseParams = this.getTTSEmotionalMapping(emotionalResponse);
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        // Adjust TTS parameters based on personality
        const adjustedParams = { ...baseParams };
        
        // Personality adjustments
        if (personalityTraits.extroversion < 0.3) {
            adjustedParams.volume *= 0.8; // Quieter for introverts
            adjustedParams.speed *= 0.9;  // Slower for introverts
        }
        
        if (personalityTraits.neuroticism > 0.6) {
            adjustedParams.stability *= 0.7; // Less stable for high neuroticism
        }
        
        if (personalityTraits.agreeableness > 0.7) {
            adjustedParams.warmth *= 1.2; // Warmer for agreeable avatars
        }
        
        return {
            ...adjustedParams,
            emotion: emotionalResponse.primary_emotion,
            intensity: emotionalResponse.intensity,
            personality_modifier: this.getTTSPersonalityModifier(personalityTraits)
        };
    }

    prepareLive2DMotionParams(avatarId, emotionalResponse, personalityFilter) {
        const baseMotion = this.getLive2DMotionMapping(emotionalResponse);
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        // Adjust motion intensity and type based on personality
        const adjustedMotion = { ...baseMotion };
        
        if (personalityTraits.extroversion < 0.3) {
            adjustedMotion.intensity *= 0.7; // Subtler motions for introverts
        }
        
        if (personalityTraits.neuroticism > 0.6) {
            adjustedMotion.duration *= 1.2; // Longer, more hesitant motions
        }
        
        return {
            ...adjustedMotion,
            emotion: emotionalResponse.primary_emotion,
            personality_influence: this.getLive2DPersonalityInfluence(personalityTraits),
            sync_with_speech: true
        };
    }

    calculateResponseTiming(avatarId, emotionalResponse) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        let baseDelay = 1000; // 1 second base delay
        
        // Personality-based timing adjustments
        if (personalityTraits.extroversion > 0.7) {
            baseDelay *= 0.7; // Extroverts respond faster
        } else if (personalityTraits.extroversion < 0.3) {
            baseDelay *= 1.5; // Introverts take more time
        }
        
        if (personalityTraits.conscientiousness > 0.6) {
            baseDelay *= 1.2; // Conscientious avatars think before speaking
        }
        
        // Emotional state adjustments
        if (emotionalResponse.primary_emotion === 'excited') {
            baseDelay *= 0.6; // Excited avatars respond quickly
        } else if (emotionalResponse.primary_emotion === 'shy') {
            baseDelay *= 1.8; // Shy avatars hesitate
        }
        
        return {
            delay_ms: baseDelay + Math.random() * 500, // Add natural variation
            typing_indicator_duration: baseDelay * 0.3,
            emotional_buildup_time: emotionalResponse.intensity * 300
        };
    }

    generateBehavioralCues(avatarId, emotionalResponse) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const cues = [];
        
        // Personality-based behavioral cues
        if (personalityTraits.extroversion > 0.7) {
            cues.push('animated_gestures', 'direct_eye_contact', 'open_posture');
        } else if (personalityTraits.extroversion < 0.3) {
            cues.push('minimal_gestures', 'averted_gaze', 'closed_posture');
        }
        
        // Emotional behavioral cues
        switch (emotionalResponse.primary_emotion) {
            case 'happy':
                cues.push('smile', 'light_bounce', 'bright_eyes');
                break;
            case 'sad':
                cues.push('downcast_eyes', 'slumped_shoulders', 'slow_movements');
                break;
            case 'excited':
                cues.push('rapid_movements', 'wide_eyes', 'energetic_gestures');
                break;
            case 'shy':
                cues.push('fidgeting', 'looking_away', 'small_gestures');
                break;
            case 'angry':
                cues.push('tense_posture', 'furrowed_brow', 'sharp_movements');
                break;
        }
        
        return cues;
    }

    // Essential Helper Methods for Avatar Context
    getAvatarAppearanceContext(avatarId) {
        // This would be enhanced with actual avatar model data
        const avatarData = this.avatarDatabase.get(avatarId);
        
        return {
            clothing: this.inferClothingFromModel(avatarId),
            features: this.inferFeaturesFromModel(avatarId),
            style: this.inferStyleFromModel(avatarId),
            colors: this.inferColorsFromModel(avatarId)
        };
    }

    inferClothingFromModel(avatarId) {
        // Basic inference based on avatar name/model - would be enhanced with actual model analysis
        const commonClothing = {
            'haruka': ['school_uniform', 'skirt', 'blouse', 'tie'],
            'rika': ['casual_dress', 'cardigan', 'leggings'],
            'hiyori': ['traditional_outfit', 'kimono', 'obi'],
            'default': ['casual_clothing', 'shirt', 'pants']
        };
        
        return commonClothing[avatarId.toLowerCase()] || commonClothing['default'];
    }

    inferFeaturesFromModel(avatarId) {
        // Basic feature inference - would be enhanced with actual model data
        return {
            hair_color: 'varies',
            eye_color: 'varies',
            height: 'average',
            build: 'slender'
        };
    }

    inferStyleFromModel(avatarId) {
        const commonStyles = {
            'haruka': ['schoolgirl', 'energetic', 'youthful'],
            'rika': ['casual', 'modern', 'comfortable'],
            'hiyori': ['traditional', 'elegant', 'graceful'],
            'default': ['casual', 'friendly', 'approachable']
        };
        
        return commonStyles[avatarId.toLowerCase()] || commonStyles['default'];
    }

    inferColorsFromModel(avatarId) {
        // Color scheme inference
        return ['varies']; // Would be enhanced with actual model color analysis
    }

    findClothingReferences(message, clothingList) {
        const clothingTerms = [
            'skirt', 'dress', 'shirt', 'blouse', 'pants', 'jeans', 'tie', 'uniform',
            'cardigan', 'jacket', 'coat', 'kimono', 'obi', 'leggings', 'socks',
            'shoes', 'boots', 'sandals', 'hat', 'cap', 'bow', 'ribbon'
        ];
        
        const matches = [];
        clothingTerms.forEach(term => {
            if (message.includes(term) && clothingList.some(item => 
                item.toLowerCase().includes(term) || term.includes(item.toLowerCase())
            )) {
                matches.push(term);
            }
        });
        
        return matches;
    }

    findFeatureReferences(message, features) {
        const featureTerms = [
            'hair', 'eyes', 'face', 'smile', 'height', 'tall', 'short',
            'cute', 'beautiful', 'pretty', 'elegant', 'graceful'
        ];
        
        const matches = [];
        featureTerms.forEach(term => {
            if (message.includes(term)) {
                matches.push(term);
            }
        });
        
        return matches;
    }

    findStyleReferences(message, styleList) {
        const styleTerms = [
            'style', 'fashion', 'look', 'appearance', 'outfit', 'aesthetic',
            'elegant', 'casual', 'formal', 'traditional', 'modern', 'trendy'
        ];
        
        const matches = [];
        styleTerms.forEach(term => {
            if (message.includes(term) && styleList.some(style => 
                style.toLowerCase().includes(term) || term.includes(style.toLowerCase())
            )) {
                matches.push(term);
            }
        });
        
        return matches;
    }

    getAvatarInterests(avatarId) {
        // Default interests based on avatar personality - would be enhanced with profile data
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const interests = [];
        
        if (personalityTraits.openness > 0.6) {
            interests.push('art', 'music', 'books', 'creativity', 'culture');
        }
        
        if (personalityTraits.extroversion > 0.6) {
            interests.push('socializing', 'parties', 'sports', 'events', 'people');
        }
        
        if (personalityTraits.conscientiousness > 0.6) {
            interests.push('organization', 'planning', 'learning', 'improvement');
        }
        
        // Avatar-specific interests
        const avatarSpecificInterests = {
            'haruka': ['school', 'studying', 'friends', 'anime', 'manga'],
            'rika': ['fashion', 'shopping', 'photography', 'travel'],
            'hiyori': ['traditional_arts', 'tea_ceremony', 'calligraphy', 'nature']
        };
        
        const specific = avatarSpecificInterests[avatarId.toLowerCase()] || [];
        return [...interests, ...specific];
    }

    extractTopicKeywords(message) {
        // Simple keyword extraction - would be enhanced with NLP
        const commonTopics = [
            'school', 'work', 'family', 'friends', 'love', 'food', 'music', 'movies',
            'books', 'games', 'sports', 'travel', 'fashion', 'art', 'technology',
            'nature', 'animals', 'weather', 'health', 'news', 'politics', 'religion'
        ];
        
        return commonTopics.filter(topic => 
            message.toLowerCase().includes(topic)
        );
    }

    getAvatarKnowledgeDomains(avatarId) {
        // Basic knowledge domains - would be enhanced with avatar profiles
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const domains = [];
        
        if (personalityTraits.openness > 0.6) {
            domains.push({
                domain: 'arts_culture',
                keywords: ['art', 'music', 'literature', 'culture', 'creativity']
            });
        }
        
        if (personalityTraits.conscientiousness > 0.6) {
            domains.push({
                domain: 'academic',
                keywords: ['education', 'learning', 'science', 'research', 'study']
            });
        }
        
        // Avatar-specific knowledge
        const avatarKnowledge = {
            'haruka': [
                { domain: 'student_life', keywords: ['school', 'classes', 'exams', 'homework'] },
                { domain: 'youth_culture', keywords: ['anime', 'manga', 'games', 'trends'] }
            ],
            'rika': [
                { domain: 'lifestyle', keywords: ['fashion', 'beauty', 'relationships', 'social'] },
                { domain: 'modern_culture', keywords: ['technology', 'social_media', 'trends'] }
            ],
            'hiyori': [
                { domain: 'traditional_culture', keywords: ['tradition', 'ceremony', 'history', 'customs'] },
                { domain: 'nature_wisdom', keywords: ['nature', 'seasons', 'mindfulness', 'balance'] }
            ]
        };
        
        const specific = avatarKnowledge[avatarId.toLowerCase()] || [];
        return [...domains, ...specific];
    }

    containsTimeReferences(message) {
        const timeWords = [
            'morning', 'afternoon', 'evening', 'night', 'today', 'yesterday', 'tomorrow',
            'now', 'later', 'soon', 'early', 'late', 'time', 'clock', 'hour', 'minute'
        ];
        
        return timeWords.some(word => message.includes(word));
    }

    containsLocationReferences(message) {
        const locationWords = [
            'here', 'there', 'place', 'room', 'home', 'school', 'work', 'outside',
            'inside', 'where', 'location', 'city', 'town', 'building', 'park'
        ];
        
        return locationWords.some(word => message.includes(word));
    }

    containsActivityReferences(message) {
        const activityWords = [
            'doing', 'playing', 'working', 'studying', 'reading', 'watching', 'listening',
            'talking', 'walking', 'running', 'eating', 'sleeping', 'thinking', 'feeling'
        ];
        
        return activityWords.some(word => message.includes(word));
    }

    calculateBehavioralConstraints(avatarId, context) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        const relationship = this.getUserRelationshipContext(avatarId);
        const socialContext = this.getSocialContext();
        
        return {
            response_threshold: this.calculateResponseThreshold(personalityTraits, context),
            emotional_boundaries: this.getPersonalityEmotionalBoundaries(personalityTraits),
            social_appropriateness: this.calculateSocialAppropriatenessLevel(relationship, socialContext),
            topic_boundaries: this.getTopicBoundaries(personalityTraits, relationship),
            interaction_limits: this.getInteractionLimits(personalityTraits, context)
        };
    }

    calculateResponseThreshold(personalityTraits, context) {
        let threshold = 0.5; // Base threshold
        
        // Extroversion affects willingness to speak
        threshold -= personalityTraits.extroversion * 0.3;
        
        // Agreeableness affects willingness to help/respond
        threshold -= personalityTraits.agreeableness * 0.2;
        
        // Neuroticism might increase threshold (more hesitant)
        threshold += personalityTraits.neuroticism * 0.2;
        
        // Context adjustments
        if (context.addressing_analysis?.directly_addressed) {
            threshold -= 0.3; // More likely to respond when directly addressed
        }
        
        return Math.max(0.1, Math.min(0.9, threshold));
    }

    getPersonalityEmotionalBoundaries(personalityTraits) {
        return {
            max_anger: personalityTraits.agreeableness > 0.7 ? 0.6 : 0.9,
            max_sadness: personalityTraits.neuroticism > 0.6 ? 0.8 : 0.5,
            max_excitement: personalityTraits.extroversion > 0.7 ? 1.0 : 0.7,
            emotional_volatility: personalityTraits.neuroticism || 0.3
        };
    }

    // Personality Filter Implementation Methods
    applyIntroversionFilter(message) {
        // Make message more subdued, less exclamatory
        return message
            .replace(/!/g, '.')
            .replace(/\b(LOVE|AMAZING|AWESOME|FANTASTIC)\b/gi, (match) => 
                match.toLowerCase().replace(/(.)/g, '$1'))
            .replace(/\b(really really|super|extremely)\b/gi, 'quite');
    }

    applyExtroversionFilter(message) {
        // Make message more enthusiastic and expressive
        if (!message.includes('!') && Math.random() < 0.3) {
            message = message.replace(/\.$/, '!');
        }
        
        return message
            .replace(/\b(good|nice|interesting)\b/gi, (match) => {
                const alternatives = {
                    'good': 'amazing',
                    'nice': 'fantastic',
                    'interesting': 'fascinating'
                };
                return alternatives[match.toLowerCase()] || match;
            });
    }

    applyAgreeablenessFilter(message) {
        // Soften harsh statements, add politeness
        return message
            .replace(/\b(wrong|stupid|bad|terrible)\b/gi, (match) => 
                'maybe not quite right')
            .replace(/^(No[,.]?)/i, 'Well, I think maybe')
            .replace(/\b(I disagree)\b/gi, 'I see it a bit differently');
    }

    applyConscientiousnessFilter(message) {
        // Add precision and structure
        if (Math.random() < 0.3) {
            const qualifiers = ['specifically', 'precisely', 'exactly', 'particularly'];
            const qualifier = qualifiers[Math.floor(Math.random() * qualifiers.length)];
            message = message.replace(/\b(I think|I believe)\b/i, `I ${qualifier} think`);
        }
        
        return message;
    }

    applyNeuroticismFilter(message) {
        // Add uncertainty and hedging
        const hedges = ['I think', 'maybe', 'perhaps', 'I suppose', 'it seems like'];
        
        if (Math.random() < 0.4 && !hedges.some(hedge => message.toLowerCase().includes(hedge))) {
            const hedge = hedges[Math.floor(Math.random() * hedges.length)];
            message = `${hedge} ${message.charAt(0).toLowerCase() + message.slice(1)}`;
        }
        
        return message;
    }

    // Additional Essential Methods
    calculateDefaultEmotion(personalityTraits) {
        if (personalityTraits.extroversion > 0.6) return 'friendly';
        if (personalityTraits.neuroticism > 0.6) return 'cautious';
        if (personalityTraits.agreeableness > 0.7) return 'caring';
        return 'neutral';
    }

    calculateEmotionalRange(personalityTraits) {
        let range = 0.5; // Base range
        
        range += personalityTraits.extroversion * 0.3; // More expressive
        range += (1.0 - personalityTraits.neuroticism) * 0.2; // More stable = wider range
        
        return Math.min(1.0, range);
    }

    calculateMaxEmotionalIntensity(personalityTraits) {
        let maxIntensity = 0.8; // Base maximum
        
        maxIntensity += personalityTraits.extroversion * 0.2;
        maxIntensity -= personalityTraits.conscientiousness * 0.1; // More controlled
        
        return Math.min(1.0, maxIntensity);
    }

    findDominantEmotion(emotions) {
        if (emotions.length === 0) return 'neutral';
        
        const emotionCounts = {};
        emotions.forEach(emotion => {
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        });
        
        return Object.keys(emotionCounts).reduce((a, b) => 
            emotionCounts[a] > emotionCounts[b] ? a : b
        );
    }

    calculateEmotionalContagion(avatarId, dominantEmotion) {
        const personalityTraits = this.getAvatarPersonalityTraits(avatarId);
        
        // Agreeableness increases emotional contagion
        return personalityTraits.agreeableness * 0.6 + 
               (1.0 - personalityTraits.conscientiousness) * 0.2;
    }

    getAvatarRelationship(avatarId1, avatarId2) {
        // Enhanced relationship tracking
        if (!this.relationshipDatabase) this.relationshipDatabase = new Map();
        
        const relationshipKey = `${avatarId1}-${avatarId2}`;
        const reverseKey = `${avatarId2}-${avatarId1}`;
        
        let relationship = this.relationshipDatabase.get(relationshipKey) || 
                          this.relationshipDatabase.get(reverseKey);
        
        if (!relationship) {
            // Initialize new relationship
            relationship = {
                type: 'new',
                conversation_count: 0,
                last_interaction_tone: 'neutral',
                positive_interactions: 0,
                negative_interactions: 0,
                recent_arguments: 0,
                compatibility_score: this.calculateCompatibility(
                    this.getAvatarPersonalityTraits(avatarId1),
                    this.getAvatarPersonalityTraits(avatarId2)
                ),
                first_meeting: new Date(),
                last_interaction: null
            };
            this.relationshipDatabase.set(relationshipKey, relationship);
        }
        
        return relationship;
    }

    updateAvatarRelationship(avatarId1, avatarId2, emotion, compatibility) {
        const relationship = this.getAvatarRelationship(avatarId1, avatarId2);
        
        relationship.conversation_count++;
        relationship.last_interaction = new Date();
        relationship.last_interaction_tone = emotion;
        
        if (['happy', 'excited', 'friendly', 'warm'].includes(emotion)) {
            relationship.positive_interactions++;
        } else if (['angry', 'annoyed', 'frustrated', 'dismissive'].includes(emotion)) {
            relationship.negative_interactions++;
            if (emotion === 'angry') relationship.recent_arguments++;
        }
        
        // Update relationship type based on interaction history
        const totalInteractions = relationship.positive_interactions + relationship.negative_interactions;
        if (totalInteractions > 0) {
            const positiveRatio = relationship.positive_interactions / totalInteractions;
            if (positiveRatio > 0.7) relationship.type = 'friends';
            else if (positiveRatio < 0.3) relationship.type = 'antagonistic';
            else relationship.type = 'neutral';
        }
    }

    getCompatibilityScore(avatarId1, avatarId2) {
        const relationship = this.getAvatarRelationship(avatarId1, avatarId2);
        return relationship.compatibility_score;
    }

    scheduleAutonomousInteractions(avatar) {
        // Schedule random autonomous behavior
        const delay = 60000 + Math.random() * 120000; // 1-3 minutes
        
        setTimeout(() => {
            if (this.activeAvatars.has(avatar.id)) {
                // Decide what type of autonomous behavior
                const behavior = this.chooseAutonomousBehavior(avatar);
                this.executeAutonomousBehavior(avatar, behavior);
            }
        }, delay);
    }

    chooseAutonomousBehavior(avatar) {
        const traits = this.getAvatarPersonalityTraits(avatar.id);
        const otherAvatars = this.getActiveAvatars().filter(a => a.id !== avatar.id);
        
        if (otherAvatars.length > 0 && Math.random() < traits.extroversion) {
            return { type: 'avatar_conversation', target: otherAvatars[Math.floor(Math.random() * otherAvatars.length)] };
        }
        
        if (Math.random() < 0.3) {
            return { type: 'spontaneous_comment' };
        }
        
        return { type: 'none' };
    }

    executeAutonomousBehavior(avatar, behavior) {
        switch (behavior.type) {
            case 'avatar_conversation':
                this.sendAvatarToAvatarMessage(avatar, behavior.target);
                break;
            case 'spontaneous_comment':
                this.sendAutonomousMessage(avatar);
                break;
        }
    }

    getAvatarConversationHistory(avatarId1, avatarId2, limit = 10) {
        return this.messageHistory
            .filter(msg => 
                (msg.speaker?.id === avatarId1 && msg.listener?.id === avatarId2) ||
                (msg.speaker?.id === avatarId2 && msg.listener?.id === avatarId1) ||
                (msg.avatar?.id === avatarId1 && msg.responding_to === avatarId2) ||
                (msg.avatar?.id === avatarId2 && msg.responding_to === avatarId1)
            )
            .slice(-limit);
    }

    getCurrentConversationTopic() {
        const recentMessages = this.messageHistory.slice(-3);
        if (recentMessages.length === 0) return 'general';
        
        // Simple topic extraction
        const lastMessage = recentMessages[recentMessages.length - 1];
        return this.extractTopic(lastMessage.message) || 'general';
    }

    getSocialContext() {
        const activeCount = this.activeAvatars.size;
        const userEngagement = this.calculateUserEngagement();
        
        return {
            active_avatar_count: activeCount,
            user_engagement_level: userEngagement,
            conversation_energy: this.calculateConversationEnergy(),
            dominant_emotion: this.getDominantGroupEmotion(),
            interaction_type: activeCount > 2 ? 'group' : activeCount === 2 ? 'pair' : 'individual'
        };
    }

    calculateConversationEnergy() {
        const recentMessages = this.messageHistory.slice(-5);
        if (recentMessages.length === 0) return 0.5;
        
        const avgLength = recentMessages.reduce((sum, msg) => sum + msg.message.length, 0) / recentMessages.length;
        const timeSpread = recentMessages.length > 1 ? 
            new Date(recentMessages[recentMessages.length - 1].timestamp) - new Date(recentMessages[0].timestamp) : 
            60000;
        
        let energy = Math.min(1.0, avgLength / 100);
        if (timeSpread < 60000) energy += 0.3; // Rapid fire conversation
        
        return Math.max(0.1, Math.min(1.0, energy));
    }

    getDominantGroupEmotion() {
        const recentEmotions = this.messageHistory
            .slice(-5)
            .filter(msg => msg.primary_emotion)
            .map(msg => msg.primary_emotion);
        
        if (recentEmotions.length === 0) return 'neutral';
        
        // Count emotion frequencies
        const emotionCounts = {};
        recentEmotions.forEach(emotion => {
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        });
        
        return Object.keys(emotionCounts).reduce((a, b) => 
            emotionCounts[a] > emotionCounts[b] ? a : b
        );
    }

    calculateEmotionVariance(emotionalTriggers) {
        if (emotionalTriggers.length < 2) return 0;
        
        const emotions = emotionalTriggers.map(trigger => trigger.emotion);
        const uniqueEmotions = new Set(emotions).size;
        
        return Math.min(1.0, uniqueEmotions / emotions.length);
    }

    analyzeMessageTone(message) {
        // Enhanced message tone analysis
        if (!message) return 'neutral';
        
        const lowerMessage = message.toLowerCase();
        
        // Positive indicators
        if (lowerMessage.match(/\b(happy|excited|great|wonderful|amazing|love|perfect|awesome|fantastic)\b/)) return 'positive';
        if (lowerMessage.match(/\b(thank|thanks|appreciate|grateful|pleased)\b/)) return 'grateful';
        if (lowerMessage.match(/\b(funny|hilarious|laugh|joke|amusing)\b/)) return 'humorous';
        
        // Negative indicators  
        if (lowerMessage.match(/\b(angry|mad|furious|annoyed|frustrated|irritated|hate)\b/)) return 'aggressive';
        if (lowerMessage.match(/\b(sad|disappointed|hurt|upset|terrible|awful|depressed)\b/)) return 'sad';
        if (lowerMessage.match(/\b(stupid|idiot|dumb|wrong|mistake|failure)\b/)) return 'rude';
        
        // Neutral indicators
        if (lowerMessage.match(/\b(curious|interesting|wonder|think|question|maybe)\b/)) return 'curious';
        if (lowerMessage.match(/\b(sorry|apologize|mistake|wrong|fault)\b/)) return 'apologetic';
        if (lowerMessage.match(/\b(worried|anxious|nervous|scared|concerned)\b/)) return 'worried';
        
        return 'neutral';
    }

    // Additional utility methods
    calculateParticipationBalance(participationMap) {
        const participationValues = Object.values(participationMap);
        if (participationValues.length === 0) return 1.0;
        
        const max = Math.max(...participationValues);
        const min = Math.min(...participationValues);
        
        return max === 0 ? 1.0 : min / max;
    }

    analyzeConversationFlow(interactions) {
        if (interactions.length < 2) return 'minimal';
        
        const speakers = interactions.map(msg => msg.avatar?.id);
        const uniqueSpeakers = new Set(speakers).size;
        const totalMessages = interactions.length;
        
        if (uniqueSpeakers === 1) return 'monologue';
        if (totalMessages / uniqueSpeakers > 2) return 'active';
        return 'balanced';
    }

    getUserRelationshipContext(avatarId) {
        // Analyze user's relationship with specific avatar
        const userMessages = this.messageHistory.filter(msg => msg.type === 'user').slice(-10);
        const avatarInteractions = this.messageHistory.filter(msg => 
            msg.avatar?.id === avatarId && msg.responding_to === 'user'
        ).slice(-5);
        
        if (userMessages.length === 0) {
            return {
                user_preference_for_avatar: 0.5,
                last_interaction_tone: 'neutral',
                unresolved_issues: [],
                positive_interactions_count: 0
            };
        }
        
        const lastUserMessage = userMessages[userMessages.length - 1];
        const lastInteractionTone = this.analyzeMessageTone(lastUserMessage.message);
        
        return {
            user_preference_for_avatar: this.calculateUserPreferenceForAvatar(avatarId),
            last_interaction_tone: lastInteractionTone,
            unresolved_issues: this.findUnresolvedIssues(avatarId),
            positive_interactions_count: avatarInteractions.filter(msg => 
                ['happy', 'friendly', 'excited'].includes(msg.primary_emotion)
            ).length
        };
    }

    calculateUserPreferenceForAvatar(avatarId) {
        const totalUserMessages = this.messageHistory.filter(msg => msg.type === 'user').length;
        const messagesWithAvatar = this.messageHistory.filter(msg => 
            msg.type === 'user' && 
            this.messageHistory.some(response => 
                response.avatar?.id === avatarId && 
                Math.abs(new Date(response.timestamp) - new Date(msg.timestamp)) < 60000
            )
        ).length;
        
        return totalUserMessages > 0 ? messagesWithAvatar / totalUserMessages : 0.5;
    }

    findUnresolvedIssues(avatarId) {
        // Simple implementation - look for negative interactions without positive follow-up
        const recentInteractions = this.messageHistory
            .filter(msg => msg.avatar?.id === avatarId || msg.responding_to === avatarId)
            .slice(-10);
        
        const negativeInteractions = recentInteractions.filter(msg => 
            ['angry', 'frustrated', 'disappointed'].includes(this.analyzeMessageTone(msg.message))
        );
        
        return negativeInteractions.map(msg => ({
            issue: this.extractTopic(msg.message),
            timestamp: msg.timestamp,
            resolved: false
        }));
    }
}

// Initialize global avatar chat manager
let avatarChatManager = null;

function addMessage(sender, message, type = 'info', avatar = null, metadata = null) {
    // Add a message to the chat window with enhanced speaker identification and TTS integration
    // Always get fresh reference to ensure we have the right element
    const chatMessagesContainer = document.getElementById('chatMessages');
    if (!chatMessagesContainer) {
        console.error('Chat messages container not found! Expected element with ID: chatMessages');
        console.log('Available elements:', document.querySelectorAll('[id*="chat"], [class*="chat"]'));
        return;
    }

    console.log('📝 Adding message to container:', chatMessagesContainer.className, 'ID:', chatMessagesContainer.id);

    const msgDiv = document.createElement('div');
    
    // Ensure sender and type are valid, non-empty strings
    const validSender = sender && typeof sender === 'string' ? sender : 'ai';
    const validType = type && typeof type === 'string' ? type : 'info';
    
    // Base class is always 'chat-message'
    msgDiv.className = 'chat-message';
    
    // Enhanced speaker identification
    let speakerPrefix = '';
    let speakerClass = '';
    
    // Generate timestamp first for proper formatting
    let timestamp = '';
    if (metadata?.timestamp) {
        timestamp = metadata.timestamp;
    } else {
        const now = new Date();
        timestamp = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    if (validSender === 'user') {
        const userName = metadata?.speaker || (avatarChatManager?.currentUser?.display_name) || 'Anonymous User';
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name user-speaker">${userName}</span>`;
        speakerClass = 'user-message';
    } else if (validSender === 'ai' && avatar) {
        const avatarName = avatar.displayName || avatar.name || 'Assistant';
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name avatar-speaker" data-avatar-id="${avatar.id}">${avatarName}</span>`;
        speakerClass = 'avatar-message';
        msgDiv.setAttribute('data-avatar-id', avatar.id);
        
        // Add emotion indicator if available
        if (metadata?.emotion && metadata.emotion !== 'neutral') {
            speakerPrefix += ` <span class="emotion-indicator emotion-${metadata.emotion}">😊</span>`;
        }
    } else if (validSender === 'system') {
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name system-speaker">System</span>`;
        speakerClass = 'system-message';
    } else {
        // Fallback for any other sender types
        speakerPrefix = `<span class="message-timestamp">${timestamp}</span> - <span class="speaker-name">${validSender}</span>`;
        speakerClass = 'system-message'; // Use existing class as fallback
    }
    
    // Create message content with DATE - NAME format
    const messageContent = `
        <div class="message-header">
            ${speakerPrefix}
        </div>
        <div class="message-text">${formatMessage(message)}</div>
    `;
    
    // Only add class if it's not empty
    if (speakerClass && speakerClass.trim() !== '') {
        msgDiv.classList.add(speakerClass);
    }
    if (validType === 'separator') {
        msgDiv.classList.add('separator-message');
    }
    
    msgDiv.innerHTML = messageContent;
    chatMessagesContainer.appendChild(msgDiv);
    
    setTimeout(() => msgDiv.classList.add('visible'), 10);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    
    // NEW: Trigger TTS for AI messages automatically
    if (validSender === 'ai' && avatar && typeof triggerEmotionalTTS === 'function') {
        // Extract TTS parameters from metadata or generate defaults
        const emotion = metadata?.emotion || metadata?.primary_emotion || 'neutral';
        const intensity = metadata?.emotion_intensity || metadata?.intensity || 0.5;
        const avatarId = avatar.id || avatar.name || 'default';
        
        // Get personality traits from avatar or metadata
        let personalityTraits = {};
        if (metadata?.personality_traits) {
            personalityTraits = metadata.personality_traits;
        } else if (avatarChatManager && avatarChatManager.getAvatarPersonalityTraits) {
            personalityTraits = avatarChatManager.getAvatarPersonalityTraits(avatar);
        }
        
        // Trigger emotional TTS with proper integration
        setTimeout(async () => {
            try {
                console.log(`🔊 Auto-triggering TTS for avatar ${avatarId} with emotion: ${emotion}`);
                await triggerEmotionalTTS(message, emotion, avatarId, personalityTraits, intensity);
            } catch (error) {
                console.warn('Failed to auto-trigger TTS:', error);
            }
        }, 200); // Small delay to ensure UI is updated first
    }
    
    console.log('✅ Message added to chat messages container');
}

function formatMessage(message) {
    // Format message for display (basic HTML escaping)
    return String(message).replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function sendMessage() {
    // Send user message to backend and display response with multi-avatar support
    if (!window.userInput) window.userInput = document.getElementById('chatInput');
    
    // Add null check to prevent the error
    if (!window.userInput) {
        console.error('Chat input element not found! Looking for element with ID: chatInput');
        return;
    }
    
    const text = window.userInput.value.trim();
    if (!text) return;
    
    // Initialize avatar chat manager if not already done
    if (!avatarChatManager) {
        avatarChatManager = new AvatarChatManager();
        // Give it a moment to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    addMessage('user', text, 'info', null, {
        speaker: avatarChatManager?.currentUser?.display_name || 'Anonymous User',
        timestamp: new Date().toLocaleTimeString()
    });
    window.userInput.value = '';
    
    try {
        // Ensure active avatars are updated before checking
        if (avatarChatManager) {
            avatarChatManager.updateActiveAvatars();
        }
        
        // Check if we have active avatars for multi-avatar mode
        const activeAvatars = avatarChatManager ? avatarChatManager.getActiveAvatars() : [];
        console.log('🎭 Active avatars for chat:', activeAvatars.length, activeAvatars.map(a => a.name));
        
        if (activeAvatars.length > 0) {
            // Use multi-avatar system
            console.log('📤 Using multi-avatar chat mode');
            const result = await avatarChatManager.sendMessageWithAvatar(text);
            addMessage('ai', result.response.reply || '[No reply]', 'info', result.avatar, {
                emotion: result.response.primary_emotion,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Trigger avatar motion if available
            if (result.avatar && result.avatar.pixiModel && result.response.primary_emotion) {
                triggerAvatarMotion(result.avatar.pixiModel, result.response.primary_emotion);
            }
            
        } else {
            // Fallback to legacy single chat mode
            console.log('📤 No active avatars found, using legacy chat mode');
            await sendMessageLegacy(text);
        }
        
    } catch (error) {
        console.error('Multi-avatar chat error:', error);
        // Fallback to legacy mode on error
        try {
            await sendMessageLegacy(text);
        } catch (legacyError) {
            addSystemMessage('Failed to send message: ' + error.message, 'error');
        }
    }
}

async function sendMessageLegacy(text) {
    // Legacy single chat mode for fallback
    try {
        // Use the same fetchWithFallback system as Live2D models
        let apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL;
        let response;
        
        // Try primary API URL first
        if (apiBaseUrl) {
            try {
                response = await fetch(`${apiBaseUrl}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                if (response.ok) {
                    const data = await response.json();
                    addMessage('ai', data.reply || '[No reply]');
                    return;
                }
            } catch (error) {
                console.warn(`Chat API failed with primary URL ${apiBaseUrl}:`, error.message);
            }
        }
        
        // Try fallback URLs if primary failed
        const fallbackUrls = window.ai2d_chat_CONFIG?.FALLBACK_URLS || [];
        for (const fallbackUrl of fallbackUrls) {
            try {
                console.log(`Trying chat API fallback URL: ${fallbackUrl}`);
                response = await fetch(`${fallbackUrl}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                if (response.ok) {
                    console.log(`Chat API successful with fallback URL: ${fallbackUrl}`);
                    // Update the working URL for future requests
                    window.ai2d_chat_CONFIG.API_BASE_URL = fallbackUrl;
                    const data = await response.json();
                    addMessage('ai', data.reply || '[No reply]');
                    return;
                }
            } catch (error) {
                console.warn(`Chat API fallback failed with ${fallbackUrl}:`, error.message);
            }
        }
        
        // If all URLs failed, throw error
        throw new Error('All chat API endpoints failed');
        
    } catch (error) {
        throw error; // Re-throw to be handled by caller
    }
}

function triggerAvatarMotion(pixiModel, emotion, params = {}) {
    // Enhanced avatar motion system with robust fallback handling and TTS integration
    return new Promise(async (resolve, reject) => {
        try {
            console.log(`🎭 Triggering avatar motion: ${emotion}`, params);
            
            if (!pixiModel) {
                console.warn('No PIXI model provided for motion trigger');
                resolve();
                return;
            }
            
            // Get avatar-specific information
            const avatarId = params.avatar_id || pixiModel.internalModel?.settings?.name || 'unknown';
            const intensity = params.intensity || 0.5;
            const duration = params.duration || 2.0;
            
            // Check if avatar has motion capabilities
            const hasMotionFunction = typeof pixiModel.motion === 'function';
            const hasExpressionFunction = typeof pixiModel.expression === 'function';
            
            if (!hasMotionFunction && !hasExpressionFunction) {
                console.warn(`⚠️ Avatar ${avatarId} has no motion or expression capabilities`);
                // Still resolve to continue the flow
                resolve();
                return;
            }
            
            // Enhanced motion mapping with fallbacks
            const motionName = await getAvatarSpecificMotion(pixiModel, emotion, avatarId);
            const expressionName = await getAvatarSpecificExpression(pixiModel, emotion, avatarId);
            
            console.log(`🎭 Selected motion: "${motionName}", expression: "${expressionName}" for ${avatarId}`);
            
            // Try to trigger motion with error handling
            let motionTriggered = false;
            if (hasMotionFunction && motionName) {
                try {
                    await pixiModel.motion(motionName);
                    motionTriggered = true;
                    console.log(`✨ Motion "${motionName}" triggered successfully for ${avatarId}`);
                } catch (motionError) {
                    console.warn(`⚠️ Motion "${motionName}" failed for ${avatarId}:`, motionError);
                    // Try fallback motion
                    await tryFallbackMotion(pixiModel, emotion, avatarId);
                }
            }
            
            // Try to trigger expression with error handling
            let expressionTriggered = false;
            if (hasExpressionFunction && expressionName) {
                try {
                    await pixiModel.expression(expressionName);
                    expressionTriggered = true;
                    console.log(`✨ Expression "${expressionName}" triggered successfully for ${avatarId}`);
                } catch (expressionError) {
                    console.warn(`⚠️ Expression "${expressionName}" failed for ${avatarId}:`, expressionError);
                    // Try fallback expression
                    await tryFallbackExpression(pixiModel, emotion, avatarId);
                }
            }
            
            // Apply intensity-based modifications if supported
            if (intensity > 0.7) {
                applyIntensityModifications(pixiModel, intensity, avatarId);
            }
            
            // Handle special emotional states with personality awareness
            if (params.personality_traits) {
                await handlePersonalityBasedEmotionalStates(pixiModel, emotion, intensity, params.personality_traits, avatarId);
            } else {
                await handleSpecialEmotionalStates(pixiModel, emotion, intensity, avatarId);
            }
            
            // Apply TTS synchronization parameters if provided
            if (params.sync_with_speech && params.tts_params) {
                applySpeechSynchronization(pixiModel, params.tts_params, avatarId);
            }
            
            // Log motion status
            if (!motionTriggered && !expressionTriggered) {
                console.warn(`⚠️ No motion or expression could be triggered for ${avatarId} with emotion: ${emotion}`);
            }
            
            // Set motion duration and cleanup
            setTimeout(() => {
                try {
                    if (hasMotionFunction) {
                        pixiModel.motion('idle');
                    }
                    if (hasExpressionFunction) {
                        pixiModel.expression('default');
                    }
                    console.log(`🔄 Reset ${avatarId} to idle state after ${duration}s`);
                } catch (resetError) {
                    console.warn(`⚠️ Failed to reset ${avatarId} to idle:`, resetError);
                }
                resolve();
            }, duration * 1000);
            
        } catch (error) {
            console.error('❌ Error in triggerAvatarMotion:', error);
            // Don't reject - continue the flow even if motion fails
            resolve();
        }
    });
}

async function getAvatarSpecificMotion(pixiModel, emotion, avatarId) {
    // Get motion name specific to this avatar, with fallbacks
    
    // First, try to get avatar-specific motions from the model
    const availableMotions = getAvailableMotions(pixiModel, avatarId);
    
    // Enhanced motion mapping with personality-aware fallbacks
    const primaryMotionMap = {
        'happy': ['happy', 'smile', 'joy', 'cheerful'],
        'excited': ['excited', 'happy', 'energetic', 'bounce'],
        'sad': ['sad', 'cry', 'disappointed', 'melancholy'],
        'angry': ['angry', 'mad', 'frustrated', 'upset'],
        'surprised': ['surprised', 'shock', 'amazed', 'gasp'],
        'curious': ['thinking', 'wonder', 'curious', 'ponder'],
        'seductive': ['flirt', 'wink', 'seduce', 'tease'],
        'horny': ['flirt', 'seduce', 'aroused', 'lustful'],
        'flirtatious': ['flirt', 'wink', 'playful', 'tease'],
        'passionate': ['passionate', 'intense', 'fervent', 'ardent'],
        'romantic': ['love', 'romantic', 'tender', 'affectionate'],
        'shy': ['shy', 'bashful', 'timid', 'embarrassed'],
        'nervous': ['nervous', 'anxious', 'worried', 'fidget'],
        'embarrassed': ['embarrassed', 'blush', 'shy', 'flustered'],
        'confident': ['confident', 'proud', 'bold', 'assertive'],
        'dominant': ['confident', 'commanding', 'authoritative', 'bold'],
        'submissive': ['shy', 'meek', 'submissive', 'yielding'],
        'mischievous': ['mischievous', 'playful', 'sneaky', 'impish'],
        'playful': ['playful', 'fun', 'energetic', 'bounce'],
        'sensual': ['sensual', 'sultry', 'alluring', 'seductive'],
        'thoughtful': ['thinking', 'contemplative', 'reflective', 'pensive'],
        'neutral': ['idle', 'neutral', 'default', 'calm'],
        'default': ['idle', 'neutral', 'default', 'calm']
    };
    
    // Get motion candidates for this emotion
    const motionCandidates = primaryMotionMap[emotion] || primaryMotionMap['default'];
    
    // Find first available motion from candidates
    for (const candidate of motionCandidates) {
        if (availableMotions.includes(candidate)) {
            return candidate;
        }
    }
    
    // Semantic fallback for unknown emotions
    const semanticFallbacks = getSemanticMotionFallbacks(emotion);
    for (const fallback of semanticFallbacks) {
        if (availableMotions.includes(fallback)) {
            return fallback;
        }
    }
    
    // Final fallback to most basic motions
    const basicMotions = ['idle', 'default', 'neutral', 'happy', 'sad'];
    for (const basic of basicMotions) {
        if (availableMotions.includes(basic)) {
            return basic;
        }
    }
    
    // If no motions available, return null
    console.warn(`⚠️ No suitable motion found for ${avatarId} with emotion: ${emotion}`);
    return null;
}

async function getAvatarSpecificExpression(pixiModel, emotion, avatarId) {
    // Get expression name specific to this avatar, with fallbacks
    
    const availableExpressions = getAvailableExpressions(pixiModel, avatarId);
    
    // Enhanced expression mapping
    const primaryExpressionMap = {
        'happy': ['smile', 'happy', 'joy', 'cheerful'],
        'excited': ['excited', 'thrilled', 'energetic', 'smile'],
        'sad': ['sad', 'cry', 'disappointed', 'melancholy'],
        'angry': ['angry', 'mad', 'frustrated', 'scowl'],
        'surprised': ['surprised', 'shock', 'amazed', 'wide_eyes'],
        'curious': ['curious', 'wonder', 'thinking', 'raised_eyebrow'],
        'seductive': ['wink', 'sultry', 'seductive', 'smirk'],
        'horny': ['wink', 'lustful', 'aroused', 'bedroom_eyes'],
        'flirtatious': ['wink', 'flirty', 'playful', 'smirk'],
        'passionate': ['love', 'passionate', 'intense', 'fervent'],
        'romantic': ['love', 'romantic', 'tender', 'soft_smile'],
        'shy': ['embarrassed', 'blush', 'shy', 'timid'],
        'nervous': ['nervous', 'worried', 'anxious', 'tense'],
        'embarrassed': ['embarrassed', 'blush', 'flustered', 'shy'],
        'confident': ['smile', 'confident', 'proud', 'smirk'],
        'dominant': ['confident', 'commanding', 'stern', 'intense'],
        'submissive': ['shy', 'meek', 'submissive', 'lowered_eyes'],
        'mischievous': ['wink', 'smirk', 'playful', 'impish'],
        'playful': ['smile', 'playful', 'cheerful', 'wink'],
        'sensual': ['sultry', 'alluring', 'seductive', 'half_lidded'],
        'thoughtful': ['thinking', 'contemplative', 'pensive', 'serious'],
        'neutral': ['default', 'neutral', 'calm', 'normal'],
        'default': ['default', 'neutral', 'normal', 'calm']
    };
    
    // Get expression candidates for this emotion
    const expressionCandidates = primaryExpressionMap[emotion] || primaryExpressionMap['default'];
    
    // Find first available expression from candidates
    for (const candidate of expressionCandidates) {
        if (availableExpressions.includes(candidate)) {
            return candidate;
        }
    }
    
    // Semantic fallback for unknown emotions
    const semanticFallbacks = getSemanticExpressionFallbacks(emotion);
    for (const fallback of semanticFallbacks) {
        if (availableExpressions.includes(fallback)) {
            return fallback;
        }
    }
    
    // Final fallback to most basic expressions
    const basicExpressions = ['default', 'neutral', 'normal', 'smile', 'sad'];
    for (const basic of basicExpressions) {
        if (availableExpressions.includes(basic)) {
            return basic;
        }
    }
    
    // If no expressions available, return null
    console.warn(`⚠️ No suitable expression found for ${avatarId} with emotion: ${emotion}`);
    return null;
}

function getAvailableMotions(pixiModel, avatarId) {
    // Get list of available motions for this avatar
    const availableMotions = [];
    
    try {
        // Try to get motions from the model's internal structure
        if (pixiModel.internalModel?.motionManager?.definitions) {
            Object.keys(pixiModel.internalModel.motionManager.definitions).forEach(group => {
                if (Array.isArray(pixiModel.internalModel.motionManager.definitions[group])) {
                    pixiModel.internalModel.motionManager.definitions[group].forEach((motion, index) => {
                        availableMotions.push(`${group}_${index}`);
                        availableMotions.push(group); // Also add group name
                    });
                }
            });
        }
        
        // Add common motion names that might be available
        const commonMotions = [
            'idle', 'happy', 'sad', 'angry', 'surprised', 'thinking', 
            'flirt', 'shy', 'confident', 'passionate', 'default', 'neutral',
            'tap_body', 'tap_head', 'shake', 'nod', 'wave', 'dance'
        ];
        
        availableMotions.push(...commonMotions);
        
        // Remove duplicates
        return [...new Set(availableMotions)];
        
    } catch (error) {
        console.warn(`⚠️ Error getting available motions for ${avatarId}:`, error);
        // Return basic fallback motions
        return ['idle', 'default', 'neutral', 'happy', 'sad'];
    }
}

function getAvailableExpressions(pixiModel, avatarId) {
    // Get list of available expressions for this avatar
    const availableExpressions = [];
    
    try {
        // Try to get expressions from the model's internal structure
        if (pixiModel.internalModel?.expressionManager?.definitions) {
            Object.keys(pixiModel.internalModel.expressionManager.definitions).forEach(expression => {
                availableExpressions.push(expression);
            });
        }
        
        // Add common expression names that might be available
        const commonExpressions = [
            'default', 'neutral', 'smile', 'sad', 'angry', 'surprised', 
            'wink', 'embarrassed', 'curious', 'love', 'normal', 'happy',
            'excited', 'thinking', 'confident', 'shy'
        ];
        
        availableExpressions.push(...commonExpressions);
        
        // Remove duplicates
        return [...new Set(availableExpressions)];
        
    } catch (error) {
        console.warn(`⚠️ Error getting available expressions for ${avatarId}:`, error);
        // Return basic fallback expressions
        return ['default', 'neutral', 'smile', 'sad'];
    }
}

function getSemanticMotionFallbacks(emotion) {
    // Provide semantic fallbacks for unknown emotions
    const emotionLower = emotion.toLowerCase();
    
    // Positive emotions
    if (emotionLower.includes('joy') || emotionLower.includes('cheer') || emotionLower.includes('delight')) {
        return ['happy', 'smile', 'cheerful'];
    }
    
    // Negative emotions
    if (emotionLower.includes('depress') || emotionLower.includes('despair') || emotionLower.includes('grief')) {
        return ['sad', 'cry', 'melancholy'];
    }
    
    // Anger emotions
    if (emotionLower.includes('rage') || emotionLower.includes('fury') || emotionLower.includes('irritat')) {
        return ['angry', 'mad', 'frustrated'];
    }
    
    // Surprise emotions
    if (emotionLower.includes('shock') || emotionLower.includes('astonish') || emotionLower.includes('amaze')) {
        return ['surprised', 'shock', 'amazed'];
    }
    
    // Love/attraction emotions
    if (emotionLower.includes('love') || emotionLower.includes('attract') || emotionLower.includes('affection')) {
        return ['love', 'romantic', 'flirt'];
    }
    
    // Sexual emotions
    if (emotionLower.includes('lust') || emotionLower.includes('arousal') || emotionLower.includes('desire')) {
        return ['flirt', 'seductive', 'passionate'];
    }
    
    // Default fallback
    return ['idle', 'neutral', 'default'];
}

function getSemanticExpressionFallbacks(emotion) {
    // Provide semantic fallbacks for unknown expression emotions
    const emotionLower = emotion.toLowerCase();
    
    // Similar to motion fallbacks but for expressions
    if (emotionLower.includes('joy') || emotionLower.includes('cheer') || emotionLower.includes('delight')) {
        return ['smile', 'happy', 'cheerful'];
    }
    
    if (emotionLower.includes('depress') || emotionLower.includes('despair') || emotionLower.includes('grief')) {
        return ['sad', 'cry', 'melancholy'];
    }
    
    if (emotionLower.includes('rage') || emotionLower.includes('fury') || emotionLower.includes('irritat')) {
        return ['angry', 'mad', 'scowl'];
    }
    
    if (emotionLower.includes('shock') || emotionLower.includes('astonish') || emotionLower.includes('amaze')) {
        return ['surprised', 'wide_eyes', 'amazed'];
    }
    
    if (emotionLower.includes('love') || emotionLower.includes('attract') || emotionLower.includes('affection')) {
        return ['love', 'romantic', 'soft_smile'];
    }
    
    if (emotionLower.includes('lust') || emotionLower.includes('arousal') || emotionLower.includes('desire')) {
        return ['wink', 'sultry', 'seductive'];
    }
    
    return ['default', 'neutral', 'normal'];
}

async function tryFallbackMotion(pixiModel, emotion, avatarId) {
    // Try fallback motions when primary motion fails
    const fallbackMotions = ['idle', 'default', 'neutral', 'happy'];
    
    console.log(`🔄 Attempting fallback motions for ${avatarId} (original emotion: ${emotion})`);
    
    for (const fallback of fallbackMotions) {
        try {
            await pixiModel.motion(fallback);
            console.log(`✅ Fallback motion "${fallback}" succeeded for ${avatarId}`);
            return true;
        } catch (error) {
            console.warn(`⚠️ Fallback motion "${fallback}" also failed for ${avatarId}:`, error.message);
        }
    }
    
    // Final attempt: try to check if model has any motions at all
    console.log(`🔍 Checking available motions for ${avatarId}...`);
    const availableMotions = await getAvailableAvatarMotions(pixiModel, avatarId);
    
    if (availableMotions.length > 0) {
        try {
            const firstAvailable = availableMotions[0];
            await pixiModel.motion(firstAvailable);
            console.log(`✅ Used first available motion "${firstAvailable}" for ${avatarId}`);
            return true;
        } catch (error) {
            console.warn(`⚠️ Even first available motion failed for ${avatarId}`);
        }
    }
    
    console.error(`❌ No working motions found for ${avatarId} - avatar may not support motion system`);
    return false;
}

async function tryFallbackExpression(pixiModel, emotion, avatarId) {
    // Try fallback expressions when primary expression fails
    const fallbackExpressions = ['default', 'neutral', 'normal', 'smile'];
    
    console.log(`🔄 Attempting fallback expressions for ${avatarId} (original emotion: ${emotion})`);
    
    for (const fallback of fallbackExpressions) {
        try {
            await pixiModel.expression(fallback);
            console.log(`✅ Fallback expression "${fallback}" succeeded for ${avatarId}`);
            return true;
        } catch (error) {
            console.warn(`⚠️ Fallback expression "${fallback}" also failed for ${avatarId}:`, error.message);
        }
    }
    
    // Final attempt: check available expressions
    console.log(`🔍 Checking available expressions for ${avatarId}...`);
    const availableExpressions = await getAvailableAvatarExpressions(pixiModel, avatarId);
    
    if (availableExpressions.length > 0) {
        try {
            const firstAvailable = availableExpressions[0];
            await pixiModel.expression(firstAvailable);
            console.log(`✅ Used first available expression "${firstAvailable}" for ${avatarId}`);
            return true;
        } catch (error) {
            console.warn(`⚠️ Even first available expression failed for ${avatarId}`);
        }
    }
    
    console.error(`❌ No working expressions found for ${avatarId} - avatar may not support expression system`);
    return false;
}

async function getAvailableAvatarMotions(pixiModel, avatarId) {
    // Discover what motions are actually available for this avatar
    const potentialMotions = [
        'idle', 'default', 'neutral', 'happy', 'sad', 'angry', 'surprised', 
        'excited', 'thinking', 'flirt', 'shy', 'confident', 'passionate', 'laugh'
    ];
    
    const availableMotions = [];
    
    for (const motion of potentialMotions) {
        try {
            // Test if motion exists without actually triggering it
            if (typeof pixiModel.motion === 'function') {
                // Check if the motion exists in the model's motion list
                if (pixiModel.internalModel?.motions?.[motion] || 
                    pixiModel.motions?.[motion] ||
                    pixiModel._motions?.[motion]) {
                    availableMotions.push(motion);
                }
            }
        } catch (error) {
            // Motion doesn't exist or can't be checked
        }
    }
    
    console.log(`📋 Available motions for ${avatarId}:`, availableMotions);
    return availableMotions;
}

async function getAvailableAvatarExpressions(pixiModel, avatarId) {
    // Discover what expressions are actually available for this avatar
    const potentialExpressions = [
        'default', 'neutral', 'normal', 'smile', 'sad', 'angry', 'surprised',
        'wink', 'embarrassed', 'excited', 'curious', 'love', 'thinking'
    ];
    
    const availableExpressions = [];
    
    for (const expression of potentialExpressions) {
        try {
            // Check if expression exists in the model
            if (typeof pixiModel.expression === 'function') {
                if (pixiModel.internalModel?.expressions?.[expression] || 
                    pixiModel.expressions?.[expression] ||
                    pixiModel._expressions?.[expression]) {
                    availableExpressions.push(expression);
                }
            }
        } catch (error) {
            // Expression doesn't exist or can't be checked
        }
    }
    
    console.log(`📋 Available expressions for ${avatarId}:`, availableExpressions);
    return availableExpressions;
}

function applyIntensityModifications(pixiModel, intensity, avatarId) {
    // Apply intensity-based modifications to avatar behavior
    try {
        if (typeof pixiModel.setMotionIntensity === 'function') {
            pixiModel.setMotionIntensity(intensity);
        }
        
        if (typeof pixiModel.setAnimationSpeed === 'function') {
            const speedMultiplier = 0.8 + (intensity * 0.4); // Range: 0.8 to 1.2
            pixiModel.setAnimationSpeed(speedMultiplier);
        }
        
        console.log(`🎚️ Applied intensity ${intensity} modifications to ${avatarId}`);
    } catch (error) {
        console.warn(`⚠️ Failed to apply intensity modifications to ${avatarId}:`, error);
    }
}

async function handlePersonalityBasedEmotionalStates(pixiModel, emotion, intensity, personalityTraits, avatarId) {
    // Handle emotional states with personality awareness
    try {
        // Seductive personalities express emotions differently
        if (personalityTraits.seductive > 0.5 || personalityTraits.horny > 0.3) {
            await handleSeductivePersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId);
        }
        
        // Shy personalities have subdued expressions
        if (personalityTraits.shy > 0.5 || personalityTraits.neuroticism > 0.6) {
            await handleShyPersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId);
        }
        
        // Confident personalities have amplified expressions
        if (personalityTraits.confident > 0.7 || personalityTraits.extroversion > 0.7) {
            await handleConfidentPersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId);
        }
        
        // Default emotional handling for other personalities
        await handleSpecialEmotionalStates(pixiModel, emotion, intensity, avatarId);
        
    } catch (error) {
        console.warn(`⚠️ Error handling personality-based emotions for ${avatarId}:`, error);
        // Fallback to basic emotional handling
        await handleSpecialEmotionalStates(pixiModel, emotion, intensity, avatarId);
    }
}

async function handleSeductivePersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId) {
    // Seductive personalities express emotions with more sensuality
    const seductiveIntensity = Math.min(1.0, intensity + personalityTraits.seductive * 0.3);
    
    try {
        if (typeof pixiModel.setAnimationSpeed === 'function') {
            pixiModel.setAnimationSpeed(0.6 + seductiveIntensity * 0.3); // Slower, more sultry
        }
        
        // Add subtle winking or eye movements if supported
        if (typeof pixiModel.expression === 'function') {
            setTimeout(() => {
                try {
                    pixiModel.expression('wink');
                } catch (e) {
                    console.warn(`Wink expression not available for ${avatarId}`);
                }
            }, 1000);
        }
        
        console.log(`💋 Applied seductive personality emotional expression to ${avatarId}`);
    } catch (error) {
        console.warn(`⚠️ Error applying seductive emotions to ${avatarId}:`, error);
    }
}

async function handleShyPersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId) {
    // Shy personalities have more subdued emotional expressions
    const shyIntensity = Math.max(0.2, intensity - personalityTraits.shy * 0.4);
    
    try {
        if (typeof pixiModel.setAnimationSpeed === 'function') {
            pixiModel.setAnimationSpeed(0.7 + shyIntensity * 0.2); // Slower, more hesitant
        }
        
        // Reduce overall motion intensity
        if (typeof pixiModel.setMotionIntensity === 'function') {
            pixiModel.setMotionIntensity(shyIntensity);
        }
        
        console.log(`😳 Applied shy personality emotional expression to ${avatarId}`);
    } catch (error) {
        console.warn(`⚠️ Error applying shy emotions to ${avatarId}:`, error);
    }
}

async function handleConfidentPersonalityEmotions(pixiModel, emotion, intensity, personalityTraits, avatarId) {
    // Confident personalities have amplified emotional expressions
    const confidentIntensity = Math.min(1.0, intensity + personalityTraits.confident * 0.2);
    
    try {
        if (typeof pixiModel.setAnimationSpeed === 'function') {
            pixiModel.setAnimationSpeed(1.0 + confidentIntensity * 0.3); // Faster, more dynamic
        }
        
        // Amplify motion intensity
        if (typeof pixiModel.setMotionIntensity === 'function') {
            pixiModel.setMotionIntensity(confidentIntensity);
        }
        
        console.log(`😎 Applied confident personality emotional expression to ${avatarId}`);
    } catch (error) {
        console.warn(`⚠️ Error applying confident emotions to ${avatarId}:`, error);
    }
}

function applySpeechSynchronization(pixiModel, ttsParams, avatarId) {
    // Apply TTS synchronization parameters to avatar
    try {
        // Synchronize animation speed with speech rate
        if (typeof pixiModel.setAnimationSpeed === 'function' && ttsParams.speed) {
            const speechSyncSpeed = Math.max(0.5, Math.min(2.0, ttsParams.speed));
            pixiModel.setAnimationSpeed(speechSyncSpeed);
        }
        
        // Apply warmth-based modifications
        if (ttsParams.warmth > 0.7 && typeof pixiModel.setEmotionalWarmth === 'function') {
            pixiModel.setEmotionalWarmth(ttsParams.warmth);
        }
        
        console.log(`🎵 Applied speech synchronization to ${avatarId}:`, ttsParams);
    } catch (error) {
        console.warn(`⚠️ Error applying speech sync to ${avatarId}:`, error);
    }
}

function handleSpecialEmotionalStates(pixiModel, emotion, intensity, avatarId) {
    // Handle special emotional behaviors
    try {
        switch (emotion) {
            case 'seductive':
            case 'horny':
            case 'flirtatious':
                // Slower, more sultry movements
                if (typeof pixiModel.setAnimationSpeed === 'function') {
                    pixiModel.setAnimationSpeed(0.7 + (intensity * 0.2));
                }
                // Trigger wink if available
                if (typeof pixiModel.expression === 'function') {
                    setTimeout(() => pixiModel.expression('wink'), 500);
                }
                break;
                
            case 'passionate':
            case 'romantic':
                // Slightly faster, more expressive movements
                if (typeof pixiModel.setAnimationSpeed === 'function') {
                    pixiModel.setAnimationSpeed(1.0 + (intensity * 0.3));
                }
                break;
                
            case 'shy':
            case 'nervous':
            case 'embarrassed':
                // Subtle, hesitant movements
                if (typeof pixiModel.setAnimationSpeed === 'function') {
                    pixiModel.setAnimationSpeed(0.8 - (intensity * 0.2));
                }
                // Trigger blush if available
                if (typeof pixiModel.expression === 'function') {
                    setTimeout(() => pixiModel.expression('embarrassed'), 300);
                }
                break;
                
            case 'confident':
            case 'dominant':
                // Strong, pronounced movements
                if (typeof pixiModel.setAnimationSpeed === 'function') {
                    pixiModel.setAnimationSpeed(1.1 + (intensity * 0.2));
                }
                break;
        }
    } catch (error) {
        console.warn('Error handling special emotional state:', error);
    }
}

// New functions for TTS integration
function triggerAvatarExpression(avatarId, expression, intensity = 0.5) {
    return new Promise((resolve) => {
        try {
            console.log(`😊 Triggering avatar expression: ${expression} for ${avatarId}`);
            
            // Find the avatar model
            const pixiModel = findAvatarModel(avatarId);
            if (!pixiModel) {
                console.warn(`Avatar model not found: ${avatarId}`);
                resolve();
                return;
            }
            
            // Trigger expression
            if (typeof pixiModel.expression === 'function') {
                pixiModel.expression(expression);
                console.log(`✨ Expression "${expression}" triggered`);
            }
            
            // Duration based on intensity
            const duration = 1.5 + (intensity * 1.5);
            setTimeout(() => {
                if (typeof pixiModel.expression === 'function') {
                    pixiModel.expression('default');
                }
                resolve();
            }, duration * 1000);
            
        } catch (error) {
            console.warn('Failed to trigger avatar expression:', error);
            resolve();
        }
    });
}

function setAvatarBlinkRate(avatarId, rate) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (pixiModel && typeof pixiModel.setBlinkRate === 'function') {
            pixiModel.setBlinkRate(rate);
            console.log(`👁️ Blink rate set to ${rate} for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar blink rate:', error);
    }
}

function setAvatarBodySway(avatarId, intensity) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (pixiModel && typeof pixiModel.setBodySway === 'function') {
            pixiModel.setBodySway(intensity);
            console.log(`🌊 Body sway set to ${intensity} for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar body sway:', error);
    }
}

function setAvatarMouthShape(avatarId, mouthShape, intensity = 0.7) {
    try {
        const pixiModel = findAvatarModel(avatarId);
        if (pixiModel && typeof pixiModel.setMouthShape === 'function') {
            pixiModel.setMouthShape(mouthShape, intensity);
            // console.log(`👄 Mouth shape "${mouthShape}" set for ${avatarId}`);
        }
    } catch (error) {
        console.warn('Failed to set avatar mouth shape:', error);
    }
}

function findAvatarModel(avatarId) {
    // Find the PIXI model for an avatar ID
    try {
        // Check if avatarId is already a PIXI model
        if (avatarId && typeof avatarId === 'object' && avatarId.motion) {
            return avatarId;
        }
        
        // Look in loaded avatars
        if (window.loadedAvatars) {
            for (let avatar of window.loadedAvatars) {
                if (avatar.id === avatarId || avatar.name === avatarId) {
                    return avatar.pixiModel;
                }
            }
        }
        
        // Look in Live2D model manager
        if (window.live2dManager && window.live2dManager.models) {
            for (let [modelId, model] of window.live2dManager.models) {
                if (modelId === avatarId || model.name === avatarId) {
                    return model.pixiModel;
                }
            }
        }
        
        return null;
    } catch (error) {
        console.warn('Error finding avatar model:', error);
        return null;
    }
}

// Export new functions to window for global access
window.triggerAvatarExpression = triggerAvatarExpression;
window.setAvatarBlinkRate = setAvatarBlinkRate;
window.setAvatarBodySway = setAvatarBodySway;
window.setAvatarMouthShape = setAvatarMouthShape;
window.findAvatarModel = findAvatarModel;

function addSystemMessage(message, type = 'info') {
    // Add a system message to the chat window
    addMessage('system', message, type);
}

// Test function to verify chat messages are going to the right container
function testChatMessage() {
    console.log('🧪 Testing chat message placement...');
    
    // Check if containers exist
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatInputContainer = document.querySelector('.chat-input-container');
    
    console.log('📍 Container check:');
    console.log('- chatMessages container:', chatMessages ? 'Found' : 'NOT FOUND', chatMessages);
    console.log('- chatInput element:', chatInput ? 'Found' : 'NOT FOUND', chatInput);
    console.log('- chatInputContainer:', chatInputContainer ? 'Found' : 'NOT FOUND', chatInputContainer);
    
    if (chatMessages) {
        console.log('✅ Chat messages container found - adding test message...');
        addMessage('system', '🧪 Test message - this should appear in the MESSAGES area, not the input area!', 'info');
        
        // Test different message types for alignment
        addMessage('user', 'Test user message (should be right-aligned)', 'info', null, {
            speaker: 'Test User',
            timestamp: new Date().toLocaleTimeString()
        });
        
        addMessage('ai', 'Test AI message (should be left-aligned)', 'info', {
            id: 'test-avatar',
            name: 'TestBot',
            displayName: 'Test Bot'
        }, {
            emotion: 'happy',
            timestamp: new Date().toLocaleTimeString()
        });
        
        // Log where the message actually went
        setTimeout(() => {
            const messagesInCorrectArea = chatMessages.querySelectorAll('.chat-message').length;
            const messagesInInputArea = chatInputContainer ? chatInputContainer.querySelectorAll('.chat-message').length : 0;
            
            console.log(`📊 Message placement results:`);
            console.log(`- Messages in correct area (chatMessages): ${messagesInCorrectArea}`);
            console.log(`- Messages in wrong area (input container): ${messagesInInputArea}`);
            
            if (messagesInCorrectArea > 0 && messagesInInputArea === 0) {
                console.log('✅ SUCCESS: Messages are in the correct area!');
            } else {
                console.log('❌ PROBLEM: Messages are in the wrong area!');
            }
        }, 100);
    } else {
        console.error('❌ Chat messages container not found!');
    }
}

// Debug function to manually trigger avatar detection
function debugActiveAvatars() {
    console.log('🔍 === ACTIVE AVATARS DEBUG ===');
    if (avatarChatManager) {
        console.log('🔄 Updating active avatars...');
        avatarChatManager.updateActiveAvatars();
        
        const activeAvatars = avatarChatManager.getActiveAvatars();
        console.log('📊 Active avatars found:', activeAvatars.length);
        activeAvatars.forEach((avatar, index) => {
            console.log(`  ${index + 1}. ${avatar.displayName} (${avatar.id})`);
        });
        
        if (window.live2dMultiModelManager) {
            const allModels = window.live2dMultiModelManager.getAllModels();
            console.log('📦 All Live2D models:', allModels.length);
            allModels.forEach((model, index) => {
                console.log(`  ${index + 1}. ${model.name} - visible: ${model.pixiModel?.visible}, alpha: ${model.pixiModel?.alpha}`);
            });
        }
    } else {
        console.warn('❌ No avatar chat manager available');
    }
    console.log('=== END AVATARS DEBUG ===');
}

// Debug function to manually trigger autonomous greetings
function triggerTestGreetings() {
    console.log('👋 === TRIGGERING TEST GREETINGS ===');
    if (avatarChatManager) {
        const activeAvatars = avatarChatManager.getActiveAvatars();
        console.log(`🎭 Found ${activeAvatars.length} active avatars`);
        
        if (activeAvatars.length > 0) {
            // Trigger greetings immediately for testing
            activeAvatars.forEach((avatar, index) => {
                setTimeout(() => {
                    avatarChatManager.sendAutonomousGreeting(avatar);
                }, index * 1000); // 1 second apart for testing
            });
            console.log('✅ Triggered test greetings');
        } else {
            console.warn('❌ No active avatars to greet');
        }
    } else {
        console.warn('❌ Avatar chat manager not available');
    }
    console.log('=== END GREETING TEST ===');
}

// Function to test autonomous backend system
function testAutonomousBackend() {
    console.log('🧪 === TESTING AUTONOMOUS BACKEND ===');
    
    // Check if socket is available
    if (typeof socket !== 'undefined' && socket.connected) {
        console.log('✅ Socket connected, requesting autonomous status');
        socket.emit('get_autonomous_status');
        
        // Also request a test message
        setTimeout(() => {
            console.log('📤 Requesting test autonomous message');
            socket.emit('test_autonomous_message');
        }, 1000);
        
        // And try to enable autonomous system
        setTimeout(() => {
            console.log('🤖 Enabling autonomous system');
            socket.emit('enable_autonomous_avatars', { enabled: true });
        }, 2000);
        
    } else {
        console.warn('❌ Socket not connected - cannot test autonomous backend');
    }
    
    console.log('=== END BACKEND TEST ===');
}

// Export test function to window for console access
window.testChatMessage = testChatMessage;
window.debugActiveAvatars = debugActiveAvatars;
window.triggerTestGreetings = triggerTestGreetings;
window.testAutonomousBackend = testAutonomousBackend;

// Debug function to check current user state
function checkUserAuth() {
    console.log('🔍 === USER AUTHENTICATION CHECK ===');
    console.log('avatarChatManager exists:', !!avatarChatManager);
    
    if (avatarChatManager) {
        console.log('Current user:', avatarChatManager.currentUser);
        console.log('User ID type:', typeof avatarChatManager.currentUser?.id);
        console.log('User profile:', avatarChatManager.userProfile);
    }
    
    console.log('localStorage currentUser:', localStorage.getItem('currentUser'));
    console.log('localStorage currentUserId:', localStorage.getItem('currentUserId'));
    
    // Check user selection system
    if (window.userSelectionSystem) {
        console.log('User selection system current user:', window.userSelectionSystem.currentUser);
    }
    
    console.log('=== END USER AUTH CHECK ===');
}

// Function to force refresh user authentication
async function refreshUserAuth() {
    console.log('🔄 Forcing user authentication refresh...');
    if (avatarChatManager) {
        await avatarChatManager.refreshCurrentUser();
    } else {
        console.warn('❌ No avatar chat manager available');
    }
}

// Export debug functions
window.checkUserAuth = checkUserAuth;
window.refreshUserAuth = refreshUserAuth;

// Export to window for global access
window.addMessage = addMessage;
window.formatMessage = formatMessage;
window.sendMessage = sendMessage;
window.addSystemMessage = addSystemMessage;
window.AvatarChatManager = AvatarChatManager;

// Test functions for autonomous system
window.testAutonomousGreeting = function(avatarName) {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    const avatar = activeAvatars.find(a => a.name.toLowerCase().includes(avatarName.toLowerCase()));
    
    if (avatar) {
        console.log(`🧪 Testing autonomous greeting for ${avatar.displayName}`);
        avatarChatManager.sendAutonomousGreeting(avatar);
    } else {
        console.error(`Avatar "${avatarName}" not found. Active avatars:`, activeAvatars.map(a => a.name));
    }
};

window.testAutonomousMessage = function(avatarName) {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    const avatar = activeAvatars.find(a => a.name.toLowerCase().includes(avatarName.toLowerCase()));
    
    if (avatar) {
        console.log(`🧪 Testing autonomous message for ${avatar.displayName}`);
        avatarChatManager.sendAutonomousMessage(avatar);
    } else {
        console.error(`Avatar "${avatarName}" not found. Active avatars:`, activeAvatars.map(a => a.name));
    }
};

window.forceAutonomousConversation = function() {
    if (!avatarChatManager) {
        console.error('Avatar chat manager not initialized');
        return;
    }
    
    const activeAvatars = avatarChatManager.getActiveAvatars();
    if (activeAvatars.length >= 2) {
        const speakingAvatar = activeAvatars[0];
        const respondingAvatar = activeAvatars[1];
        
        console.log(`🧪 Forcing conversation between ${speakingAvatar.displayName} and ${respondingAvatar.displayName}`);
        
        // First avatar sends a message
        avatarChatManager.sendAutonomousMessage(speakingAvatar);
        
        // Second avatar responds after a delay
        setTimeout(() => {
            avatarChatManager.sendAutonomousResponse(respondingAvatar, speakingAvatar, "test message");
        }, 3000);
        
    } else {
        console.error('Need at least 2 active avatars for conversation. Current:', activeAvatars.length);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize avatar chat manager after a short delay to ensure Live2D system is ready
    setTimeout(() => {
        if (!avatarChatManager) {
            console.log('🚀 Creating avatar chat manager...');
            avatarChatManager = new AvatarChatManager();
            window.avatarChatManager = avatarChatManager;
        }
    }, 1000);
    
    // Also listen for user authentication events at the document level
    document.addEventListener('userAuthenticated', async (event) => {
        console.log('🔐 User authenticated event received, refreshing chat manager user...');
        if (avatarChatManager) {
            await avatarChatManager.refreshCurrentUser();
        }
    });
});
