// Emergency border injection script - bypasses main waifu-tips.js
// This script directly applies borders to diagnose the issue

console.log('🚨 Emergency border injection script loaded');

// Wait for DOM to be ready
function injectEmergencyBorders() {
    console.log('🚨 Running emergency border injection...');
    
    const waifu = document.getElementById('waifu');
    const canvas2 = document.getElementById('live2d2');
    const canvas4 = document.getElementById('live2d4');
    const tools = document.querySelector('.waifu-tool');
    const message = document.getElementById('waifu-message');
    
    if (waifu) {
        console.log('🚨 Found #waifu element, applying emergency borders...');
        
        // Remove any hiding classes
        waifu.classList.remove('hide');
        
        // Nuclear option - force styling
        waifu.style.cssText = `
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 500px !important;
            height: 500px !important;
            border: 10px solid red !important;
            background: rgba(255, 0, 0, 0.2) !important;
            z-index: 9999 !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            overflow: visible !important;
        `;
        
        console.log('🚨 Applied emergency red border to #waifu');
        
        // Style canvases
        if (canvas2) {
            canvas2.style.cssText = `
                border: 5px solid green !important;
                background: rgba(0, 255, 0, 0.1) !important;
                display: block !important;
                width: 500px !important;
                height: 500px !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
            `;
            console.log('🚨 Applied emergency green border to canvas2');
        }
        
        if (canvas4) {
            canvas4.style.cssText = `
                border: 5px solid blue !important;
                background: rgba(0, 0, 255, 0.1) !important;
                display: none !important;
                width: 500px !important;
                height: 500px !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
            `;
            console.log('🚨 Applied emergency blue border to canvas4');
        }
        
        if (tools) {
            tools.style.cssText = `
                border: 3px solid yellow !important;
                background: rgba(255, 255, 0, 0.2) !important;
                display: block !important;
                position: absolute !important;
                top: 10px !important;
                left: 10px !important;
                z-index: 10000 !important;
                padding: 5px !important;
            `;
            console.log('🚨 Applied emergency yellow border to tools');
        }
        
        if (message) {
            message.style.cssText = `
                border: 3px solid purple !important;
                background: rgba(255, 0, 255, 0.2) !important;
                display: block !important;
                position: absolute !important;
                top: 50px !important;
                left: 10px !important;
                z-index: 10001 !important;
                padding: 10px !important;
                color: white !important;
            `;
            message.textContent = 'EMERGENCY BORDERS ACTIVE';
            console.log('🚨 Applied emergency purple border to message');
        }
        
        // Log computed styles for verification
        const computedStyle = window.getComputedStyle(waifu);
        console.log('🚨 Final computed border:', computedStyle.border);
        console.log('🚨 Final computed display:', computedStyle.display);
        console.log('🚨 Final computed visibility:', computedStyle.visibility);
        
        return true;
    } else {
        console.log('🚨 ERROR: #waifu element not found!');
        
        // List all elements with IDs for debugging
        const allElements = document.querySelectorAll('[id]');
        console.log('🚨 Available elements with IDs:');
        allElements.forEach(el => {
            console.log(`  - #${el.id}: ${el.tagName}`);
        });
        
        return false;
    }
}

// Try to inject borders immediately and on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectEmergencyBorders);
} else {
    injectEmergencyBorders();
}

// Also try after a delay in case elements are added dynamically
setTimeout(injectEmergencyBorders, 1000);
setTimeout(injectEmergencyBorders, 3000);
setTimeout(injectEmergencyBorders, 5000);

// Make function available globally for manual testing
window.injectEmergencyBorders = injectEmergencyBorders;

console.log('🚨 Emergency border script setup complete. Check console for results.');
