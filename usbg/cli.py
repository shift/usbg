import argparse
import sys
from pathlib import Path
from .app import USBGuardApp
from .waybar import waybar_main
from .dbus_client import USBGuardDBus

def generate_policy(args):
    usbguard = USBGuardDBus()
    policy = usbguard.generate_policy()
    
    if args.output:
        Path(args.output).write_text(policy)
        print(f"Policy written to {args.output}")
    else:
        print(policy)

def list_devices(args):
    usbguard = USBGuardDBus()
    devices = usbguard.list_devices()
    
    for device in devices:
        status = {0: "ALLOW", 1: "BLOCK", 2: "REJECT"}[device['target']]
        print(f"[{device['id']}] {device['name']} - {status}")
        if args.verbose:
            print(f"  Port: {device['port']}")
            print(f"  Serial: {device['serial']}")
            print(f"  Rule: {device['rule']}")

def allow_device(args):
    usbguard = USBGuardDBus()
    usbguard.apply_device_policy(args.device_id, 0, args.permanent)
    print(f"Device {args.device_id} allowed{'(permanent)' if args.permanent else ''}")

def block_device(args):
    usbguard = USBGuardDBus()
    usbguard.apply_device_policy(args.device_id, 1, args.permanent)
    print(f"Device {args.device_id} blocked{'(permanent)' if args.permanent else ''}")

def main():
    parser = argparse.ArgumentParser(
        description="USBGuard Waybar Applet - Control USBGuard from Waybar and CLI"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    gui_parser = subparsers.add_parser('gui', help='Launch GUI application')
    
    waybar_parser = subparsers.add_parser('waybar', help='Waybar module output')
    waybar_parser.add_argument('--continuous', action='store_true',
                              help='Continuous output for waybar')
    
    gen_parser = subparsers.add_parser('generate-policy',
                                       help='Generate policy from current devices')
    gen_parser.add_argument('-o', '--output', help='Output file path')
    
    list_parser = subparsers.add_parser('list', help='List USB devices')
    list_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output')
    
    allow_parser = subparsers.add_parser('allow', help='Allow a device')
    allow_parser.add_argument('device_id', type=int, help='Device ID')
    allow_parser.add_argument('-p', '--permanent', action='store_true',
                             help='Make policy permanent')
    
    block_parser = subparsers.add_parser('block', help='Block a device')
    block_parser.add_argument('device_id', type=int, help='Device ID')
    block_parser.add_argument('-p', '--permanent', action='store_true',
                             help='Make policy permanent')
    
    args = parser.parse_args()
    
    if args.command == 'gui' or args.command is None:
        app = USBGuardApp()
        return app.run(sys.argv)
    elif args.command == 'waybar':
        waybar_main(args.continuous)
    elif args.command == 'generate-policy':
        generate_policy(args)
    elif args.command == 'list':
        list_devices(args)
    elif args.command == 'allow':
        allow_device(args)
    elif args.command == 'block':
        block_device(args)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
