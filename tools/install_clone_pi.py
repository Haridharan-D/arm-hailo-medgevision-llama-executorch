"""Install a user service and dual-monitor launchers for this checkout."""
import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Write launchers and enable/start the user service')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    home = Path.home()
    unit = home/'.config/systemd/user/blistertrace.service'
    launchers = [(home/'medge-vision', root/'tools/launch_monitors.py'),
                 (home/'medge-demo', root/'tools/medge_demo.py')]
    if not args.install:
        print('Checkout:', root, '\nService:', unit)
        print('Run with --install to install this checkout. Existing service/launchers are never overwritten.')
        return
    if sys.platform != 'linux':
        raise SystemExit('Run on Linux in the Pi desktop user session.')
    for target in [unit, *(pair[0] for pair in launchers)]:
        if target.exists():
            raise SystemExit('Existing installation retained: '+str(target))
    if any(c in str(root) for c in ['"', '%', '\n']):
        raise SystemExit('Checkout path must not contain quote, percent or newline characters.')
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text('[Unit]\nDescription=Medge Vision offline inspection\nAfter=graphical-session.target\n'
                    '[Service]\nType=simple\nWorkingDirectory="'+str(root)+'"\n'
                    'ExecStart="'+str(Path(sys.executable).resolve())+'" "'+str(root/'main.py')+'" --no-browser\n'
                    'Restart=on-failure\nRestartSec=5\nUMask=0077\nNoNewPrivileges=true\n'
                    '[Install]\nWantedBy=default.target\n')
    for target, script in launchers:
        target.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(script))+' "$@"\n')
        target.chmod(0o755)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', '--user', 'enable', '--now', 'blistertrace.service'], check=True)
    print('Installed. Run ~/medge-vision from the desktop terminal, or ~/medge-demo start.')


if __name__ == '__main__':
    main()
