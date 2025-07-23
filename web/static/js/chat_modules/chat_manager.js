/**
 * Streamlined Avatar Chat Manager
 * Core chat management with modular architecture
 * This is the new modular version that uses separate manager classes
 */
class AvatarChatManager {
    constructor() {
        // Core state
        this.activeAvatars = new Map(); // Map of avatar_id -> avatar_data
        this.speakingAvatar = null; // Currently speaking avatar
        this.avatarDatabase = new Map(); // Avatar-specific information
        this.messageHistory = []; // Chat history with avatar attribution
        this.currentUser = null; // Current user information
        this.userProfile = null; // User profile data
        this.chatHistory = []; // Full chat history from database
        
        // Module references (will be set after modules load)
        this.personalityManager = null;
        this.conversationManager = null;
        this.responseManager = null;
        this.interactionManager = null;
        
        // Initialize system
        this.initializeAvatarSystem();
    }

    async initializeAvatarSystem() {
        console.log('🎭 Initializing streamlined avatar chat system...');
        
        // Wait for modules to be ready
        await this.waitForModules();
        
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
        
        // Check for active avatars after initialization and clear chat if none
        setTimeout(() => {
            this.updateActiveAvatars();
            if (this.activeAvatars.size === 0) {
                console.log('🔍 No active avatars found after initialization');
            }
        }, 3000); // Wait 3 seconds for models to load
        
        console.log('🎭 Modular chat system initialized with user context:', this.currentUser?.display_name || 'No user');
    }

    async waitForModules() {
        // Wait for chat modules to be ready
        return new Promise((resolve) => {
            if (window.chatSystemModules && window.chatSystemModules.initialized) {
                this.connectToModules();
                resolve();
            } else {
                document.addEventListener('chatModulesReady', () => {
                    this.connectToModules();
                    resolve();
                });
            }
        });
    }

    connectToModules() {
        console.log('🔗 Connecting to chat system modules...');
        const modules = window.chatSystemModules.getAllModules();
        
        this.personalityManager = modules.personalityManager;
        this.conversationManager = modules.conversationManager;
        this.responseManager = modules.responseManager;
        this.interactionManager = modules.interactionManager;
        
        console.log('✅ Connected to all chat modules');
    }

    async checkForExpectedUser() {
        // Check if localStorage indicates there should be a current user
        const storedUsername = localStorage.getItem('currentUser');
        const storedUserId = localStorage.getItem('currentUserId');
        
        if (storedUsername && storedUserId) {
            console.log('🔍 Found stored user info, but no current user from API');
            console.log('Stored username:', storedUsername, 'Stored ID:', storedUserId);
            
            // Try to refresh/reload user information
            await this.loadCurrentUser();
        }
    }

