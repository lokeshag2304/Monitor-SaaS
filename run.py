import uvicorn
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print("\n" + "=" * 60)
    print(">>> Website Monitor - Starting Server")
    print("=" * 60)
    print(f"\n[+] Server Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {'Enabled' if reload else 'Disabled'}")
    print(f"   Log Level: {log_level}")
    print(f"\n[i] Server will be available at:")
    print(f"   Local: http://{host}:{port}")
    print(f"   API Docs: http://{host}:{port}/docs")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("[!] Server stopped by user (Ctrl+C)")
        print("=" * 60 + "\n")
        sys.exit(0)
    except Exception as e:
        print("\n\n" + "=" * 60)
        print(f"[X] Error starting server: {e}")
        print("=" * 60 + "\n")
        sys.exit(1)