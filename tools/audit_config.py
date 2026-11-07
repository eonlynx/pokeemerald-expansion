import subprocess
import re

diff = subprocess.check_output(['git', 'diff', 'include/config/'], encoding='utf-8', errors='ignore')

hunks = re.split(r'\n@@ ', diff)
print(f"Total diff hunks: {len(hunks)}")

suspicious = []
for h in hunks[1:]:
    lines = h.splitlines()
    # Check removed (-) vs added (+)
    removed = [l for l in lines if l.startswith('-') and not l.startswith('---')]
    added = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
    
    for r in removed:
        # Check if r had TRUE or FALSE or a specific non-GEN enum
        m_def = re.match(r'^-#define\s+([A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)', r)
        if m_def:
            macro_name = m_def.group(1)
            old_val = m_def.group(2)
            
            # Find in added
            for a in added:
                m_add = re.match(r'^\+#define\s+' + macro_name + r'\s+([A-Za-z0-9_]+)', a)
                if m_add:
                    new_val = m_add.group(1)
                    if old_val in ['TRUE', 'FALSE'] and new_val not in ['TRUE', 'FALSE']:
                        suspicious.append((macro_name, old_val, new_val))
                    elif not old_val.startswith('GEN_') and new_val.startswith('GEN_'):
                        suspicious.append((macro_name, old_val, new_val))

print(f"Suspicious macro replacements found: {len(suspicious)}")
for s in suspicious:
    print("  ", s)
