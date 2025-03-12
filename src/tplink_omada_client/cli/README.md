# TP-Link Omada CLI Commands

This document describes the available commands in the TP-Link Omada CLI tool and their usage.

## Global Options

These options are available for all commands:

- `-t, --target`: Specify which controller configuration to use from `~/.omada/config.yaml`
- `-h, --help`: Show help message for the command

## Commands

### switch_port

Controls the enable/disable state of a switch port.

```bash
omada switch_port [-h] -p PORT (--enable | --disable) [--apply-schedule] [-d] mac
```

#### Arguments

- `mac`: The MAC address or name of the switch

#### Options

- `-p, --port`: The port number to control (required)
- `--enable`: Enable the port
  - If the port has a schedule: Disables the schedule
  - If no schedule: Temporarily sets port to Disable profile then restores original profile
- `--disable`: Disable the port
  - If `--apply-schedule` is used and port has a schedule: Enables the schedule
  - Otherwise: Sets port to Disable profile
- `--apply-schedule`: When disabling, use schedule if available instead of forcing port to Disable profile
- `-d, --dump`: Output raw port information

#### Examples

```bash
# Disable port 10 on switch with MAC xx-xx-xx-xx-xx-xx
omada switch_port -p 10 --disable xx-xx-xx-xx-xx-xx

# Enable port 10 and show the port details
omada switch_port -p 10 --enable --dump xx-xx-xx-xx-xx-xx

# Disable port 10 using its schedule (if available)
omada switch_port -p 10 --disable --apply-schedule xx-xx-xx-xx-xx-xx
```

### switch_ports

Lists all ports on a switch and their current status.

```bash
omada switch_ports [-h] [-d] mac
```

#### Arguments

- `mac`: The MAC address or name of the switch

#### Options

- `-d, --dump`: Output raw port information

#### Examples

```bash
# List all ports on switch with MAC xx-xx-xx-xx-xx-xx
omada switch_ports xx-xx-xx-xx-xx-xx

# List all ports with detailed information
omada switch_ports -d xx-xx-xx-xx-xx-xx
```

### devices

Lists all devices managed by the controller.

```bash
omada devices [-h] [-d]
```

#### Options

- `-d, --dump`: Output raw device information

#### Examples

```bash
# List all devices
omada devices

# List all devices with detailed information
omada devices -d
```

### sites

Lists all sites managed by the controller.

```bash
omada sites [-h] [-d]
```

#### Options

- `-d, --dump`: Output raw site information

#### Examples

```bash
# List all sites
omada sites

# List all sites with detailed information
omada sites -d
```

## Configuration

The CLI tool uses a configuration file located at `~/.omada/config.yaml`. This file should contain your controller connection details:

```yaml
default: # Default controller to use when -t/--target not specified
  host: omada.example.com
  username: admin
  password: admin_password
  site: Default # Site name to use
  verify_ssl: true # Whether to verify SSL certificates

other_controller: # Another controller configuration
  host: 192.168.1.100
  username: admin
  password: different_password
  site: Branch Office
  verify_ssl: false
```

You can specify which controller configuration to use with the `-t/--target` option:

```bash
omada -t other_controller switch_ports xx-xx-xx-xx-xx-xx
```
