// live2d-motions.js
// Live2D motion and animation logic for frontend

function getAvailableMotions() {
    // Returns the available motions for the current model from the Live2D SDK
    if (window.live2dv4 && window.live2dv4._motionGroups) {
        const groups = window.live2dv4._motionGroups;
        let motions = [];
        Object.keys(groups).forEach(group => {
            groups[group].forEach((motion, idx) => {
                motions.push({
                    group: group,
                    index: idx,
                    name: `${group}_${idx}`,
                    type: classifyMotionType(group)
                });
            });
        });
        return motions;
    }
    return [];
}

function classifyMotionType(groupName) {
    // Classifies the motion type based on group name
    const name = groupName.toLowerCase();
    if (name.includes('head') || name.includes('face') || name.includes('eye') || name.includes('nod') || name.includes('tilt') || name.includes('think')) return 'head';
    if (name.includes('body') || name.includes('pose') || name.includes('arm') || name.includes('hand') || name.includes('wave')) return 'body';
    if (name.includes('expression') || name.includes('expr')) return 'expression';
    if (name.includes('special') || name.includes('unique')) return 'special';
    return 'body';
}

async function registerMotionsWithBackend(modelName, motions) {
    // Registers motions for a model with the backend API
    try {
        const response = await fetch(`http://localhost:13443/api/live2d/model/${modelName}/register_motions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ motions })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Failed to register motions:', error);
        return null;
    }
}

function triggerExpressionByName(expressionName) {
    // Triggers an expression by name if available
    if (window.live2dv4 && window.live2dv4.setExpression) {
        window.live2dv4.setExpression(expressionName);
        console.log(`😃 Triggered expression: ${expressionName}`);
    } else {
        console.warn('Expression trigger not available');
    }
}

function triggerMotionByName(motionName) {
    // Triggers a motion by its name (group_index)
    const motions = getAvailableMotions();
    const motion = motions.find(m => m.name === motionName);
    if (motion) {
        forceMotionTrigger(motion);
    } else {
        console.warn('Motion not found:', motionName);
    }
}

function triggerRandomMotion() {
    // Triggers a random motion from available motions
    const motions = getAvailableMotions();
    if (motions.length === 0) return false;
    const motion = motions[Math.floor(Math.random() * motions.length)];
    forceMotionTrigger(motion);
    return true;
}

function forceMotionTrigger(motion) {
    // Forces a motion trigger using the Live2D API
    if (!motion) return;
    try {
        if (window.live2dv4.startMotion) {
            window.live2dv4.startMotion(motion.group, motion.index);
        } else if (window.live2dv4._model && window.live2dv4._model.startMotion) {
            window.live2dv4._model.startMotion(motion.group, motion.index, 2);
        }
        if (window.debugLastMotionName) window.debugLastMotionName.textContent = motion.name;
        console.log(`🎭 Forced motion: ${motion.group}[${motion.index}]`);
    } catch (error) {
        console.warn('Failed to force motion:', error);
    }
}

function tryDirectModelMotionTrigger() {
    // Attempts to trigger a motion directly on the model (for debugging)
    if (window.live2dv4 && window.live2dv4._model && window.live2dv4._model.startMotion) {
        window.live2dv4._model.startMotion('idle', 0, 2);
        console.log('Tried direct model motion trigger');
    }
}

function triggerBodyIdleMotion() {
    // Triggers a body idle motion if available
    const motions = getAvailableMotions().filter(m => m.type === 'body' && m.group.toLowerCase().includes('idle'));
    if (motions.length > 0) {
        forceMotionTrigger(motions[Math.floor(Math.random() * motions.length)]);
    } else {
        triggerRandomMotion();
    }
}

function triggerSubtleIdleMotion() {
    // Triggers a subtle idle motion if available
    const motions = getAvailableMotions().filter(m => m.type === 'body' && m.group.toLowerCase().includes('subtle'));
    if (motions.length > 0) {
        forceMotionTrigger(motions[Math.floor(Math.random() * motions.length)]);
    } else {
        triggerBodyIdleMotion();
    }
}

function triggerHeadAreaMotion() {
    const availableMotions = getAvailableMotions();
    // Filter for head-type motions
    const headMotions = availableMotions.filter(motion => 
        motion.type === 'head' || 
        motion.group.toLowerCase().includes('head') ||
        motion.group.toLowerCase().includes('nod') ||
        motion.group.toLowerCase().includes('tilt') ||
        motion.group.toLowerCase().includes('think')
    );
    // If no head motions found, use general motions
    const motions = headMotions.length > 0 ? headMotions : availableMotions.slice(0, 5);
    const motion = motions[Math.floor(Math.random() * motions.length)];
    try {
        console.log(`🎭 Triggering head motion: ${motion.group}[${motion.index}] (type: ${motion.type || 'unknown'})`);
        if (window.live2dv4.startMotion) {
            const result = window.live2dv4.startMotion(motion.group, motion.index);
            console.log(`🎭 Head motion result:`, result);
        } else if (window.live2dv4._model && window.live2dv4._model.startMotion) {
            const result = window.live2dv4._model.startMotion(motion.group, motion.index, 2);
            console.log(`🎭 Head motion (_model) result:`, result);
        }
    } catch (error) {
        console.warn('Failed to trigger head motion:', error);
    }
}

function triggerBodyAreaMotion() {
    const availableMotions = getAvailableMotions();
    // Filter for body-type motions
    const bodyMotions = availableMotions.filter(motion => 
        motion.type === 'body' || 
        motion.group.toLowerCase().includes('body') ||
        motion.group.toLowerCase().includes('pose') ||
        motion.group.toLowerCase().includes('arm') ||
        motion.group.toLowerCase().includes('hand') ||
        motion.group.toLowerCase().includes('wave')
    );
    // If no body motions found, use general motions
    const motions = bodyMotions.length > 0 ? bodyMotions : availableMotions.slice(0, 5);
    const motion = motions[Math.floor(Math.random() * motions.length)];
    try {
        console.log(`🎭 Triggering body motion: ${motion.group}[${motion.index}] (type: ${motion.type || 'unknown'})`);
        if (window.live2dv4.startMotion) {
            const result = window.live2dv4.startMotion(motion.group, motion.index);
            console.log(`🎭 Body motion result:`, result);
        } else if (window.live2dv4._model && window.live2dv4._model.startMotion) {
            const result = window.live2dv4._model.startMotion(motion.group, motion.index, 2);
            console.log(`🎭 Body motion (_model) result:`, result);
        }
    } catch (error) {
        console.warn('Failed to trigger body motion:', error);
    }
}

// Export to window for global access
window.getAvailableMotions = getAvailableMotions;
window.classifyMotionType = classifyMotionType;
window.registerMotionsWithBackend = registerMotionsWithBackend;
window.triggerExpressionByName = triggerExpressionByName;
window.triggerMotionByName = triggerMotionByName;
window.triggerRandomMotion = triggerRandomMotion;
window.forceMotionTrigger = forceMotionTrigger;
window.tryDirectModelMotionTrigger = tryDirectModelMotionTrigger;
window.triggerBodyIdleMotion = triggerBodyIdleMotion;
window.triggerSubtleIdleMotion = triggerSubtleIdleMotion;
window.triggerHeadAreaMotion = triggerHeadAreaMotion;
window.triggerBodyAreaMotion = triggerBodyAreaMotion;
