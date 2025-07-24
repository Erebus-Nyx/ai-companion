#!/usr/bin/env python3
"""
Precise CSS Duplicate Cleaner
Surgically removes only the exact duplicates identified by the analysis
"""

import re
from pathlib import Path
from collections import defaultdict
import sys

def parse_css_rules(css_content):
    """Parse CSS content and extract rules with their selectors and properties"""
    rules = []
    
    # Remove comments first but preserve structure
    lines = css_content.split('\n')
    
    # Find rules using line-by-line parsing for better precision
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('/*') or line.startswith('*') or line.endswith('*/'):
            i += 1
            continue
        
        # Look for selector lines (end with { or have { on same line)
        if '{' in line:
            # Single line rule
            if '}' in line:
                rule_text = line
                start_line = i
                end_line = i
            else:
                # Multi-line rule - collect until closing brace
                rule_lines = [line]
                start_line = i
                i += 1
                brace_count = line.count('{') - line.count('}')
                
                while i < len(lines) and brace_count > 0:
                    rule_lines.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                
                end_line = i - 1
                rule_text = '\n'.join(rule_lines)
            
            # Parse the rule
            if '{' in rule_text and '}' in rule_text:
                selector_part = rule_text.split('{')[0].strip()
                properties_part = rule_text.split('{')[1].split('}')[0].strip()
                
                # Parse properties
                props = []
                if properties_part:
                    for prop in properties_part.split(';'):
                        prop = prop.strip()
                        if prop and ':' in prop:
                            name, value = prop.split(':', 1)
                            props.append((name.strip(), value.strip()))
                
                rules.append({
                    'selector': selector_part,
                    'properties': props,
                    'start_line': start_line,
                    'end_line': end_line,
                    'full_text': rule_text,
                    'line_numbers': list(range(start_line + 1, end_line + 2))
                })
        
        i += 1
    
    return rules

def find_exact_duplicates(rules):
    """Find rules that are completely identical"""
    identical_groups = defaultdict(list)
    
    for i, rule in enumerate(rules):
        # Create signature from selector + sorted properties
        props_signature = tuple(sorted(rule['properties']))
        signature = (rule['selector'].strip(), props_signature)
        identical_groups[signature].append(i)
    
    # Return only groups with multiple rules
    duplicates = {sig: indices for sig, indices in identical_groups.items() 
                  if len(indices) > 1}
    
    return duplicates

def find_snapped_rules(rules):
    """Find all snapped selector rules"""
    snapped_rules = []
    
    for i, rule in enumerate(rules):
        selector = rule['selector']
        if '.snapped-' in selector or 'snapped' in selector.lower():
            snapped_rules.append(i)
    
    return snapped_rules

def create_precise_cleanup_script(css_file_path):
    """Create a precise cleanup that only removes exact duplicates"""
    css_path = Path(css_file_path)
    
    if not css_path.exists():
        print(f"❌ CSS file not found: {css_file_path}")
        return
    
    print(f"🔍 Analyzing CSS file for precise cleanup: {css_path}")
    
    # Read original content
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
        original_lines = css_content.split('\n')
    
    print(f"📊 Original: {len(css_content)} characters, {len(original_lines)} lines")
    
    # Parse CSS rules
    rules = parse_css_rules(css_content)
    print(f"📋 Found {len(rules)} CSS rules")
    
    # Find exact duplicates to remove
    exact_duplicates = find_exact_duplicates(rules)
    snapped_rules = find_snapped_rules(rules)
    
    print(f"\n🎯 REMOVAL TARGETS:")
    print(f"   🔄 Identical rule groups: {len(exact_duplicates)}")
    print(f"   🔗 Snapped selectors: {len(snapped_rules)}")
    
    # Collect line numbers to remove
    lines_to_remove = set()
    
    # Add lines from duplicate rules (keep first, remove rest)
    duplicate_count = 0
    for (selector, props), rule_indices in exact_duplicates.items():
        if len(rule_indices) > 1:
            print(f"\n🔄 Removing duplicates of: {selector}")
            # Keep first occurrence, remove the rest
            for rule_idx in rule_indices[1:]:  
                rule = rules[rule_idx]
                print(f"   • Removing lines {rule['start_line']+1}-{rule['end_line']+1}")
                for line_num in rule['line_numbers']:
                    lines_to_remove.add(line_num - 1)  # Convert to 0-based
                duplicate_count += 1
    
    # Add lines from snapped rules
    snapped_count = 0
    for rule_idx in snapped_rules:
        rule = rules[rule_idx]
        print(f"\n🔗 Removing snapped selector: {rule['selector']}")
        print(f"   • Removing lines {rule['start_line']+1}-{rule['end_line']+1}")
        for line_num in rule['line_numbers']:
            lines_to_remove.add(line_num - 1)  # Convert to 0-based
        snapped_count += 1
    
    print(f"\n📊 REMOVAL SUMMARY:")
    print(f"   🔄 Duplicate rules to remove: {duplicate_count}")
    print(f"   🔗 Snapped rules to remove: {snapped_count}")
    print(f"   📝 Total lines to remove: {len(lines_to_remove)}")
    print(f"   📉 Estimated reduction: {len(lines_to_remove)/len(original_lines)*100:.1f}%")
    
    # Create backup
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = css_path.with_suffix(f'.precise_backup_{timestamp}')
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"💾 Backup created: {backup_path}")
    
    # Create cleaned content
    cleaned_lines = []
    for i, line in enumerate(original_lines):
        if i not in lines_to_remove:
            cleaned_lines.append(line)
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Remove excessive blank lines
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)
    
    # Write cleaned file
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    # Final stats
    final_lines = len(cleaned_content.split('\n'))
    reduction = len(original_lines) - final_lines
    
    print(f"\n✅ CLEANUP COMPLETED:")
    print(f"   📊 Original: {len(original_lines)} lines")
    print(f"   📊 Cleaned: {final_lines} lines")
    print(f"   📉 Removed: {reduction} lines ({reduction/len(original_lines)*100:.1f}%)")
    print(f"   💾 Backup: {backup_path}")
    
    return True

def main():
    css_file = "web/static/css/live2d_test.css"
    
    if len(sys.argv) > 1:
        css_file = sys.argv[1]
    
    print("🎯 Precise CSS Duplicate Cleaner")
    print("=" * 50)
    print("Removes only exact duplicates and snapped selectors")
    print()
    
    success = create_precise_cleanup_script(css_file)
    
    if success:
        print("\n✨ Precise cleanup completed!")
        print("\n📋 What was removed:")
        print("   ✅ Identical duplicate rules (kept first occurrence)")
        print("   ✅ All snapped selector rules")
        print("   ❌ NO consolidation of similar rules (preserved functionality)")
        print("\n🧪 Test the website to ensure everything still works")

if __name__ == "__main__":
    main()
