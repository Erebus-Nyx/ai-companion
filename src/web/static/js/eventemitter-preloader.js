// Pre-EventEmitter Setup for PIXI v8 Compatibility
// This file MUST be loaded before any other Live2D libraries

(function() {
    'use strict';
    
    // Enhanced EventEmitter class that matches Node.js API
    class EventEmitter {
        constructor() {
            this._events = {};
            this._eventsCount = 0;
            this._maxListeners = 10;
        }
        
        on(event, listener) {
            if (typeof listener !== 'function') {
                throw new TypeError('The listener must be a function');
            }
            
            if (!this._events[event]) {
                this._events[event] = [];
                this._eventsCount++;
            }
            
            this._events[event].push(listener);
            return this;
        }
        
        addListener(event, listener) {
            return this.on(event, listener);
        }
        
        once(event, listener) {
            if (typeof listener !== 'function') {
                throw new TypeError('The listener must be a function');
            }
            
            const onceWrapper = (...args) => {
                this.off(event, onceWrapper);
                listener.apply(this, args);
            };
            
            onceWrapper.listener = listener;
            return this.on(event, onceWrapper);
        }
        
        emit(event, ...args) {
            if (!this._events[event]) return false;
            
            const listeners = this._events[event].slice();
            
            for (const listener of listeners) {
                try {
                    listener.apply(this, args);
                } catch (error) {
                    console.error(`Error in EventEmitter listener for event "${event}":`, error);
                }
            }
            
            return listeners.length > 0;
        }
        
        off(event, listener) {
            if (!this._events[event]) return this;
            
            if (typeof listener === 'undefined') {
                delete this._events[event];
                this._eventsCount--;
                return this;
            }
            
            const listeners = this._events[event];
            for (let i = listeners.length - 1; i >= 0; i--) {
                if (listeners[i] === listener || listeners[i].listener === listener) {
                    listeners.splice(i, 1);
                    if (listeners.length === 0) {
                        delete this._events[event];
                        this._eventsCount--;
                    }
                    break;
                }
            }
            
            return this;
        }
        
        removeListener(event, listener) {
            return this.off(event, listener);
        }
        
        removeAllListeners(event) {
            if (typeof event === 'undefined') {
                this._events = {};
                this._eventsCount = 0;
            } else if (this._events[event]) {
                delete this._events[event];
                this._eventsCount--;
            }
            return this;
        }
        
        listeners(event) {
            return this._events[event] ? this._events[event].slice() : [];
        }
        
        listenerCount(event) {
            return this._events[event] ? this._events[event].length : 0;
        }
        
        eventNames() {
            return Object.keys(this._events);
        }
        
        setMaxListeners(n) {
            this._maxListeners = n;
            return this;
        }
        
        getMaxListeners() {
            return this._maxListeners;
        }
    }
    
    // Install EventEmitter in all possible locations where libraries might expect it
    
    // Global scope
    if (typeof window !== 'undefined') {
        window.EventEmitter = EventEmitter;
    }
    
    if (typeof global !== 'undefined') {
        global.EventEmitter = EventEmitter;
    }
    
    if (typeof globalThis !== 'undefined') {
        globalThis.EventEmitter = EventEmitter;
    }
    
    // Module exports (for libraries that use require)
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = EventEmitter;
        module.exports.EventEmitter = EventEmitter;
    }
    
    if (typeof exports !== 'undefined') {
        exports.EventEmitter = EventEmitter;
    }
    
    // Create a mock require function for 'events' module
    if (typeof window !== 'undefined') {
        window.require = window.require || function(moduleName) {
            if (moduleName === 'events') {
                return { EventEmitter: EventEmitter };
            }
            throw new Error(`Module '${moduleName}' not found`);
        };
        
        // Additional compatibility layers for different library loading patterns
        window.require.resolve = function(moduleName) {
            if (moduleName === 'events') return 'events';
            throw new Error(`Module '${moduleName}' not found`);
        };
        
        // Create a more comprehensive module system
        if (!window.module) {
            window.module = {
                exports: { EventEmitter: EventEmitter },
                require: window.require,
                id: 'events'
            };
        }
        
        // For CommonJS-style access
        if (!window.exports) {
            window.exports = { EventEmitter: EventEmitter };
        }
        
        // For AMD-style access
        if (typeof define === 'undefined') {
            window.define = function(deps, factory) {
                if (typeof deps === 'function') {
                    factory = deps;
                    deps = [];
                }
                if (deps.includes('events')) {
                    return factory({ EventEmitter: EventEmitter });
                }
                return factory();
            };
            window.define.amd = true;
        }
    }
    
    // Additional compatibility for different naming conventions
    if (typeof window !== 'undefined') {
        window.EventEmitter = EventEmitter;
        window.Events = { EventEmitter: EventEmitter };
        
        // Set up process object if it doesn't exist (some libraries expect it)
        if (typeof window.process === 'undefined') {
            window.process = {
                EventEmitter: EventEmitter,
                env: {},
                platform: 'browser',
                versions: { node: '16.0.0' },
                nextTick: function(callback) {
                    setTimeout(callback, 0);
                }
            };
        }
        
        // Ensure global object has EventEmitter
        if (typeof window.global === 'undefined') {
            window.global = window;
        }
        window.global.EventEmitter = EventEmitter;
        
        // For Node.js-style module loading
        if (typeof window.__dirname === 'undefined') {
            window.__dirname = '/';
            window.__filename = '/events.js';
        }
        
        // Create a comprehensive events module
        window.events = {
            EventEmitter: EventEmitter,
            once: function(emitter, event) {
                return new Promise((resolve) => {
                    emitter.once(event, resolve);
                });
            }
        };
    }
    
    // Debug: Log all the locations where EventEmitter is available
    console.log('EventEmitter pre-loader installed successfully');
    console.log('EventEmitter available at:', {
        'window.EventEmitter': typeof window.EventEmitter !== 'undefined',
        'global.EventEmitter': typeof global !== 'undefined' && typeof global.EventEmitter !== 'undefined',
        'window.events.EventEmitter': typeof window.events !== 'undefined' && typeof window.events.EventEmitter !== 'undefined',
        'window.require("events")': (() => { 
            try { 
                return typeof window.require('events').EventEmitter !== 'undefined'; 
            } catch(e) { 
                return false; 
            } 
        })(),
        'window.module.exports': typeof window.module !== 'undefined' && typeof window.module.exports !== 'undefined',
        'window.exports': typeof window.exports !== 'undefined',
        'window.process.EventEmitter': typeof window.process !== 'undefined' && typeof window.process.EventEmitter !== 'undefined'
    });
    
    // Add a global interceptor for undefined property access
    if (typeof window !== 'undefined' && typeof Proxy !== 'undefined') {
        const originalWindow = window;
        const handler = {
            get(target, prop) {
                if (prop === 'EventEmitter' && typeof target[prop] === 'undefined') {
                    console.log('EventEmitter accessed from window - returning our polyfill');
                    return EventEmitter;
                }
                return target[prop];
            }
        };
        
        // Note: This is experimental and might not work in all environments
        try {
            Object.setPrototypeOf(window, new Proxy(Object.getPrototypeOf(window), handler));
        } catch (e) {
            // Proxy approach failed, continue without it
        }
    }

})();
