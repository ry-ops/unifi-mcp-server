#!/usr/bin/env python3
"""
Script to add type hints to remaining functions in main.py
"""
import re
from typing import List, Tuple

def add_prompt_return_types(content: str) -> str:
    """Add -> Dict[str, Any] to prompt functions"""
    # Prompt functions return dict with description and messages
    prompt_pattern = r'(def (how_to_\w+)\(\):)'
    replacement = r'\1 -> Dict[str, Any]:'
    content = re.sub(prompt_pattern, replacement.replace('():', '() -> Dict[str, Any]:'), content)

    # Fix the regex properly
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip().startswith('def how_to_') and '() -> ' not in line:
            line = line.replace('):', ') -> Dict[str, Any]:')
        new_lines.append(line)
    return '\n'.join(new_lines)

def add_async_resource_types(content: str) -> str:
    """Add proper return types to async resources"""
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        # Match async resource functions
        if line.strip().startswith('async def ') and '@mcp.resource' in '\n'.join(new_lines[-5:]):
            if ' -> ' not in line and not line.strip().endswith(':'):
                # Most resources return lists
                line = line.rstrip() + ' -> List[Dict[str, Any]]:'
        new_lines.append(line)
    return '\n'.join(new_lines)

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Apply transformations
content = add_prompt_return_types(content)

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print("Type hints added successfully!")
