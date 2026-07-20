import sys, json
data = json.load(sys.stdin)
for issue in data.get("issues", []):
    print(f"File: {issue.get('component')}, Line: {issue.get('line')}, Msg: {issue.get('message')}")
