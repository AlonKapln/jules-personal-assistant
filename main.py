import sys
import subprocess
import os

def run_bot():
    print("Starting Kernel...")
    # Use python from the current environment, running as a module to fix imports
    subprocess.run([sys.executable, "-m", "src.bot"])

def run_dashboard():
    print("Starting Dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/dashboard.py"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [bot|dashboard]")
        print("Example:")
        print("  python main.py bot       # Runs the Telegram bot")
        print("  python main.py dashboard # Runs the settings GUI")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "bot":
        run_bot()
    elif cmd == "dashboard":
        run_dashboard()
    else:
        print(f"Unknown command '{cmd}'. Use 'bot' or 'dashboard'.")
