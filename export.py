import subprocess

result = subprocess.run(['python', 'manage.py', 'dumpdata', 'users', 'cuisine', '--natural-foreign', '--natural-primary', '-e', 'contenttypes', '-e', 'auth.permission', '--format=json', '--indent=4'], capture_output=True, text=True, encoding='utf-8')

with open('data.json', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
