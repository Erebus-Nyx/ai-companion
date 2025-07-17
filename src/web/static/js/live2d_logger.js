// Live2D Logger - Unified logging system
class Live2DLogger {
    constructor(config) {
        this.config = config || { debugMode: true }; // Fallback config
        this.logHistory = [];
    }

    log(message, type = 'info') {
        if (!this.config.debugMode && type === 'info') {
            return;
        }

        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
        
        this.logHistory.push(logMessage);
        
        switch (type) {
            case 'error':
                console.error(logMessage);
                break;
            case 'warning':
                console.warn(logMessage);
                break;
            case 'success':
                console.log(`%c${logMessage}`, 'color: #28a745;');
                break;
            default:
                console.log(logMessage);
        }
    }

    logInfo(message) {
        this.log(message, 'info');
    }

    logWarning(message) {
        this.log(message, 'warning');
    }

    logError(message) {
        this.log(message, 'error');
    }

    logSuccess(message) {
        this.log(message, 'success');
    }

    getHistory() {
        return this.logHistory;
    }

    clearHistory() {
        this.logHistory = [];
    }
}

// Export for modular use
window.Live2DLogger = Live2DLogger;
