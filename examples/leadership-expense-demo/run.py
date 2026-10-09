"""Run with: python run.py. Local loopback only by default."""
import argparse
import uvicorn
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Education Fund expense demo')
    parser.add_argument('--port',type=int,default=8087)
    args=parser.parse_args()
    print(f'Open http://127.0.0.1:{args.port} — Ctrl+C stops the demo.')
    uvicorn.run('app.main:app',host='127.0.0.1',port=args.port,access_log=False)
