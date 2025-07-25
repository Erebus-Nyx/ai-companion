// Console Logger - Captures browser console output and sends to backend
class ConsoleLogger {
    constructor() {
        this.logBuffer = [];
        this.maxBufferSize = 100;
        this.flushInterval = 5000; // 5 seconds
        this.isEnabled = true;
        
        this.initializeConsoleCapture();
        this.startPeriodicFlush();
        
        console.log('📝 Console Logger initialized - capturing logs to backend');
    }
    
    initializeConsoleCapture() {
        // Store original console methods
        this.originalConsole = {
            log: console.log.bind(console),
            info: console.info.bind(console),
            warn: console.warn.bind(console),
            error: console.error.bind(console),
            debug: console.debug.bind(console)
        };
        
        // Override console methods
        console.log = (...args) => {
            this.originalConsole.log(...args);
            this.captureLog('log', args);
        };
        
        console.info = (...args) => {
            this.originalConsole.info(...args);
            this.captureLog('info', args);
        };
        
        console.warn = (...args) => {
            this.originalConsole.warn(...args);
            this.captureLog('warn', args);
        };
        
        console.error = (...args) => {
            this.originalConsole.error(...args);
            this.captureLog('error', args);
        };
        
        console.debug = (...args) => {
            this.originalConsole.debug(...args);
            this.captureLog('debug', args);
        };
        
        // Capture unhandled errors
        window.addEventListener('error', (event) => {
            this.captureLog('error', [`Unhandled Error: ${event.error?.message || event.message}`, event.error?.stack || event.filename + ':' + event.lineno]);
        });
        
        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.captureLog('error', [`Unhandled Promise Rejection: ${event.reason}`]);
        });
    }
    
    captureLog(level, args) {
        if (!this.isEnabled) return;
        
        try {
            // Convert arguments to strings, handling objects
            const message = args.map(arg => {
                if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg, null, 2);
                    } catch (e) {
                        return String(arg);
                    }
                }
                return String(arg);
            }).join(' ');
            
            const logEntry = {
                timestamp: new Date().toISOString(),
                level: level,
                message: message,
                url: window.location.href,
                userAgent: navigator.userAgent.substring(0, 100) // Truncate for brevity
            };
            
            // Add to buffer
            this.logBuffer.push(logEntry);
            
            // Flush if buffer is full
            if (this.logBuffer.length >= this.maxBufferSize) {
                this.flushLogs();
            }
            
        } catch (error) {
            // Avoid infinite recursion by using original console
            this.originalConsole.error('Console logger error:', error);
        }
    }
    
    async flushLogs() {
        if (this.logBuffer.length === 0) return;
        
        const logsToSend = [...this.logBuffer];
        this.logBuffer = [];
        
        try {
            // Ensure server configuration is loaded
            if (typeof loadServerConfig === 'function' && !window.ai2d_chat_CONFIG?._configLoaded) {
                try {
                    await loadServerConfig();
                } catch (error) {
                    this.originalConsole.warn('Failed to load server config in console logger:', error);
                }
            }
            
            // Always use relative URLs for proxy compatibility
            const apiBaseUrl = '';
            
            const response = await fetch(`${apiBaseUrl}/api/logs/frontend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    logs: logsToSend,
                    session_id: this.getSessionId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to send logs: ${response.status}`);
            }
            
        } catch (error) {
            // Re-add logs to buffer if sending failed
            this.logBuffer.unshift(...logsToSend);
            
            // Limit buffer size to prevent memory issues
            if (this.logBuffer.length > this.maxBufferSize * 2) {
                this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
            }
            
            // Only log error once per minute to avoid spam
            const now = Date.now();
            if (!this.lastLogError || (now - this.lastLogError) > 60000) {
                this.lastLogError = now;
                this.originalConsole.warn('Failed to send console logs to backend - will retry silently');
            }
        }
    }
    
    startPeriodicFlush() {
        setInterval(() => {
            this.flushLogs();
        }, this.flushInterval);
        
        // Also flush on page unload
        window.addEventListener('beforeunload', () => {
            // Use sendBeacon for reliable delivery during page unload
            if (this.logBuffer.length > 0 && navigator.sendBeacon) {
                try {
                    // Always use relative URLs for proxy compatibility
                    const apiBaseUrl = '';
                    const data = JSON.stringify({
                        logs: this.logBuffer,
                        session_id: this.getSessionId()
                    });
                    
                    navigator.sendBeacon(`${apiBaseUrl}/api/logs/frontend`, data);
                } catch (error) {
                    this.originalConsole.warn('Failed to send logs on page unload:', error);
                }
            }
        });
    }
    
    getSessionId() {
        // Create or get session ID for log correlation
        let sessionId = sessionStorage.getItem('console_logger_session');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('console_logger_session', sessionId);
        }
        return sessionId;
    }
    
    disable() {
        this.isEnabled = false;
        this.originalConsole.log('📝 Console logging disabled');
    }
    
    enable() {
        this.isEnabled = true;
        this.originalConsole.log('📝 Console logging enabled');
    }
    
    // Manual log method for important events
    logEvent(event, data = {}) {
        this.captureLog('info', [`[EVENT] ${event}`, JSON.stringify(data)]);
    }
    
    // Download logs as file (for debugging)
    downloadLogs() {
        try {
            const allLogs = JSON.stringify(this.logBuffer, null, 2);
            const blob = new Blob([allLogs], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `console_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.originalConsole.log('📥 Console logs downloaded');
        } catch (error) {
            this.originalConsole.error('Failed to download logs:', error);
        }
    }
}

// Initialize console logger when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.consoleLogger) {
        window.consoleLogger = new ConsoleLogger();
        
        // Add global functions for manual control
        window.disableConsoleLogging = () => window.consoleLogger.disable();
        window.enableConsoleLogging = () => window.consoleLogger.enable();
        window.downloadConsoleLogs = () => window.consoleLogger.downloadLogs();
        window.flushConsoleLogs = () => window.consoleLogger.flushLogs();
        
        // Log important events
        window.consoleLogger.logEvent('PAGE_LOADED', {
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    }
});

// Initialize immediately if DOM already loaded
if (document.readyState === 'loading') {
    // Already set up the event listener above
} else {
    if (!window.consoleLogger) {
        window.consoleLogger = new ConsoleLogger();
        window.disableConsoleLogging = () => window.consoleLogger.disable();
        window.enableConsoleLogging = () => window.consoleLogger.enable();
        window.downloadConsoleLogs = () => window.consoleLogger.downloadLogs();
        window.flushConsoleLogs = () => window.consoleLogger.flushLogs();
    }
}
