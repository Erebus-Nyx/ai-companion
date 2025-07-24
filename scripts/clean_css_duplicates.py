#!/usr/bin/env python3
"""
CSS Duplicate Cleaner
Removes duplicated CSS sections and snapped selectors from live2d_test.css
"""

import re
from pathlib import Path
import sys
from collections import defaultdict

def read_css_file(file_path):
    """Read CSS file and return content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_css_file(file_path, content):
    """Write CSS content to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def find_duplicate_sections(css_content):
    """Find sections that are completely duplicated"""
    lines = css_content.split('\n')
    
    # Look for major section boundaries based on comments or large gaps
    section_starts = []
    
    for i, line in enumerate(lines):
        # Look for section dividers or major changes
        if (line.strip().startswith('/*') and 
            ('====' in line or '----' in line or len(line.strip()) > 50)):
            section_starts.append(i)
    
    return section_starts

def remove_snapped_selectors(css_content):
    """Remove all snapped selector rules"""
    print("🧹 Removing snapped selectors...")
    
    # Remove entire rules containing snapped selectors
    # Pattern: selector.snapped-xxx { ... }
    snapped_pattern = r'[^{}]*\.snapped-[^{}]*\{[^{}]*\}'
    
    original_length = len(css_content)
    css_content = re.sub(snapped_pattern, '', css_content, flags=re.MULTILINE | re.DOTALL)
    removed_length = original_length - len(css_content)
    
    print(f"   Removed {removed_length} characters of snapped selector rules")
    
    return css_content

def remove_duplicate_sections_by_line_range(css_content):
    """Remove duplicate sections based on analysis"""
    lines = css_content.split('\n')
    total_lines = len(lines)
    
    print(f"📊 Original file: {total_lines} lines")
    
    # Based on the analysis, there seems to be major duplication starting around line 1950-2000
    # Let's identify where the real duplication starts
    
    # Look for patterns that indicate duplication
    chat_content_positions = []
    for i, line in enumerate(lines):
        if '.chat-content {' in line.strip():
            chat_content_positions.append(i)
    
    print(f"🔍 Found .chat-content at lines: {[pos+1 for pos in chat_content_positions]}")
    
    if len(chat_content_positions) >= 2:
        # Assume everything after the second occurrence is duplicated
        first_duplicate_line = chat_content_positions[1]
        
        # Look backwards to find a good section boundary
        section_boundary = first_duplicate_line
        for i in range(first_duplicate_line, max(0, first_duplicate_line - 100), -1):
            line = lines[i].strip()
            if (line.startswith('/*') or 
                line == '' or 
                line.startswith('.settings-panel') or
                line.startswith('.dialog-')):
                section_boundary = i
                break
        
        print(f"✂️  Removing duplicate section from line {section_boundary+1} to end")
        print(f"   This removes {total_lines - section_boundary} lines ({((total_lines - section_boundary)/total_lines)*100:.1f}%)")
        
        # Keep only the first part
        cleaned_lines = lines[:section_boundary]
        return '\n'.join(cleaned_lines)
    
    return css_content

def smart_remove_duplicates(css_content):
    """Intelligently remove duplicate sections"""
    print("🧠 Smart duplicate removal...")
    
    # First remove snapped selectors
    css_content = remove_snapped_selectors(css_content)
    
    # Then remove duplicate sections
    css_content = remove_duplicate_sections_by_line_range(css_content)
    
    # Clean up multiple empty lines
    css_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', css_content)
    
    return css_content

def create_backup_and_clean(css_file_path):
    """Main cleanup function"""
    css_path = Path(css_file_path)
    
    if not css_path.exists():
        print(f"❌ CSS file not found: {css_file_path}")
        return False
    
    print(f"🧹 Cleaning CSS file: {css_path}")
    
    # Read original content
    original_content = read_css_file(css_path)
    original_size = len(original_content)
    original_lines = original_content.count('\n')
    
    print(f"📊 Original: {original_size} characters, {original_lines} lines")
    
    # Create backup with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = css_path.with_suffix(f'.{timestamp}.backup')
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    print(f"💾 Backup created: {backup_path}")
    
    # Clean the content
    cleaned_content = smart_remove_duplicates(original_content)
    
    # Stats
    cleaned_size = len(cleaned_content)
    cleaned_lines = cleaned_content.count('\n')
    size_reduction = original_size - cleaned_size
    line_reduction = original_lines - cleaned_lines
    
    print(f"📊 Cleaned: {cleaned_size} characters, {cleaned_lines} lines")
    print(f"📉 Reduction: {size_reduction} characters ({size_reduction/original_size*100:.1f}%), {line_reduction} lines ({line_reduction/original_lines*100:.1f}%)")
    
    # Write cleaned content
    write_css_file(css_path, cleaned_content)
    
    print(f"✅ Cleaned CSS written to: {css_path}")
    print(f"🔄 Backup available at: {backup_path}")
    
    return True

def main():
    css_file = "web/static/css/live2d_test.css"
    
    if len(sys.argv) > 1:
        css_file = sys.argv[1]
    
    print("🚀 CSS Duplicate Cleaner")
    print("=" * 50)
    
    success = create_backup_and_clean(css_file)
    
    if success:
        print("\n✨ Cleanup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Test the website to ensure layout still works")
        print("   2. If issues occur, restore from backup")
        print("   3. Commit changes if everything looks good")
    else:
        print("\n❌ Cleanup failed!")

if __name__ == "__main__":
    main()
