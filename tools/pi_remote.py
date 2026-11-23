"""Run a literal Python script over the authorized local Pi SSH connection."""
import argparse
import subprocess
from pathlib import Path
def main():
    parser=argparse.ArgumentParser();parser.add_argument('script',type=Path)
    parser.add_argument('--host',default='saul@10.217.96.102')
    parser.add_argument('--key',type=Path,default=Path.home()/'.ssh/blistertrace_pi')
    args=parser.parse_args()
    result=subprocess.run(['ssh','-i',str(args.key),'-o','BatchMode=yes',args.host,'python3','-'],
                          input=args.script.read_bytes())
    raise SystemExit(result.returncode)
if __name__=='__main__':main()
