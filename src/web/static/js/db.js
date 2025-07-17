// db.js - All database-related frontend logic for AI Companion
// Exports all functions to window for global access

// Update database info section
function updateDatabaseInfo() {
    const dbModelCountEl = document.getElementById('debug-db-model-count');
    const dbMotionCountEl = document.getElementById('debug-db-motion-count');
    const dbConnectionEl = document.getElementById('debug-db-connection');
    if (!dbModelCountEl || !dbMotionCountEl || !dbConnectionEl) {
        window.debugLog && window.debugLog('⚠️ Database info elements not found');
        return;
    }
    fetch('http://localhost:13443/api/live2d/system_status')
        .then(response => response.json())
        .then(data => {
            if (data.database_connection) {
                dbConnectionEl.textContent = 'Connected';
                dbConnectionEl.className = 'debug-status-success';
                dbModelCountEl.textContent = data.models_count || '0';
                dbMotionCountEl.textContent = data.total_motions || '0';
                window.debugLog && window.debugLog(`📊 DB Status: ${data.models_count} models, ${data.total_motions} motions`);
            } else {
                dbConnectionEl.textContent = 'Disconnected';
                dbConnectionEl.className = 'debug-status-error';
                dbModelCountEl.textContent = '-';
                dbMotionCountEl.textContent = '-';
                window.debugLog && window.debugLog('❌ Database connection failed');
            }
        })
        .catch(error => {
            dbConnectionEl.textContent = 'Error';
            dbConnectionEl.className = 'debug-status-error';
            dbModelCountEl.textContent = '-';
            dbMotionCountEl.textContent = '-';
            window.debugLog && window.debugLog(`❌ Error loading database info: ${error.message}`);
        });
}

// Load database info for debug panel
async function debugDatabaseInfo() {
    window.debugLog && window.debugLog('💾 Loading database information...');
    try {
        const response = await fetch('http://localhost:13443/api/live2d/models');
        if (response.ok) {
            const models = await response.json();
            window.debugLog && window.debugLog(`📦 Database models: ${models.length}`);
            document.getElementById('debug-db-model-count').textContent = models.length;
            document.getElementById('debug-db-connection').textContent = 'Connected';
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        window.debugLog && window.debugLog(`❌ Database error: ${error.message}`, 'error');
        document.getElementById('debug-db-connection').textContent = 'Error';
    }
}

// Clear database
async function debugClearDatabase() {
    if (!confirm('⚠️ WARNING: Delete ALL database content?')) return;
    window.debugLog && window.debugLog('🗑 Clearing database...');
    try {
        const response = await fetch('http://localhost:13443/api/live2d/clear_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.debugLog && window.debugLog('🗑 Database cleared');
            updateDatabaseInfo();
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        window.debugLog && window.debugLog(`❌ Clear error: ${error.message}`, 'error');
    }
}

// Re-import all data
async function debugReimportData() {
    if (!confirm('📥 Re-import all models and motions?')) return;
    window.debugLog && window.debugLog('📥 Starting re-import...');
    try {
        const response = await fetch('http://localhost:13443/api/live2d/reimport_all', {
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.debugLog && window.debugLog('📥 Re-import completed');
            updateDatabaseInfo();
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        window.debugLog && window.debugLog(`❌ Import error: ${error.message}`, 'error');
    }
}

// Export all to window for global access
window.updateDatabaseInfo = updateDatabaseInfo;
window.debugDatabaseInfo = debugDatabaseInfo;
window.debugClearDatabase = debugClearDatabase;
window.debugReimportData = debugReimportData;
