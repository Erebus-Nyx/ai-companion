// Live2D Logger - Unified logging system
class Live2DLogger {
    constructor(logElementId = null) {
        this.logElement = logElementId ? document.getElementById(logElementId) : null;
        this.logs = [];
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString().split('T')[1].substring(0, 8);
        const logEntry = {
            timestamp,
            message,
            type
        };
        
        this.logs.push(logEntry);
        
        if (this.logElement) {
            const className = type === 'error' ? 'error' : 
                             type === 'success' ? 'success' : 
                             type === 'warning' ? 'warning' : '';
            
            this.logElement.innerHTML += `<div class="${className}">[${timestamp}] ${message}</div>`;
            this.logElement.scrollTop = this.logElement.scrollHeight;
        }
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    clear() {
        this.logs = [];
        if (this.logElement) {
            this.logElement.innerHTML = '';
        }
    }

    copyToClipboard() {
        const logText = this.logs.map(entry => 
            `[${entry.timestamp}] ${entry.message}`
        ).join('\n');
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(logText).then(() => {
                this.log('Log copied to clipboard!', 'success');
            }).catch(err => {
                this.log('Failed to copy log: ' + err, 'error');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = logText;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                this.log('Log copied to clipboard!', 'success');
            } catch (err) {
                this.log('Failed to copy log: ' + err, 'error');
            }
            document.body.removeChild(textArea);
        }
    }

    getLogs() {
        return this.logs;
    }

    getLogText() {
        return this.logs.map(entry => 
            `[${entry.timestamp}] ${entry.message}`
        ).join('\n');
    }
}

// Export for use in other modules
window.Live2DLogger = Live2DLogger;
