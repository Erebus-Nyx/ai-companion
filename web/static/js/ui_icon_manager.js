/**
 * Character Icon Manager - Icon Upload and Processing System
 * Handles character icon upload, processing, and management
 */

class CharacterIconManager {
    constructor() {
        this.currentCharacterIcon = null;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.iconSize = 64; // 64x64 for high quality
        
        this.initializeIconManager();
    }
    
    initializeIconManager() {
        console.log('Character Icon Manager initialized');
        
        // Set up file input change handler if it exists
        const fileInput = document.getElementById('characterIconFile');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleIconUpload(e));
        }
    }
    
    handleIconUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }
        
        // Validate file size
        if (file.size > this.maxFileSize) {
            alert('Image file is too large. Please select an image smaller than 5MB.');
            return;
        }
        
        console.log('Processing character icon upload:', file.name);
        
        // Create FileReader to read the image
        const reader = new FileReader();
        reader.onload = (e) => {
            this.processCharacterIcon(e.target.result, file.name);
        };
        reader.readAsDataURL(file);
    }
    
    processCharacterIcon(imageDataUrl, fileName) {
        const img = new Image();
        img.onload = () => {
            // Create canvas for image processing
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size for people list icon
            canvas.width = this.iconSize;
            canvas.height = this.iconSize;
            
            // Calculate dimensions to maintain aspect ratio
            let sourceX = 0, sourceY = 0, sourceWidth = img.width, sourceHeight = img.height;
            
            // Crop to square if not already square
            if (img.width > img.height) {
                sourceX = (img.width - img.height) / 2;
                sourceWidth = img.height;
            } else if (img.height > img.width) {
                sourceY = (img.height - img.width) / 2;
                sourceHeight = img.width;
            }
            
            // Draw the image scaled and cropped to square
            ctx.drawImage(img, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, this.iconSize, this.iconSize);
            
            // Get the processed image data
            const processedImageData = canvas.toDataURL('image/png', 0.9);
            
            // Store the icon data
            this.currentCharacterIcon = {
                original: imageDataUrl,
                processed: processedImageData,
                fileName: fileName,
                timestamp: new Date().toISOString()
            };
            
            // Update the preview
            this.updateIconPreview(processedImageData);
            
            console.log('Character icon processed successfully:', fileName);
        };
        
        img.onerror = () => {
            alert('Error loading image. Please try a different file.');
            console.error('Failed to load image for processing');
        };
        
        img.src = imageDataUrl;
    }
    
    updateIconPreview(imageDataUrl) {
        const preview = document.getElementById('iconPreview');
        const removeBtn = document.getElementById('removeIconBtn');
        
        if (imageDataUrl && preview) {
            preview.innerHTML = `<img src="${imageDataUrl}" alt="Character Icon" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;">`;
            preview.classList.add('has-image');
            
            if (removeBtn) {
                removeBtn.style.display = 'inline-block';
            }
        } else {
            // Reset to placeholder
            if (preview) {
                preview.innerHTML = `
                    <div class="icon-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px;">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5"/>
                            <polyline points="21,15 16,10 5,21"/>
                        </svg>
                        <span style="font-size: 12px; margin-top: 4px;">No icon uploaded</span>
                    </div>
                `;
                preview.classList.remove('has-image');
            }
            
            if (removeBtn) {
                removeBtn.style.display = 'none';
            }
        }
    }
    
    removeCharacterIcon() {
        if (confirm('Are you sure you want to remove the character icon?')) {
            this.currentCharacterIcon = null;
            this.updateIconPreview(null);
            
            // Clear the file input
            const fileInput = document.getElementById('characterIconFile');
            if (fileInput) {
                fileInput.value = '';
            }
            
            console.log('Character icon removed');
        }
    }
    
    // Function to get character icon data for saving
    getCharacterIconData() {
        return this.currentCharacterIcon;
    }
    
    // Function to load character icon when editing existing character
    loadCharacterIcon(iconData) {
        if (iconData) {
            this.currentCharacterIcon = iconData;
            this.updateIconPreview(iconData.processed || iconData.original);
            console.log('Loaded existing character icon');
        } else {
            // Clear icon without confirmation when loading character (not user-initiated)
            this.currentCharacterIcon = null;
            this.updateIconPreview(null);
            
            // Clear the file input
            const fileInput = document.getElementById('characterIconFile');
            if (fileInput) {
                fileInput.value = '';
            }
            
            console.log('Character icon cleared (no icon set for this character)');
        }
    }
    
    // Create a profile picture from an existing image URL or data
    createProfilePictureFromImage(imageSource, callback) {
        if (typeof imageSource === 'string' && imageSource.startsWith('data:')) {
            // Already a data URL
            this.processCharacterIcon(imageSource, 'imported_image.png');
            if (callback) callback(this.currentCharacterIcon);
            return;
        }
        
        // Try to load as URL
        const img = new Image();
        img.crossOrigin = 'anonymous'; // For CORS
        
        img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            
            ctx.drawImage(img, 0, 0);
            const dataUrl = canvas.toDataURL('image/png');
            
            this.processCharacterIcon(dataUrl, 'imported_image.png');
            if (callback) callback(this.currentCharacterIcon);
        };
        
        img.onerror = () => {
            console.error('Failed to load image from source:', imageSource);
            if (callback) callback(null);
        };
        
        img.src = imageSource;
    }
    
    // Generate a default avatar with initials
    generateDefaultAvatar(initials, backgroundColor = '#6366f1', textColor = '#ffffff') {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = this.iconSize;
        canvas.height = this.iconSize;
        
        // Draw background
        ctx.fillStyle = backgroundColor;
        ctx.fillRect(0, 0, this.iconSize, this.iconSize);
        
        // Draw initials
        ctx.fillStyle = textColor;
        ctx.font = `${this.iconSize * 0.4}px Arial, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        const text = initials.substring(0, 2).toUpperCase();
        ctx.fillText(text, this.iconSize / 2, this.iconSize / 2);
        
        const dataUrl = canvas.toDataURL('image/png');
        
        this.currentCharacterIcon = {
            original: dataUrl,
            processed: dataUrl,
            fileName: `avatar_${initials}.png`,
            timestamp: new Date().toISOString(),
            isGenerated: true
        };
        
        this.updateIconPreview(dataUrl);
        return this.currentCharacterIcon;
    }
    
    // Utility function to generate a random color
    generateRandomColor() {
        const colors = [
            '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
            '#f97316', '#eab308', '#22c55e', '#06b6d4',
            '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    // Export icon as blob for upload to server
    async getIconAsBlob() {
        if (!this.currentCharacterIcon) return null;
        
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = this.iconSize;
            canvas.height = this.iconSize;
            
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0);
                canvas.toBlob(resolve, 'image/png', 0.9);
            };
            img.src = this.currentCharacterIcon.processed;
        });
    }
    
    // Clear current icon
    clearIcon() {
        this.currentCharacterIcon = null;
        this.updateIconPreview(null);
        
        const fileInput = document.getElementById('characterIconFile');
        if (fileInput) {
            fileInput.value = '';
        }
    }
    
    // Get icon data URL for immediate use
    getIconDataUrl() {
        return this.currentCharacterIcon?.processed || null;
    }
    
    // Check if an icon is currently loaded
    hasIcon() {
        return !!this.currentCharacterIcon;
    }
}

// Global instance
let characterIconManager = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    characterIconManager = new CharacterIconManager();
    window.characterIconManager = characterIconManager;
});

// Legacy function compatibility
window.handleIconUpload = (event) => characterIconManager?.handleIconUpload(event);
window.removeCharacterIcon = () => characterIconManager?.removeCharacterIcon();
window.getCharacterIconData = () => characterIconManager?.getCharacterIconData();
window.loadCharacterIcon = (iconData) => characterIconManager?.loadCharacterIcon(iconData);
