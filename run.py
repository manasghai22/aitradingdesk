import subprocess
import sys
import time
import os

def main():
    print("===========================================")
    print("🚀 Starting AI Trading Desk")
    print("===========================================")
    
    # 1. Start the trading engine in a subprocess
    print("[1/2] Launching Trading Engine...")
    engine_process = subprocess.Popen(
        [sys.executable, "engine/main_loop.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Give the engine a few seconds to initialize
    time.sleep(3)
    
    # 2. Start the Streamlit dashboard in a subprocess
    print("[2/2] Launching Live Dashboard...")
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.headless=true", "--server.port=8501"],
        stdout=sys.stdout, # Streamlit logs will print here
        stderr=sys.stderr
    )
    
    print("\n✅ All systems go! Dashboard is at: http://localhost:8501")
    print("⚠️  Press Ctrl+C to safely shut down both systems at once.\n")
    
    try:
        # Keep the main thread alive to listen for Ctrl+C
        # and monitor if either child process crashes
        while True:
            time.sleep(1)
            
            if engine_process.poll() is not None:
                print("❌ Engine process stopped unexpectedly.")
                break
            
            if dashboard_process.poll() is not None:
                print("❌ Dashboard process stopped unexpectedly.")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AI Trading Desk...")
    finally:
        # Gracefully terminate both processes
        engine_process.terminate()
        dashboard_process.terminate()
        
        # Wait for them to exit thoroughly
        engine_process.wait()
        dashboard_process.wait()
        print("Shutdown complete. Bye!")

if __name__ == "__main__":
    main()
