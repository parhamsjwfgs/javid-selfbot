import subprocess
import sys

def main():
    print("Starting Javid Self Bot...")
    bot = subprocess.Popen([sys.executable, "bot.py"], cwd="/app")
    helper = subprocess.Popen([sys.executable, "helper.py"], cwd="/app")
    
    processes = [bot, helper]
    
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    main()
