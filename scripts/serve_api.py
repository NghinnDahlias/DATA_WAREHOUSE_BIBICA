"""Loopback-only server. Access logs are disabled to avoid logging user query text."""
import argparse
import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import uvicorn
from src.api.db import database_dsn


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    database_dsn()  # Fail before creating runtime state if the parent DB was configured.
    runtime = root/'.runtime'
    runtime.mkdir(exist_ok=True)
    (runtime/'api.pid.json').write_text(json.dumps({'pid':os.getpid(),'port':args.port}),encoding='utf8')
    uvicorn.run('src.api.app:app', host='127.0.0.1', port=args.port, access_log=False)
