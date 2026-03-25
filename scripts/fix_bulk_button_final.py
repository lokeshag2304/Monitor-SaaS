import os

def surgical_replace(file_path, old_string, new_string):
    """Performs a single find-and-replace operation on a file."""
    try:
        if not os.path.exists(file_path):
            print(f"❌ Error: File not found at {file_path}")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_string not in content:
            print(f"❌ Error: Could not find target code in {file_path}. Skipping update.")
            return False
        
        new_content = content.replace(old_string, new_string)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True

    except Exception as e:
        print(f"❌ Exception occurred while fixing {file_path}: {e}")
        return False

# --- 1. Fix HTML: Rename the injection point ---
html_fixed = surgical_replace(
    "frontend/static/dashboard.html",
    'id="admin-actions"',
    'id="admin-actions-container"'
)

# --- 2. Fix JavaScript: Target the new injection point ---
js_fixed = surgical_replace(
    "frontend/static/js/app.js",
    "const bulkBtnContainer = document.getElementById('admin-actions');",
    "const bulkBtnContainer = document.getElementById('admin-actions-container');"
)

if html_fixed and js_fixed:
    print("\n✅ SUCCESS: Button injection IDs have been synchronized.")
else:
    print("\n⚠️  CRITICAL FAILURE: Please check the file names and try again.")