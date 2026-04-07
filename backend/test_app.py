import traceback
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Step 1: Importing app...")
    from app import create_app
    print("Step 2: Creating app...")
    app = create_app()
    print("Step 3: App created successfully!")
    print("Registered routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print(f"  {rule.methods - {'OPTIONS', 'HEAD'}} {rule.rule}")
    print("\nDone!")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
