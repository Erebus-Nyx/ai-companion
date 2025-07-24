// Audio Queue Control Panel
class AudioQueueControlPanel {
    constructor() {
        this.isVisible = false;
        this.panelElement = null;
        this.createPanel();
        this.setupEventListeners();
        
        console.log('🎵 Audio Queue Control Panel initialized');
    }
    
    createPanel() {
        this.panelElement = document.createElement('div');
        this.panelElement.id = 'audioQueueControlPanel';
        this.panelElement.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            min-width: 280px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            display: none;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;
        
        this.panelElement.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 16px; color: #ffffff;">🎵 Audio Queue Control</h3>
                <button id="closeAudioPanel" style="background: none; border: none; color: #ffffff; font-size: 18px; cursor: pointer;">×</button>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold;">Queue Mode:</label>
                <select id="audioQueueMode" style="width: 100%; padding: 6px; border-radius: 4px; border: none; background: #333; color: white;">
                    <option value="queue">Queue (Sequential)</option>
                    <option value="interrupt">Interrupt (Replace Current)</option>
                    <option value="priority">Priority (Based on Importance)</option>
                </select>
                <div style="font-size: 12px; color: #ccc; margin-top: 4px;">
                    <div id="queueModeDescription">Queue: Wait for current audio to finish</div>
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold;">Queue Status:</label>
                <div id="queueStatus" style="background: #222; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                    Loading...
                </div>
            </div>
            
            <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                <button id="clearQueue" style="flex: 1; background: #d32f2f; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer;">Clear Queue</button>
                <button id="stopCurrent" style="flex: 1; background: #f57c00; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer;">Stop Current</button>
            </div>
            
            <div style="font-size: 11px; color: #999; line-height: 1.3;">
                <strong>Tips:</strong><br>
                • Queue: Best for natural conversation flow<br>
                • Interrupt: For urgent messages<br>
                • Priority: For mixed-importance scenarios
            </div>
        `;
        
        document.body.appendChild(this.panelElement);
    }
    
    setupEventListeners() {
        // Close button
        document.getElementById('closeAudioPanel').addEventListener('click', () => {
            this.hide();
        });
        
        // Mode selection
        const modeSelect = document.getElementById('audioQueueMode');
        modeSelect.addEventListener('change', (e) => {
            this.setAudioQueueMode(e.target.value);
        });
        
        // Action buttons
        document.getElementById('clearQueue').addEventListener('click', () => {
            this.clearQueue();
        });
        
        document.getElementById('stopCurrent').addEventListener('click', () => {
            this.stopCurrent();
        });
        
        // Update status every 2 seconds
        setInterval(() => {
            this.updateStatus();
        }, 2000);
        
        // Initial status update
        setTimeout(() => {
            this.updateStatus();
        }, 1000);
    }
    
    setAudioQueueMode(mode) {
        if (window.setAudioQueueMode) {
            window.setAudioQueueMode(mode);
            this.updateModeDescription(mode);
            console.log(`🎵 Audio queue mode changed to: ${mode}`);
        }
    }
    
    updateModeDescription(mode) {
        const descriptions = {
            queue: 'Queue: Wait for current audio to finish before playing next',
            interrupt: 'Interrupt: Stop current audio and play new audio immediately',
            priority: 'Priority: High priority audio interrupts, others queue'
        };
        
        const descElement = document.getElementById('queueModeDescription');
        if (descElement) {
            descElement.textContent = descriptions[mode] || 'Unknown mode';
        }
    }
    
    clearQueue() {
        if (window.clearAudioQueue) {
            window.clearAudioQueue();
            console.log('🎵 Audio queue cleared');
            this.updateStatus();
        }
    }
    
    stopCurrent() {
        if (window.stopCurrentAudio) {
            window.stopCurrentAudio();
            console.log('🎵 Current audio stopped');
            this.updateStatus();
        }
    }
    
    updateStatus() {
        const statusElement = document.getElementById('queueStatus');
        if (!statusElement) return;
        
        if (window.getAudioQueueStatus) {
            const status = window.getAudioQueueStatus();
            
            if (status.available === false) {
                statusElement.innerHTML = `
                    <div style="color: #ff9800;">⚠ Audio Queue Manager not available</div>
                `;
                return;
            }
            
            const statusHtml = `
                <div>Playing: <span style="color: ${status.isPlaying ? '#4caf50' : '#f44336'}">${status.isPlaying ? 'Yes' : 'No'}</span></div>
                <div>Current Avatar: <span style="color: #2196f3">${status.currentAvatarId || 'None'}</span></div>
                <div>Queue Length: <span style="color: #ff9800">${status.queueLength || 0}</span></div>
                <div>Mode: <span style="color: #9c27b0">${status.preemptionMode || 'Unknown'}</span></div>
                <div style="margin-top: 6px; font-size: 11px; color: #666;">
                    Total: ${status.stats?.totalRequests || 0} | 
                    Completed: ${status.stats?.completedRequests || 0} | 
                    Interrupted: ${status.stats?.interruptedRequests || 0}
                </div>
            `;
            
            statusElement.innerHTML = statusHtml;
        } else {
            statusElement.innerHTML = `
                <div style="color: #f44336;">⚠ Audio queue functions not available</div>
            `;
        }
    }
    
    show() {
        this.isVisible = true;
        this.panelElement.style.display = 'block';
        this.updateStatus();
        
        // Update current mode in UI
        if (window.getAudioQueueStatus) {
            const status = window.getAudioQueueStatus();
            if (status.preemptionMode) {
                const modeSelect = document.getElementById('audioQueueMode');
                if (modeSelect) {
                    modeSelect.value = status.preemptionMode;
                    this.updateModeDescription(status.preemptionMode);
                }
            }
        }
    }
    
    hide() {
        this.isVisible = false;
        this.panelElement.style.display = 'none';
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

// Create global audio queue control panel
window.audioQueueControlPanel = new AudioQueueControlPanel();

// Global function to toggle panel
window.toggleAudioQueuePanel = function() {
    window.audioQueueControlPanel.toggle();
};

// Export
window.AudioQueueControlPanel = AudioQueueControlPanel;

console.log('🎵 Audio Queue Control Panel loaded');
