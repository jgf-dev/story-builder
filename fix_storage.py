with open("src/storybuilder/utils/storage.py", "r") as f:
    content = f.read()

content = content.replace('if __name__ == "__main__":\n        hf_client = get_hf_client()\n\n    upload_story_db(hf_client)', 'if __name__ == "__main__":\n    hf_client = get_hf_client()\n    upload_story_db(hf_client)')

with open("src/storybuilder/utils/storage.py", "w") as f:
    f.write(content)