    async loadCurrentUser() {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/users/current`);
            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                console.log('👤 Loaded current user:', userData.display_name, 'ID:', userData.id);
                
                // Also load user profile if available
                await this.loadUserProfile();
            } else {
                console.log('ℹ️ No current user session found');
                this.currentUser = null;
            }
        } catch (error) {
            console.warn('Failed to load current user:', error);
            this.currentUser = null;
        }
    }

    async loadUserProfile() {
        if (!this.currentUser) return;

        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/users/${this.currentUser.id}/profile`);
            if (response.ok) {
                const profileData = await response.json();
                this.userProfile = profileData;
                console.log('📋 Loaded user profile for:', this.currentUser.display_name);
            }
        } catch (error) {
            console.warn('Failed to load user profile:', error);
        }
    }

    async loadChatHistory(limit = 50) {
        // Only load chat history if we have a valid authenticated user
        if (!this.currentUser || typeof this.currentUser.id !== 'number') {
            console.log('ℹ️ Skipping chat history load - no authenticated user');
            this.chatHistory = [];
            return;
        }

        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/chat/history?limit=${limit}`);
            if (response.ok) {
                const historyData = await response.json();
                this.chatHistory = historyData.messages || [];
                console.log(`📚 Loaded ${this.chatHistory.length} chat history messages`);
                
                // Update conversation manager with history
                if (this.conversationManager) {
                    this.conversationManager.updateMessageHistory(this.chatHistory);
                }
                
                // Display chat history in UI
                this.displayChatHistory();
            } else {
                console.warn('Failed to load chat history:', response.status);
                this.chatHistory = [];
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            this.chatHistory = [];
        }
    }

    async loadAvatarDatabase() {
        try {
            const apiBaseUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || window.location.origin;
            const response = await fetch(`${apiBaseUrl}/api/live2d/models`);
            if (response.ok) {
                const avatarData = await response.json();
                
                // Process avatar data into the database map
                this.avatarDatabase.clear();
                if (avatarData.models) {
                    avatarData.models.forEach(avatar => {
                        const displayName = this.formatAvatarName(avatar.name);
                        this.avatarDatabase.set(avatar.name, {
                            id: avatar.name,
                            name: avatar.name,
                            displayName: displayName,
                            modelPath: avatar.model_path,
                            capabilities: avatar.capabilities || {},
                            // Enhanced character identity information
                            character_info: {
                                name: displayName,
                                character_name: displayName,
                                identity: displayName,
                                self_name: displayName,
                                is_character: true,
                                model_source: avatar.name
                            },
                            background: avatar.background || {
                                description: `I am ${displayName}, a Live2D character.`,
                                personality: avatar.personality || 'friendly and helpful'
                            },
                            appearance: avatar.appearance || {
                                description: `I appear as ${displayName}, a Live2D animated character.`
                            },
                            ...avatar
                        });
                    });
                }
                
                console.log(`🎭 Loaded ${this.avatarDatabase.size} avatars in database`);
            } else {
                console.warn('Failed to load avatar database:', response.status);
            }
        } catch (error) {
            console.error('Error loading avatar database:', error);
        }
    }

    displayChatHistory() {
        // Display recent chat history in the chat window
        if (!this.chatHistory || this.chatHistory.length === 0) return;
        
        // Clear existing messages first
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            
            // Show last 10 messages to avoid overwhelming the interface
            const recentHistory = this.chatHistory.slice(-10);
            
            // Add a separator for history
            if (recentHistory.length > 0) {
                const separator = document.createElement('div');
                separator.className = 'chat-separator';
                separator.innerHTML = '<span>— Previous Conversation —</span>';
                chatMessagesContainer.appendChild(separator);
            }
            
            // Display each historical message with proper speaker identification
            recentHistory.forEach(msg => {
                this.addMessageToUI(msg, true); // true indicates it's historical
            });
            
            // Add separator for new conversation
            if (recentHistory.length > 0) {
                const separator = document.createElement('div');
                separator.className = 'chat-separator';
                separator.innerHTML = '<span>— Current Session —</span>';
                chatMessagesContainer.appendChild(separator);
            }
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
            // Listen for model loaded events
            document.addEventListener('live2dModelLoaded', (event) => {
                console.log('🎭 Received live2dModelLoaded event:', event.detail);
                this.handleModelLoaded(event.detail);
            });
            
            // Listen for model removed events
            document.addEventListener('live2dModelRemoved', (event) => {
                console.log('🎭 Received live2dModelRemoved event:', event.detail);
                this.handleModelRemoved(event.detail);
            });
        } else {
            console.warn('⚠️ Live2D multi model manager not available, setting up polling fallback');
        }
        
        // Listen for user changes from the user selection system
        document.addEventListener('userChanged', (event) => {
            console.log('👤 User changed event received:', event.detail);
            this.currentUser = event.detail.user;
            this.loadUserProfile();
            this.loadChatHistory();
        });
        
        // FALLBACK: Also check for models via polling as backup (less frequent)
        setInterval(() => {
            this.updateActiveAvatars();
        }, 30000); // Check every 30 seconds as fallback
    }

    handleModelLoaded(modelDetail) {
        console.log('🎭 === HANDLING MODEL LOADED EVENT ===');
        console.log('Model detail received:', modelDetail);
        
        // Clear chat messages when first model loads - always clear for fresh start
        if (this.activeAvatars.size === 0) {
            console.log('🧹 Clearing chat for fresh avatar session...');
            this.clearChatWindow();
        }
        
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
                console.log('✅ Added pixiModel reference to avatar info');
            } else {
                console.warn('⚠️ No pixiModel found in modelData');
            }
            
            // Trigger autonomous greeting for the newly loaded avatar
            const delay = 2000 + Math.random() * 3000; // 2-5 seconds for natural feel
            console.log(`👋 Scheduling autonomous greeting for ${avatarInfo.displayName} in ${delay.toFixed(0)}ms`);
            
            setTimeout(() => {
                this.sendAutonomousGreeting(avatarInfo);
            }, delay);
        } else {
            console.warn('⚠️ Invalid model detail received:', modelDetail);
        }
        console.log('🎭 === END MODEL LOADED HANDLING ===');
    }

    handleModelRemoved(modelDetail) {
        console.log('🎭 Handling model removed:', modelDetail);
        this.updateActiveAvatars();
        
        // Clear chat if no avatars remain
        if (this.activeAvatars.size === 0) {
            this.clearChatWindow();
        }
    }

    clearChatWindow() {
        console.log('🧹 Clearing chat window for new session...');
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (chatMessagesContainer) {
            chatMessagesContainer.innerHTML = '';
            console.log('✅ Chat messages container cleared');
            
            // Clear message history as well for fresh start
            this.messageHistory = [];
            console.log('✅ Message history cleared');
            
            // Add welcome message only if avatars are expected
            if (this.activeAvatars.size > 0 || window.live2dMultiModelManager?.getAllModels()?.length > 0) {
                const welcomeMsg = {
                    message: 'Welcome! Your avatars are ready to chat.',
                    type: 'system',
                    timestamp: new Date().toISOString()
                };
                this.addMessageToUI(welcomeMsg);
            } else {
                console.log('ℹ️ No avatars detected, skipping welcome message');
            }
        }
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
        
        // Store previous state to avoid redundant logging
        const previousActiveAvatars = new Set(this.activeAvatars.keys());
        
        // Only log when there are actually models to check
        if (allModels.length > 0) {
            console.log('🔍 Checking all Live2D models:', allModels.length);
        }
        
        allModels.forEach((modelData, index) => {
            // Only log individual model details if there's a change or it's the first check
            if (this.activeAvatars.size === 0 || !this.activeAvatars.has(modelData.name)) {
                console.log(`🎭 Model ${index + 1}:`, {
                    name: modelData.name,
                    visible: modelData.pixiModel?.visible,
                    alpha: modelData.pixiModel?.alpha,
                    hasPixiModel: !!modelData.pixiModel
                });
            }
            
            // Check if model exists and is visible 
            // Note: Some Live2D models might not have alpha property or default to 1
            const isVisible = modelData.pixiModel && 
                             (modelData.pixiModel.visible === true || modelData.pixiModel.visible === undefined) &&
                             (modelData.pixiModel.alpha === undefined || modelData.pixiModel.alpha > 0);
            
            if (isVisible) {
                const avatarData = this.avatarDatabase.get(modelData.name) || {
                    id: modelData.name,
                    name: modelData.name,
                    displayName: this.formatAvatarName(modelData.name)
                };
                
                // Add the pixiModel reference
                avatarData.pixiModel = modelData.pixiModel;
                
                currentActive.set(modelData.name, avatarData);
            }
        });

        // Check if the active avatars have actually changed
        const currentActiveAvatars = new Set(currentActive.keys());
        const hasChanges = previousActiveAvatars.size !== currentActiveAvatars.size ||
                          Array.from(previousActiveAvatars).some(id => !currentActiveAvatars.has(id)) ||
                          Array.from(currentActiveAvatars).some(id => !previousActiveAvatars.has(id));

        // Update active avatars map
        this.activeAvatars = currentActive;
        
        // Update interaction manager with new active avatars
        if (this.interactionManager) {
            this.interactionManager.updateActiveAvatars(this.activeAvatars);
        }
        
        // Only log updates when there are actual changes
        if (hasChanges || this.activeAvatars.size === 0) {
            console.log('🎭 Updated active avatars:', this.activeAvatars.size, Array.from(this.activeAvatars.keys()));
            
            // Clear chat if no avatars are active
            if (this.activeAvatars.size === 0) {
                console.log('🧹 No active avatars, clearing chat window');
                this.clearChatWindow();
            }
        }
        
        // Update UI if needed
        this.updateChatUI();
        
        // Notify autonomous system about avatar changes (only if there are changes)
        if (hasChanges) {
            this.notifyAutonomousSystem();
        }
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
                const delay = (index + 1) * 1000 + Math.random() * 2000; // Stagger greetings
                setTimeout(() => {
                    const fullAvatar = this.activeAvatars.get(avatar.id);
                    if (fullAvatar) {
                        this.sendAutonomousGreeting(fullAvatar);
                    }
                }, delay);
            });
        }
    }

    // Enhanced sendAutonomousGreeting using modular system
    async sendAutonomousGreeting(avatar) {
        console.log('👋 === SENDING MODULAR AUTONOMOUS GREETING ===');
        console.log('Avatar info:', avatar);
        
        if (!this.personalityManager || !this.responseManager) {
            console.error('❌ Required modules not available for greeting generation');
            this.sendFallbackGreeting(avatar);
            return;
        }

        try {
            // Check personality - shy avatars might not greet immediately
            const personalityTraits = await this.personalityManager.getAvatarPersonalityTraits(avatar.id);
            const behavioralConstraints = await this.personalityManager.calculateBehavioralConstraints(avatar.id, { 
                context: 'greeting'
            });
            
            console.log('🧠 Personality traits:', personalityTraits);
            console.log('🎯 Behavioral constraints:', behavioralConstraints);
            
            // Check if avatar should greet based on analysis
            if (!this.shouldAvatarGreet(personalityTraits, behavioralConstraints)) {
                console.log(`🤐 ${avatar.displayName} chooses not to greet based on personality analysis`);
                return;
            }
            
            // Generate AI-based greeting using response manager
            const greetingResponse = await this.responseManager.generateAutonomousMessage(avatar, 'greeting', {
                context: 'Avatar just loaded and is greeting the user',
                intent: 'welcome_user',
                emotion: 'friendly'
            });
            
            console.log('💬 Generated modular greeting:', greetingResponse);
            
            if (greetingResponse && greetingResponse.message) {
                // Add the greeting to the chat
                this.addMessageToUI({
                    ...greetingResponse,
                    avatar: avatar,
                    type: 'avatar'
                });
                
                // Record interaction
                if (this.interactionManager) {
                    this.interactionManager.recordInteraction(
                        avatar.id, 
                        null, 
                        'autonomous_greeting', 
                        { greeting_type: 'initial' }
                    );
                }
                
                // Trigger TTS and animation if available
                await this.executeSynchronizedAvatarResponse(avatar, greetingResponse);
                
            } else {
                console.warn('⚠️ No greeting generated, using fallback');
                this.sendFallbackGreeting(avatar);
            }
            
        } catch (error) {
            console.error('❌ Error sending modular autonomous greeting:', error);
            this.sendFallbackGreeting(avatar);
        }
        
        console.log('👋 === END MODULAR AUTONOMOUS GREETING ===');
    }

    shouldAvatarGreet(personalityTraits, behavioralConstraints) {
        // Simplified greeting decision logic
        
        // Shy or introverted avatars may not greet immediately
        if (personalityTraits.extroversion < 0.3 && Math.random() < 0.4) {
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
        
        return true; // Avatar should greet
    }

    sendFallbackGreeting(avatar) {
        const avatarName = avatar.displayName || avatar.name;
        const fallbackGreetings = [
            `Hello! I'm ${avatarName}. Nice to meet you!`,
            `Hi there! ${avatarName} here. How are you doing today?`,
            `Hey! It's ${avatarName}. Great to see you!`,
            `Hello! ${avatarName} at your service. How can I help you today?`,
            `Greetings! I'm ${avatarName}. What would you like to talk about?`
        ];
        
        const greeting = fallbackGreetings[Math.floor(Math.random() * fallbackGreetings.length)];
        
        this.addMessageToUI({
            message: greeting,
            avatar: avatar,
            type: 'avatar',
            timestamp: new Date().toISOString(),
            generated_by: 'fallback'
        });
    }

    async executeSynchronizedAvatarResponse(avatar, response) {
        console.log('🎭 Executing synchronized avatar response...');
        
        // Trigger Live2D motion if available
        if (avatar.pixiModel && typeof triggerAvatarMotion === 'function') {
            console.log('🎭 Triggering Live2D motion...');
            try {
                triggerAvatarMotion(avatar.pixiModel, response.emotional_tone || 'happy');
            } catch (error) {
                console.warn('⚠️ Error triggering Live2D motion:', error);
            }
        }
        
        // Trigger TTS if available
        if (typeof triggerEmotionalTTS === 'function' && response.message) {
            console.log('🔊 Triggering TTS...');
            try {
                const avatarId = response.avatar_id || this.currentAvatarId || 'default';
                const emotion = response.emotional_tone || 'neutral';
                const personalityTraits = response.personality_expression || {};
                const intensity = response.emotional_intensity || 0.5;
                
                triggerEmotionalTTS(
                    response.message, 
                    emotion, 
                    avatarId, 
                    personalityTraits, 
                    intensity
                );
            } catch (error) {
                console.warn('⚠️ Error triggering TTS:', error);
            }
        }
        
        console.log('✅ Synchronized avatar response execution complete');
    }

    // User message handling using modular system
    async handleUserMessage(userMessage) {
        console.log('💬 === HANDLING USER MESSAGE ===');
        console.log('User message:', userMessage);

        if (!userMessage || !userMessage.trim()) {
            console.warn('⚠️ Empty user message received');
            return;
        }

        // Add user message to UI and history
        const userMessageObj = {
            message: userMessage,
            type: 'user',
            timestamp: new Date().toISOString(),
            user: this.currentUser
        };

        this.addMessageToUI(userMessageObj);
        this.messageHistory.push(userMessageObj);

        // Update conversation manager with new message
        if (this.conversationManager) {
            this.conversationManager.updateMessageHistory([...this.chatHistory, ...this.messageHistory]);
        }

        // Determine which avatar should respond
        if (!this.interactionManager) {
            console.error('❌ Interaction manager not available');
            return;
        }

        const respondingAvatar = await this.interactionManager.determineResponder(userMessage, {
            context: 'user_message',
            user: this.currentUser
        });

        if (!respondingAvatar) {
            console.warn('⚠️ No avatar available to respond');
            return;
        }

        console.log(`🎯 ${respondingAvatar.displayName} will respond to user message`);

        // Generate response using response manager
        try {
            const response = await this.responseManager.generateAutonomousMessage(respondingAvatar, 'response', {
                context: 'responding_to_user',
                user_message: userMessage,
                conversation_history: this.messageHistory.slice(-5)
            });

            if (response && response.message) {
                // Add response to UI
                this.addMessageToUI({
                    ...response,
                    avatar: respondingAvatar,
                    type: 'avatar'
                });

                // Record interaction
                this.interactionManager.recordInteraction(
                    respondingAvatar.id,
                    this.currentUser?.id,
                    'user_response',
                    { user_message: userMessage }
                );

                // Execute synchronized response (TTS, animation)
                await this.executeSynchronizedAvatarResponse(respondingAvatar, response);

                // Check for additional avatar interactions
                const additionalInteractions = await this.interactionManager.checkForAvatarToAvatarInteractions(
                    userMessage,
                    respondingAvatar
                );

                // Execute additional interactions with delays
                this.executeAdditionalInteractions(additionalInteractions);

            } else {
                console.warn('⚠️ No response generated for user message');
            }

        } catch (error) {
            console.error('❌ Error generating response to user message:', error);
        }

        console.log('💬 === END USER MESSAGE HANDLING ===');
    }

    async executeAdditionalInteractions(interactions) {
        if (!interactions || interactions.length === 0) return;

        console.log(`🎭 Executing ${interactions.length} additional avatar interactions`);

        for (const interaction of interactions) {
            setTimeout(async () => {
                try {
                    const response = await this.responseManager.generateAutonomousMessage(
                        interaction.avatar,
                        'interaction',
                        {
                            context: 'avatar_to_avatar',
                            interaction_type: interaction.interaction_type
                        }
                    );

                    if (response && response.message) {
                        this.addMessageToUI({
                            ...response,
                            avatar: interaction.avatar,
                            type: 'avatar'
                        });

                        this.interactionManager.recordInteraction(
                            interaction.avatar.id,
                            null,
                            interaction.interaction_type,
                            { triggered_by: 'avatar_interaction' }
                        );

                        await this.executeSynchronizedAvatarResponse(interaction.avatar, response);
                    }
                } catch (error) {
                    console.error(`❌ Error executing additional interaction for ${interaction.avatar.displayName}:`, error);
                }
            }, interaction.delay);
        }
    }

    // UI Management methods
    addMessageToUI(messageObj, isHistorical = false) {
        console.log('🎯 addMessageToUI called with:', { messageObj, isHistorical });
        
        const chatMessagesContainer = document.getElementById('chatMessages');
        if (!chatMessagesContainer) {
            console.warn('⚠️ Chat messages container not found');
            return;
        }

        console.log('✅ Chat messages container found:', chatMessagesContainer);
        
        const messageElement = this.createMessageElement(messageObj, isHistorical);
        console.log('📝 Created message element:', messageElement);
        
        chatMessagesContainer.appendChild(messageElement);
        console.log('➕ Message element appended to container');

        // Add visible class with animation delay
        requestAnimationFrame(() => {
            messageElement.classList.add('visible');
            console.log('✨ Added visible class for animation');
        });

        // Scroll to bottom for new messages (not historical)
        if (!isHistorical) {
            setTimeout(() => {
                chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
                console.log('📜 Scrolled chat to bottom');
            }, 100); // Small delay to allow animation
        }
        
        console.log('✅ addMessageToUI completed successfully');
    }

    createMessageElement(messageObj, isHistorical = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${messageObj.type}-message${isHistorical ? ' historical' : ''}`;

        // Create speaker label
        const speakerSpan = document.createElement('span');
        speakerSpan.className = 'speaker-label';
        
        if (messageObj.type === 'avatar') {
            speakerSpan.textContent = messageObj.avatar?.displayName || messageObj.avatar?.name || 'Avatar';
            speakerSpan.className += ' avatar-speaker';
        } else if (messageObj.type === 'user') {
            speakerSpan.textContent = messageObj.user?.display_name || 'User';
            speakerSpan.className += ' user-speaker';
        } else {
            speakerSpan.textContent = 'System';
            speakerSpan.className += ' system-speaker';
        }

        // Create message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = messageObj.message;

        // Create timestamp
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'message-timestamp';
        const timestamp = new Date(messageObj.timestamp);
        timestampSpan.textContent = timestamp.toLocaleTimeString();

        // Add generation info for debugging (only in development)
        if (messageObj.generated_by && window.location.hostname === 'localhost') {
            const debugSpan = document.createElement('span');
            debugSpan.className = 'debug-info';
            debugSpan.textContent = `[${messageObj.generated_by}]`;
            timestampSpan.appendChild(debugSpan);
        }

        messageDiv.appendChild(speakerSpan);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timestampSpan);

        return messageDiv;
    }

    updateChatUI() {
        // Update any UI elements that depend on active avatars
        const avatarCount = this.activeAvatars.size;
        
        // Update avatar counter if it exists
        const avatarCountElement = document.getElementById('activeAvatarCount');
        if (avatarCountElement) {
            avatarCountElement.textContent = avatarCount;
        }

        // Update chat input placeholder
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            if (avatarCount === 0) {
                chatInput.placeholder = 'Load an avatar to start chatting...';
                chatInput.disabled = true;
            } else if (avatarCount === 1) {
                const avatarName = Array.from(this.activeAvatars.values())[0].displayName;
                chatInput.placeholder = `Chat with ${avatarName}...`;
                chatInput.disabled = false;
            } else {
                chatInput.placeholder = `Chat with ${avatarCount} avatars...`;
                chatInput.disabled = false;
            }
        }
    }

    // Utility methods
    getActiveAvatars() {
        return Array.from(this.activeAvatars.values());
    }

    getAvatarById(avatarId) {
        return this.activeAvatars.get(avatarId);
    }

    getInteractionStats() {
        if (this.interactionManager) {
            return this.interactionManager.getInteractionStats();
        }
        return null;
    }

    // Debug and maintenance methods
    async refreshAllData() {
        console.log('🔄 Refreshing all chat data...');
        
        await this.loadCurrentUser();
        await this.loadAvatarDatabase();
        await this.loadChatHistory();
        this.updateActiveAvatars();
        
        console.log('✅ All chat data refreshed');
    }

    clearAllCaches() {
        console.log('🧹 Clearing all caches...');
        
        if (window.chatSystemModules) {
            window.chatSystemModules.clearAllCaches();
        }
        
        this.messageHistory = [];
        this.chatHistory = [];
        
        console.log('✅ All caches cleared');
    }

    // Public API for external integration
    async sendMessage(message) {
        return this.handleUserMessage(message);
    }

    async triggerAvatarGreeting(avatarId) {
        const avatar = this.activeAvatars.get(avatarId);
        if (avatar) {
            return this.sendAutonomousGreeting(avatar);
        } else {
            console.warn(`⚠️ Avatar ${avatarId} not found or not active`);
        }
    }

    getSystemStatus() {
        return {
            activeAvatars: this.activeAvatars.size,
            currentUser: this.currentUser?.display_name || null,
            messageHistory: this.messageHistory.length,
            chatHistory: this.chatHistory.length,
            modulesLoaded: !!(this.personalityManager && this.conversationManager && this.responseManager && this.interactionManager),
            interactionStats: this.getInteractionStats()
        };
    }
}

// Export for global access
window.AvatarChatManager = AvatarChatManager;

// Global sendMessage function for chat input functionality
async function sendMessage() {
    console.log('📤 Global sendMessage called');
    
    // Get chat input element
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) {
        console.error('Chat input element not found! Looking for element with ID: chatInput');
        return;
    }
    
    const text = chatInput.value.trim();
    if (!text) {
        console.log('Empty message, not sending');
        return;
    }
    
    console.log('📤 Sending message:', text);
    
    // Clear input immediately
    chatInput.value = '';
    
    // Initialize avatar chat manager if not already done
    if (!window.avatarChatManager) {
        console.log('Initializing avatar chat manager...');
        window.avatarChatManager = new AvatarChatManager();
        // Give it a moment to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Add user message to chat
    const userMessageObj = {
        type: 'user',
        message: text,
        timestamp: new Date(),
        user: window.avatarChatManager.currentUser || { display_name: 'User' },
        generated_by: 'manual'
    };
    
    window.avatarChatManager.addMessageToUI(userMessageObj);
    
    try {
        // Send message to backend for AI response
        const apiUrl = window.ai2d_chat_CONFIG?.API_BASE_URL || '';
        const response = await fetch(`${apiUrl}/api/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: text,
                user_id: window.avatarChatManager.currentUser?.id || 1
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Add AI response to chat
            const aiMessageObj = {
                type: 'avatar',
                message: data.reply || data.response || '[No reply]',
                timestamp: new Date(),
                avatar: { 
                    id: 'assistant', 
                    name: 'Assistant', 
                    displayName: 'AI Assistant' 
                },
                generated_by: 'api_response',
                emotion: data.emotion || 'neutral'
            };
            
            window.avatarChatManager.addMessageToUI(aiMessageObj);
            
            console.log('✅ Message sent and response received');
        } else {
            console.error('Chat API request failed:', response.status);
            
            // Add error message
            const errorMessageObj = {
                type: 'system',
                message: 'Failed to get response from AI assistant',
                timestamp: new Date(),
                generated_by: 'error'
            };
            
            window.avatarChatManager.addMessageToUI(errorMessageObj);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Add error message
        const errorMessageObj = {
            type: 'system',
            message: 'Error: Could not send message',
            timestamp: new Date(),
            generated_by: 'error'
        };
        
        window.avatarChatManager.addMessageToUI(errorMessageObj);
    }
}

