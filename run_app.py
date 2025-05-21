import os
import sys

# Get the folder where the executable is running
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(base_path, 'zachmlb.py')

print(f"🚀 Launching: {script_path}")
exit_code = os.system(f'streamlit run "{script_path}"')
print(f"❌ Streamlit exited with code {exit_code}")
input("Press Enter to close...")
