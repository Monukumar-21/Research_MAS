import glob

for file in glob.glob('agents/*.py'):
    if 'base.py' in file or '__init__' in file: continue
    with open(file, 'r') as f: content = f.read()
    
    # 1. Update signature
    content = content.replace('def __init__(self, mcp_client=None, api_key: str | None = None) -> None:',
                              'def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:')
    # 2. Update super call
    content = content.replace('api_key=api_key)', 'api_key=api_key, provider=provider)')
    
    with open(file, 'w') as f: f.write(content)
