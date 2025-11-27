with open('requirements.txt', 'rb') as f:
    content = f.read()

try:
    decoded_content = content.decode('utf-16')
except UnicodeDecodeError:
    decoded_content = content.decode('utf-8', errors='ignore')

with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write(decoded_content)