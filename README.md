# USBG - USBGuard Waybar Applet

A Wayland/Waybar compatible applet for controlling USBGuard with a GTK4 GUI interface.

## Features

- **Waybar Integration**: Custom module that displays USB device status
- **GTK4 GUI**: Modern interface for managing USB devices
- **Device Control**: Allow, block, or reject USB devices
- **Policy Management**: Generate and edit USBGuard policies
- **D-Bus Integration**: Communicates with USBGuard daemon via D-Bus
- **CLI Tools**: Command-line interface for device management
- **NixOS Integration**: Fully integrated with Nix flakes

## Requirements

- NixOS or Nix package manager
- USBGuard daemon running
- Wayland compositor (for GUI)
- Waybar (optional, for status bar integration)

## Installation

### Using Nix Flakes

```bash
nix profile install github:shift/usbg
```

### From Source

```bash
git clone https://github.com/shift/usbg.git
cd usbg
nix build
```

## NixOS Integration

If using flakes, add USBG to your flake inputs:

```nix
{
  inputs = {
    # ... other inputs
    usbg.url = "github:shift/usbg";
  };

  outputs = { self, nixpkgs, usbg, ... }: {
    nixosConfigurations.yourhost = nixpkgs.lib.nixosSystem {
      modules = [
        usbg.nixosModules.default
        {
          services.usbg = {
            enable = true;
            waybar.enable = true;
            systemdUserService = true;
          };
        }
        # ... other modules
      ];
    };
  };
}
```

For non-flake setups, add the module directly:

```nix
{ config, pkgs, ... }:

{
  imports = [
    (builtins.fetchTarball "https://github.com/shift/usbg/archive/main.tar.gz")
  ];

  services.usbg = {
    enable = true;
    waybar.enable = true;
    systemdUserService = true;
  };
}
```

## Home Manager Integration

For Home Manager users (recommended if Waybar is managed via Home Manager):

```nix
{
  inputs = {
    # ... other inputs
    usbg.url = "github:shift/usbg";
  };

  outputs = { self, nixpkgs, home-manager, usbg, ... }: {
    homeConfigurations.youruser = home-manager.lib.homeManagerConfiguration {
      modules = [
        usbg.homeManagerModules.default
        {
          services.usbg = {
            enable = true;
            waybar.enable = true;
            systemdUserService = true;
          };
        }
        # ... other modules
      ];
    };
  };
}
```

**Note**: You'll still need the NixOS module for USBGuard daemon and D-Bus permissions. Use both modules together for full integration.

## Usage

### Development Environment

**IMPORTANT**: Before running commands, enter the Nix development shell:

```bash
nix develop
```

Or use direnv (recommended):

```bash
direnv allow
```

If you're not in the devShell, you'll need to run commands with:

```bash
nix develop -c -- <command>
```

### GUI Application

Launch the graphical interface:

```bash
usbg gui
```

Or simply:

```bash
usbg
```

### Waybar Integration

Add to your Waybar configuration (`~/.config/waybar/config`):

```json
{
  "modules-right": ["custom/usbguard"],
  "custom/usbguard": {
    "exec": "usbg waybar --continuous",
    "return-type": "json",
    "interval": "once",
    "tooltip": true,
    "on-click": "usbg gui"
  }
}
```

### CLI Commands

List all USB devices:

```bash
usbg list
usbg list -v  # verbose output
```

Allow a device:

```bash
usbg allow <device-id>
usbg allow <device-id> --permanent
```

Block a device:

```bash
usbg block <device-id>
usbg block <device-id> --permanent
```

Generate policy from current devices:

```bash
usbg generate-policy
usbg generate-policy -o /etc/usbguard/rules.conf
```

### Systemd User Service

Install the systemd user service for automatic Waybar integration:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/usbg-waybar.service ~/.config/systemd/user/
systemctl --user enable --now usbg-waybar.service
```

## Configuration

Configuration file location: `~/.config/usbg/config.json`

Default configuration:

```json
{
  "waybar": {
    "update_interval": 2,
    "show_tooltip": true,
    "show_notifications": true
  },
  "gui": {
    "start_minimized": false,
    "enable_system_tray": true
  },
  "usbguard": {
    "auto_allow_known": false,
    "notification_on_block": true
  }
}
```

## Building

Build the project:

```bash
nix build
```

Run checks:

```bash
nix flake check
```

## Development

Enter the development shell:

```bash
nix develop
```

The development environment includes:
- Python 3 with PyGObject and dbus-python
- GTK4 and libadwaita
- USBGuard tools
- All necessary build dependencies

Run the application in development mode:

```bash
python -m usbg
```

## USBGuard Setup

Ensure USBGuard daemon is running:

```bash
systemctl status usbguard
```

If not running, start it:

```bash
sudo systemctl start usbguard
sudo systemctl enable usbguard
```

### D-Bus Permissions

You may need to configure D-Bus permissions for your user to access USBGuard.

Create `/etc/dbus-1/system.d/usbguard.conf`:

```xml
<!DOCTYPE busconfig PUBLIC
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy user="shift">
    <allow send_destination="org.usbguard1"/>
  </policy>
</busconfig>
```

## Project Structure

```
usbg/
├── flake.nix              # Nix flake configuration
├── pyproject.toml         # Python package configuration
├── usbg/
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Main entry point
│   ├── app.py             # GTK4 GUI application
│   ├── cli.py             # CLI argument parser
│   ├── config.py          # Configuration management
│   ├── dbus_client.py     # USBGuard D-Bus interface
│   └── waybar.py          # Waybar module output
└── systemd/
    └── usbg-waybar.service # Systemd user service
```

## Troubleshooting

### Cannot connect to USBGuard D-Bus

- Ensure USBGuard daemon is running: `systemctl status usbguard`
- Check D-Bus permissions (see D-Bus Permissions section above)
- Verify your user has appropriate PolicyKit permissions

### GUI doesn't start

- Make sure you're running a Wayland compositor
- Check GTK4 and libadwaita are available
- Run from Nix devShell: `nix develop -c -- usbg gui`

### Waybar module not updating

- Check the systemd service: `systemctl --user status usbg-waybar`
- Verify Waybar configuration syntax
- Check logs: `journalctl --user -u usbg-waybar`

## Contributing

Contributions are welcome! Please ensure:

- Code follows Python conventions
- All changes work within Nix build system
- No binaries are committed to the repository
- Tests are included for new features

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [USBGuard](https://usbguard.github.io/) - USB device authorization framework
- [Waybar](https://github.com/Alexays/Waybar) - Highly customizable Wayland bar
- [GTK4](https://www.gtk.org/) - GUI toolkit
