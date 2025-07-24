# Audio Queue Management System

## Overview

The Audio Queue Management System prevents audio overlap when multiple Live2D models are loaded and generating speech simultaneously. This is essential for maintaining clear audio output and preventing the cacophony that occurs when multiple avatars try to speak at the same time.

## Problem Solved

**Before**: When multiple Live2D models were loaded, each could trigger TTS independently, causing:
- Audio tracks playing simultaneously and overlapping
- Unintelligible speech due to multiple voices at once
- Poor user experience with chaotic audio output
- No control over which avatar should speak first

**After**: With the audio queue system:
- Only one avatar speaks at a time
- Clear, sequential audio output
- Configurable priority system for important messages
- User control over audio queue behavior

## Components

### 1. AudioQueueManager (`audio_queue_manager.js`)
The core audio queue management system with three operating modes:

#### Queue Mode (Default)
- Audio requests are queued sequentially
- First-in, first-out processing
- Best for natural conversation flow

#### Interrupt Mode
- New audio immediately stops current playback
- Useful for urgent messages or user interactions
- Current audio is interrupted and new audio plays immediately

#### Priority Mode
- Audio with higher priority can interrupt lower priority audio
- Lower or equal priority audio is queued
- Flexible system for mixed-importance scenarios

### 2. AudioQueueControlPanel (`audio_queue_control_panel.js`)
A user interface for controlling and monitoring the audio queue:
- Switch between queue modes in real-time
- View current queue status and statistics
- Clear queue or stop current audio
- Monitor performance metrics

### 3. Integration with TTS System
The existing `triggerEmotionalTTS` function is enhanced to:
- Route audio through the queue manager
- Support priority levels
- Fallback to direct playback if queue manager unavailable
- Maintain compatibility with existing code

## Usage

### Basic Usage
```javascript
// Standard TTS call (now automatically queued)
triggerEmotionalTTS(text, emotion, avatarId, personalityTraits, intensity);

// TTS call with priority
triggerEmotionalTTS(text, emotion, avatarId, personalityTraits, intensity, priority);
```

### Priority Levels
- **Priority 1**: Autonomous avatar messages (default)
- **Priority 2**: System notifications
- **Priority 3**: User chat responses (higher priority)
- **Priority 5**: Urgent messages (can interrupt)

### Queue Control
```javascript
// Change queue mode
setAudioQueueMode('queue');    // Sequential processing
setAudioQueueMode('interrupt'); // Interrupt current audio
setAudioQueueMode('priority');  // Priority-based processing

// Control playback
clearAudioQueue();  // Clear pending audio
stopCurrentAudio(); // Stop current playback

// Monitor status
const status = getAudioQueueStatus();
console.log(status);
```

### UI Controls
- **Audio Queue Button**: Click the music note icon in the navigation bar
- **Control Panel**: Configure queue mode, view status, and control playback
- **Real-time Monitoring**: See current queue length and processing statistics

## Testing

### Quick Test
```javascript
// Test basic queue functionality
runAudioQueueTestSuite();
```

### Manual Testing
```javascript
// Test audio overlap prevention
testAudioOverlap();

// Test priority system
testPrioritySystem();

// Test rapid avatar switching
testRapidAvatarSwitching();
```

### Monitoring
```javascript
// Start real-time monitoring
startAudioQueueMonitoring();
```

## Configuration

### Default Settings
- **Mode**: Queue (sequential processing)
- **Max Retries**: 2 attempts per audio request
- **Retry Delay**: 100ms between queue items
- **Cleanup Interval**: 30 seconds for completed requests

### Customization
The system can be customized by modifying the AudioQueueManager constructor or through the control panel.

## Integration Points

### Autonomous Avatars
- Autonomous conversations automatically use the queue system
- Priority 1 (normal) for autonomous messages
- Prevents multiple autonomous avatars speaking simultaneously

### Chat System
- User chat responses get priority 3 (higher priority)
- Can interrupt autonomous conversations when needed
- Maintains responsive user interaction

### Live2D Models
- Seamless integration with existing Live2D avatar system
- Maintains lipsync and expression synchronization
- Compatible with all current avatar personalities

## Browser Compatibility

- **Modern Browsers**: Full functionality with Web Audio API
- **Fallback Support**: Graceful degradation for older browsers
- **Mobile Support**: Optimized for mobile device audio restrictions

## Performance

### Metrics Tracked
- Total audio requests processed
- Completed vs failed requests
- Queue length statistics
- Interruption frequency

### Optimization
- Automatic cleanup of completed requests
- Minimal memory footprint
- Efficient queue processing
- Performance monitoring and statistics

## Troubleshooting

### Common Issues

**Audio Queue Manager Not Available**
- Ensure `audio_queue_manager.js` is loaded before `audio_tts.js`
- Check browser console for initialization errors

**Audio Still Overlapping**
- Verify queue mode is set correctly
- Check if fallback to direct playback is occurring
- Monitor queue status for processing errors

**Priority Not Working**
- Ensure priority mode is enabled: `setAudioQueueMode('priority')`
- Check priority values are correctly specified
- Higher numbers = higher priority

### Debug Mode
Enable detailed logging by opening the browser console and monitoring queue operations:
```javascript
// Enable queue monitoring
startAudioQueueMonitoring();

// View current status
console.log(getAudioQueueStatus());
```

## API Reference

### Core Functions
- `triggerEmotionalTTS(text, emotion, avatarId, traits, intensity, priority)`
- `setAudioQueueMode(mode)` - 'queue', 'interrupt', or 'priority'
- `getAudioQueueStatus()` - Returns current queue status
- `clearAudioQueue()` - Clear all pending audio
- `stopCurrentAudio()` - Stop current playback

### Control Panel
- `toggleAudioQueuePanel()` - Show/hide control panel
- Access via audio queue button in navigation bar

### Testing Functions
- `runAudioQueueTestSuite()` - Comprehensive test
- `testAudioOverlap()` - Test overlap prevention
- `testPrioritySystem()` - Test priority handling
- `resetAudioQueue()` - Reset to default state

## Future Enhancements

- **Voice Activity Detection**: Pause queue when user is speaking
- **Conversation Context**: Smart priority based on conversation flow
- **Avatar Relationships**: Priority based on avatar relationships
- **Audio Ducking**: Lower background audio when speaking
- **Cross-tab Synchronization**: Coordinate audio across multiple tabs
