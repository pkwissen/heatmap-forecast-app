# launcher.py

import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.join(sys._MEIPASS, "_internal")
else:
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_internal")

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'modules'))
sys.path.insert(0, os.path.join(BASE_DIR, 'prophet'))
sys.path.insert(0, os.path.join(BASE_DIR, 'holidays'))

# Entry point
os.system(f'streamlit run "{os.path.join(BASE_DIR, "app.py")}"')
