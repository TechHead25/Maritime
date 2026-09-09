import os
import re

directories = ['c:/Projects/Maritime_Oil/frontend/src/pages', 'c:/Projects/Maritime_Oil/frontend/src/components']

hex_colors = ['#0c1322', '#111827', '#090d16', '#131b2e', '#1e293b', '#0a0f1d']

def update_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace solid backgrounds with glass-panel in inline styles
    for color in hex_colors:
        # Match backgroundColor: 'color' or backgroundColor: "color"
        pattern = r"backgroundColor:\s*['\"]" + color + r"['\"]"
        replacement = "backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)'"
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Match background: 'color' or background: "color"
        pattern2 = r"background:\s*['\"]" + color + r"['\"]"
        content = re.sub(pattern2, replacement, content, flags=re.IGNORECASE)

    # Replace solid borders with glass borders
    border_pattern = r"border:\s*['\"]1px solid #[0-9a-fA-F]+['\"]"
    border_replacement = "border: '1px solid var(--glass-border)'"
    content = re.sub(border_pattern, border_replacement, content)
    
    border_pattern2 = r"borderBottom:\s*['\"]1px solid #[0-9a-fA-F]+['\"]"
    border_replacement2 = "borderBottom: '1px solid var(--glass-border)'"
    content = re.sub(border_pattern2, border_replacement2, content)

    border_pattern3 = r"borderTop:\s*['\"]1px solid #[0-9a-fA-F]+['\"]"
    border_replacement3 = "borderTop: '1px solid var(--glass-border)'"
    content = re.sub(border_pattern3, border_replacement3, content)

    border_pattern4 = r"borderRight:\s*['\"]1px solid #[0-9a-fA-F]+['\"]"
    border_replacement4 = "borderRight: '1px solid var(--glass-border)'"
    content = re.sub(border_pattern4, border_replacement4, content)

    border_pattern5 = r"borderLeft:\s*['\"]1px solid #[0-9a-fA-F]+['\"]"
    border_replacement5 = "borderLeft: '1px solid var(--glass-border)'"
    content = re.sub(border_pattern5, border_replacement5, content)
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {path}')

for directory in directories:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.tsx') and file not in ['LandingPage.tsx', 'OverviewDashboard.tsx', 'AppLayout.tsx']:
                update_file(os.path.join(root, file))
