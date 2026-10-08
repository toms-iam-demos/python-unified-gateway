import argparse
import uvicorn

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Houston procurement | PUG local demonstration"
    )
    p.add_argument("--port", type=int, default=8089)
    args = p.parse_args()
    print(f"Open http://127.0.0.1:{args.port} — Ctrl+C stops this demo.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, access_log=False)
