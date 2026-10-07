"""Portable local demonstration. No provider credentials or outbound connectors."""
import argparse
import uvicorn
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='PUG Getty procurement playground')
    p.add_argument('--port', type=int, default=8088)
    args = p.parse_args()
    print(f'Open http://127.0.0.1:{args.port} — Ctrl+C stops the demo.')
    uvicorn.run('app.main:app', host='127.0.0.1', port=args.port, access_log=False)
