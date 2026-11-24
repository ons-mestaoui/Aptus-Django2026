import os
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from django.template.loader import get_template
from django.urls import reverse, NoReverseMatch

templates_dir = r"C:\xampp\htdocs\aptus_django\templates"

url_tag_pattern = re.compile(r"{%\s*url\s+'([^']+)'([^%]*)\s*%}")
href_pattern = re.compile(r'href="([^"]+)"')

errors = []
all_found_urls = set()

for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, templates_dir)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as html_file:
                content = html_file.read()
                
                # Check all {% url 'name' ... %}
                for match in url_tag_pattern.finditer(content):
                    url_name = match.group(1)
                    args_part = match.group(2).strip()
                    all_found_urls.add((relpath, url_name, args_part))
                    
                    # Try to reverse if no args
                    if not args_part:
                        try:
                            reverse(url_name)
                        except NoReverseMatch as e:
                            errors.append((relpath, url_name, str(e)))

print(f"Total template url tags found: {len(all_found_urls)}")
print(f"Total reverse errors: {len(errors)}")
for err in errors:
    print(f"❌ {err[0]}: url '{err[1]}' -> {err[2]}")

print("\n--- Listing all unique url names in templates ---")
for tpl, name, args in sorted(all_found_urls):
    print(f"  {tpl} -> '{name}' {args}")
