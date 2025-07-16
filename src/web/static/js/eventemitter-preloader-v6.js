// EventEmitter Preloader for PIXI v6 and Live2D compatibility
// This must be loaded BEFORE pixi-live2d-display
(function() {
    'use strict';
    
    console.log('EventEmitter Preloader (PIXI v6) loading...');
    
    // Simple EventEmitter implementation for PIXI v6 compatibility
    class EventEmitter {
        constructor() {
            this._events = {};
            this._maxListeners = 10;
        }
        
        on(event, listener) {
            if (!this._events[event]) {
                this._events[event] = [];
            }
            this._events[event].push(listener);
            return this;
        }
        
        addListener(event, listener) {
            return this.on(event, listener);
        }
        
        once(event, listener) {
            const onceWrapper = (...args) => {
                this.removeListener(event, onceWrapper);
                listener.apply(this, args);
            };
            return this.on(event, onceWrapper);
        }
        
        removeListener(event, listener) {
            if (!this._events[event]) return this;
            
            const index = this._events[event].indexOf(listener);
            if (index !== -1) {
                this._events[event].splice(index, 1);
            }
            
            if (this._events[event].length === 0) {
                delete this._events[event];
            }
            
            return this;
        }
        
        removeAllListeners(event) {
            if (event) {
                delete this._events[event];
            } else {
                this._events = {};
            }
            return this;
        }
        
        emit(event, ...args) {
            if (!this._events[event]) return false;
            
            const listeners = this._events[event].slice();
            for (let listener of listeners) {
                listener.apply(this, args);
            }
            
            return true;
        }
        
        listeners(event) {
            return this._events[event] ? this._events[event].slice() : [];
        }
        
        listenerCount(event) {
            return this._events[event] ? this._events[event].length : 0;
        }
        
        setMaxListeners(n) {
            this._maxListeners = n;
            return this;
        }
        
        getMaxListeners() {
            return this._maxListeners;
        }
    }
    
    // Make EventEmitter available globally in multiple ways
    window.EventEmitter = EventEmitter;
    
    // Set up global if it doesn't exist
    if (typeof global === 'undefined') {
        window.global = window;
    }
    
    // Make sure global has EventEmitter
    if (typeof global !== 'undefined') {
        global.EventEmitter = EventEmitter;
    } else {
        window.global = window;
        window.global.EventEmitter = EventEmitter;
    }
    
    // Create events module for require('events')
    const eventsModule = {
        EventEmitter: EventEmitter
    };
    
    // Enhanced require function for PIXI v6 compatibility
    if (typeof require === 'undefined') {
        window.require = function(moduleName) {
            console.log('EventEmitter Preloader: require() called for:', moduleName);
            if (moduleName === 'events') {
                return eventsModule;
            }
            if (moduleName === 'eventemitter3') {
                return EventEmitter;
            }
            // Return empty object for unknown modules
            return {};
        };
    }
    
    // Override the original require if it exists but doesn't handle 'events'
    const originalRequire = window.require;
    window.require = function(moduleName) {
        console.log('EventEmitter Preloader: require() called for:', moduleName);
        if (moduleName === 'events') {
            return eventsModule;
        }
        if (moduleName === 'eventemitter3') {
            return EventEmitter;
        }
        if (originalRequire) {
            try {
                return originalRequire(moduleName);
            } catch (e) {
                console.log('Original require failed, returning empty object for:', moduleName);
                return {};
            }
        }
        return {};
    };
    
    // Make events available as a global property
    window.events = eventsModule;
    
    // Also make it available in the exact way pixi-live2d-display expects
    if (typeof global !== 'undefined') {
        global.events = eventsModule;
        global.require = window.require;
    }
    
    // Direct EventEmitter availability for different access patterns
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = EventEmitter;
        module.exports.EventEmitter = EventEmitter;
    }
    
    // Try to set up the exact path the library is looking for
    try {
        const eventsPath = require('events');
        if (eventsPath && eventsPath.EventEmitter) {
            console.log('EventEmitter available via require("events")');
        }
    } catch (e) {
        console.log('Failed to verify require("events"):', e.message);
    }
    
    // Process object for Node.js compatibility
    if (typeof process === 'undefined') {
        window.process = {
            env: { NODE_ENV: 'production' },
            version: 'v16.0.0',
            platform: 'browser'
        };
    }
    
    // Module compatibility
    if (typeof module === 'undefined') {
        window.module = { exports: {} };
    }
    
    console.log('EventEmitter Preloader loaded successfully');
    console.log('EventEmitter available globally:', typeof EventEmitter !== 'undefined');
    console.log('events module available:', typeof window.events !== 'undefined');
})();