// Also handle Enter key in chat input
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}

// Make functions globally available
window.sendMessage = sendMessage;
window.handleChatKeyPress = handleChatKeyPress;

// Global addMessage function for backwards compatibility with autonomous system
function addMessage(sender, message, type = 'info', avatar = null, metadata = null) {
    // Bridge to current chat manager's addMessageToUI method
    console.log('🔗 Global addMessage called - bridging to chat manager');
    console.log('📝 addMessage parameters:', { sender, message, type, avatar, metadata });
    
    if (!window.avatarChatManager) {
        console.warn('⚠️ Avatar chat manager not initialized, creating new instance');
        window.avatarChatManager = new AvatarChatManager();
    }
    
    console.log('🎯 Avatar chat manager available:', !!window.avatarChatManager);
    console.log('🎯 addMessageToUI method available:', typeof window.avatarChatManager.addMessageToUI);
    
    // Convert old addMessage format to new addMessageToUI format
    const messageObj = {
        type: sender === 'user' ? 'user' : (sender === 'ai' ? 'avatar' : 'system'),
        message: message,
        timestamp: metadata?.timestamp ? new Date(metadata.timestamp) : new Date(),
        avatar: avatar,
        user: sender === 'user' ? (window.avatarChatManager.currentUser || { display_name: 'User' }) : null,
        generated_by: metadata?.is_autonomous ? 'autonomous' : metadata?.is_self_reflection ? 'reflection' : 'manual',
        emotion: metadata?.emotion || 'neutral',
        metadata: metadata
    };
    
    console.log('📦 Converted message object:', messageObj);
    
    // Use the current chat manager's method
    try {
        window.avatarChatManager.addMessageToUI(messageObj, false);
        console.log('✅ Message bridged to chat manager successfully');
    } catch (error) {
        console.error('❌ Error calling addMessageToUI:', error);
    }
}

