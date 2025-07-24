#!/usr/bin/env python3
"""
CSS Duplicate Finder
Identifies duplicated CSS selectors and rules in the live2d_test.css file
"""

import re
from pathlib import Path
from collections import defaultdict, Counter
import sys

def parse_css_rules(css_content):
    """Parse CSS content and extract rules with their selectors and properties"""
    rules = []
    
    # Remove comments first
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Split into rules (selector { properties })
    rule_pattern = r'([^{}]+)\s*\{([^{}]*)\}'
    matches = re.finditer(rule_pattern, css_content)
    
    for match in matches:
        selector = match.group(1).strip()
        properties = match.group(2).strip()
        start_pos = match.start()
        
        # Skip empty rules
        if not selector or not properties:
            continue
            
        # Parse properties
        prop_list = []
        for prop in properties.split(';'):
            prop = prop.strip()
            if prop and ':' in prop:
                prop_name, prop_value = prop.split(':', 1)
                prop_list.append((prop_name.strip(), prop_value.strip()))
        
        rules.append({
            'selector': selector,
            'properties': prop_list,
            'raw_properties': properties,
            'position': start_pos,
            'full_match': match.group(0)
        })
    
    return rules

def find_line_number(content, position):
    """Find line number for a given character position"""
    return content[:position].count('\n') + 1

def find_duplicate_selectors(rules):
    """Find selectors that appear multiple times"""
    selector_occurrences = defaultdict(list)
    
    for i, rule in enumerate(rules):
        selector_occurrences[rule['selector']].append(i)
    
    duplicates = {selector: indices for selector, indices in selector_occurrences.items() 
                  if len(indices) > 1}
    
    return duplicates

def find_similar_property_sets(rules):
    """Find rules with identical or very similar property sets"""
    property_signatures = defaultdict(list)
    
    for i, rule in enumerate(rules):
        # Create a signature from sorted properties (ignoring values for now)
        prop_names = tuple(sorted([prop[0] for prop in rule['properties']]))
        if len(prop_names) > 0:  # Only consider rules with properties
            property_signatures[prop_names].append(i)
    
    similar_sets = {sig: indices for sig, indices in property_signatures.items() 
                    if len(indices) > 1 and len(sig) > 2}  # At least 3 properties
    
    return similar_sets

def find_identical_rules(rules):
    """Find completely identical rules (selector + properties)"""
    rule_signatures = defaultdict(list)
    
    for i, rule in enumerate(rules):
        # Create signature from selector + sorted properties
        props = tuple(sorted(rule['properties']))
        signature = (rule['selector'], props)
        rule_signatures[signature].append(i)
    
    identical = {sig: indices for sig, indices in rule_signatures.items() 
                 if len(indices) > 1}
    
    return identical