// Make addMessage globally available
window.addMessage = addMessage;

// Debug: Log function availability after all functions are defined
console.log('✅ Global chat functions exposed:', {
    sendMessage: typeof window.sendMessage,
    handleChatKeyPress: typeof window.handleChatKeyPress,
    addMessage: typeof window.addMessage
});

// Debug function for testing chat UI - call from browser console: testChatUI()
function testChatUI() {
    console.log('🧪 Testing chat UI functionality...');
    
    // Check if container exists
    const container = document.getElementById('chatMessages');
    console.log('📦 Chat container found:', !!container);
    
    if (container) {
        console.log('📏 Container dimensions:', {
            width: container.offsetWidth,
            height: container.offsetHeight,
            childCount: container.children.length
        });
        
        // Check existing messages
        const messages = container.querySelectorAll('.chat-message');
        console.log('💬 Existing messages:', messages.length);
        messages.forEach((msg, i) => {
            console.log(`Message ${i}:`, {
                text: msg.textContent.substring(0, 50),
                visible: msg.classList.contains('visible'),
                opacity: getComputedStyle(msg).opacity
            });
        });
        
        // Try adding a test message directly
        const testDiv = document.createElement('div');
        testDiv.className = 'chat-message test-message';
        testDiv.textContent = '🧪 TEST MESSAGE - If you see this, DOM manipulation works!';
        testDiv.style.cssText = 'background: yellow; color: black; padding: 10px; margin: 5px; border: 2px solid red;';
        container.appendChild(testDiv);
        requestAnimationFrame(() => {
            testDiv.classList.add('visible');
        });
        console.log('✅ Test message added to DOM');
        
        // Try the official addMessage function
        console.log('🔄 Testing addMessage function...');
        addMessage('Test User', '🧪 Testing addMessage function', 'test');
    }
}

// Make test function globally available
window.testChatUI = testChatUI;