def analyze_css_file(css_file_path):
    """Main analysis function"""
    css_path = Path(css_file_path)
    
    if not css_path.exists():
        print(f"❌ CSS file not found: {css_file_path}")
        return
    
    print(f"🔍 Analyzing CSS file: {css_path}")
    
    # Read CSS content
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    print(f"📊 File size: {len(css_content)} characters, {css_content.count(chr(10))} lines")
    
    # Parse CSS rules
    rules = parse_css_rules(css_content)
    print(f"📋 Found {len(rules)} CSS rules")
    
    # Find different types of duplicates
    print("\n" + "="*60)
    print("🔍 DUPLICATE ANALYSIS")
    print("="*60)
    
    # 1. Duplicate selectors
    duplicate_selectors = find_duplicate_selectors(rules)
    print(f"\n1️⃣  DUPLICATE SELECTORS: {len(duplicate_selectors)}")
    print("-" * 40)
    
    for selector, indices in sorted(duplicate_selectors.items()):
        if len(indices) > 1:
            print(f"\n🎯 Selector: {selector}")
            print(f"   Found {len(indices)} times:")
            for idx in indices:
                line_num = find_line_number(css_content, rules[idx]['position'])
                print(f"   • Line {line_num}: {len(rules[idx]['properties'])} properties")
    
    # 2. Identical rules (complete duplicates)
    identical_rules = find_identical_rules(rules)
    print(f"\n2️⃣  IDENTICAL RULES: {len(identical_rules)}")
    print("-" * 40)
    
    for (selector, props), indices in sorted(identical_rules.items()):
        if len(indices) > 1:
            print(f"\n🔄 Identical Rule: {selector}")
            print(f"   Properties: {len(props)}")
            print(f"   Duplicated {len(indices)} times:")
            for idx in indices:
                line_num = find_line_number(css_content, rules[idx]['position'])
                print(f"   • Line {line_num}")
    
    # 3. Similar property sets
    similar_properties = find_similar_property_sets(rules)
    print(f"\n3️⃣  SIMILAR PROPERTY SETS: {len(similar_properties)}")
    print("-" * 40)
    
    for prop_signature, indices in sorted(similar_properties.items()):
        if len(indices) > 1:
            print(f"\n🔧 Property pattern: {', '.join(prop_signature[:5])}{'...' if len(prop_signature) > 5 else ''}")
            print(f"   Found in {len(indices)} rules:")
            for idx in indices:
                line_num = find_line_number(css_content, rules[idx]['position'])
                print(f"   • Line {line_num}: {rules[idx]['selector']}")
    
    # 4. Snapped vs regular patterns
    print(f"\n4️⃣  SNAPPED VS REGULAR PATTERNS")
    print("-" * 40)
    
    snapped_selectors = []
    regular_selectors = []
    
    for rule in rules:
        selector = rule['selector']
        if '.snapped-' in selector or 'snapped' in selector:
            snapped_selectors.append(rule)
        else:
            # Look for corresponding regular selector
            base_selector = re.sub(r'\.snapped-\w+', '', selector).strip()
            if base_selector:
                regular_selectors.append((base_selector, rule))
    
    print(f"   🔗 Found {len(snapped_selectors)} snapped selectors")
    
    # Find matching pairs
    matches = []
    for snapped_rule in snapped_selectors:
        snapped_selector = snapped_rule['selector']
        base_selector = re.sub(r'\.snapped-\w+', '', snapped_selector).strip()
        
        for regular_base, regular_rule in regular_selectors:
            if base_selector == regular_base:
                matches.append((regular_rule, snapped_rule))
    
    print(f"   🎯 Found {len(matches)} regular/snapped pairs")
    
    for regular_rule, snapped_rule in matches[:10]:  # Show first 10
        reg_line = find_line_number(css_content, regular_rule['position'])
        snap_line = find_line_number(css_content, snapped_rule['position'])
        print(f"   • {regular_rule['selector']} (Line {reg_line}) ↔ {snapped_rule['selector']} (Line {snap_line})")
    
    # Summary and recommendations
    print(f"\n" + "="*60)
    print("📝 SUMMARY & RECOMMENDATIONS")
    print("="*60)
    
    total_duplicates = len(duplicate_selectors) + len(identical_rules) + len(similar_properties)
    print(f"📊 Total duplicate patterns found: {total_duplicates}")
    print(f"🎯 Duplicate selectors: {len(duplicate_selectors)}")
    print(f"🔄 Identical rules: {len(identical_rules)}")
    print(f"🔧 Similar property sets: {len(similar_properties)}")
    print(f"🔗 Snapped selectors: {len(snapped_selectors)}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if len(snapped_selectors) > 0:
        print(f"   1. Remove {len(snapped_selectors)} snapped selectors (snap-to-edge was removed)")
    if len(duplicate_selectors) > 5:
        print(f"   2. Consolidate {len(duplicate_selectors)} duplicate selectors")
    if len(identical_rules) > 0:
        print(f"   3. Remove {len(identical_rules)} completely identical rules")
    
    estimated_reduction = len(snapped_selectors) + len(identical_rules) * 0.5
    print(f"   📉 Estimated file size reduction: ~{estimated_reduction:.0f} rules ({estimated_reduction/len(rules)*100:.1f}%)")

def main():
    css_file = "web/static/css/live2d_test.css"
    
    if len(sys.argv) > 1:
        css_file = sys.argv[1]
    
    analyze_css_file(css_file)

if __name__ == "__main__":
    main()
