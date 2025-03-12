"""Implementation for 'switch_port' command"""

from argparse import ArgumentParser
from tplink_omada_client.definitions import PoEMode
from tplink_omada_client.devices import OmadaDevice, OmadaSwitchPortDetails
from .config import get_target_config, to_omada_connection
from .util import dump_raw_data, get_device_mac, get_target_argument


def _preserve_port_settings(port_details: OmadaSwitchPortDetails) -> dict:
    """Create a payload that preserves current port settings"""
    payload = {
        "operation": port_details.operation,
        "linkSpeed": port_details.link_speed.value,
        "duplex": port_details.duplex.value,
        "dot1x": port_details.eth_802_1x_control.value,
        "poe": port_details.poe_mode.value,
        "bandWidthCtrlType": port_details.bandwidth_limit_mode.value,
        "lldpMedEnable": port_details.lldp_med_enabled,
        "spanningTreeEnable": port_details.spanning_tree_enabled,
        "loopbackDetectEnable": port_details.loopback_detect_enabled,
        "portIsolationEnable": port_details.port_isolation_enabled
    }

    # Add optional settings if they exist in the raw data
    if "topoNotifyEnable" in port_details._data:
        payload["topoNotifyEnable"] = port_details.topology_notify_enabled
    if "eeeEnable" in port_details._data:
        payload["eeeEnable"] = port_details._data["eeeEnable"]
    if "flowControlEnable" in port_details._data:
        payload["flowControlEnable"] = port_details._data["flowControlEnable"]
    if "fastLeaveEnable" in port_details._data:
        payload["fastLeaveEnable"] = port_details._data["fastLeaveEnable"]

    return payload


async def _get_disable_profile_id(site_client) -> str:
    """Get the ID of the Disable profile"""
    profiles = await site_client.get_port_profiles()
    for profile in profiles:
        if profile.name == "Disable":
            return profile.profile_id
    raise ValueError("Could not find Disable profile")


async def _enable_port_via_schedule(site_client, device: OmadaDevice, port: int) -> bool:
    """Enable port by disabling its schedule if it has one"""
    port_details = await site_client.get_switch_port(device, port)
    # Store the original profile ID before any changes
    original_profile = port_details.profile_id

    if port_details.has_schedule:
        # Disable the schedule to enable the port
        payload = _preserve_port_settings(port_details)
        payload["scheduleEnable"] = False
        await site_client.update_switch_port(
            device,
            port,
            overrides=payload
        )
        print(f"Port {port} enabled by disabling schedule")
        return True
    else:
        # No schedule exists, do a quick disable/enable cycle
        # Get the Disable profile ID
        disable_profile_id = await _get_disable_profile_id(site_client)

        # First disable the port by setting profile to Disable
        await site_client.update_switch_port(
            device,
            port,
            profile_id=disable_profile_id
        )
        print(f"Port {port} temporarily disabled")

        # Wait a moment to ensure the disable takes effect
        import asyncio
        await asyncio.sleep(1)

        # Then restore the original profile
        await site_client.update_switch_port(
            device,
            port,
            profile_id=original_profile
        )
        print(f"Port {port} re-enabled with original profile")

        # Refresh port status
        refreshed_port = await site_client.get_switch_port(device, port)
        print(f"Port {port} status: {'enabled' if not refreshed_port.is_disabled else 'disabled'}")
        return True


async def _disable_port_via_schedule(site_client, device: OmadaDevice, port: int, apply_schedule: bool) -> bool:
    """Disable port by enabling its schedule if it has one, otherwise disable the port directly"""
    port_details = await site_client.get_switch_port(device, port)

    if port_details.has_schedule and apply_schedule:
        # Enable the schedule to disable the port
        payload = _preserve_port_settings(port_details)
        payload["scheduleEnable"] = True
        await site_client.update_switch_port(
            device,
            port,
            overrides=payload
        )
        print(f"Port {port} disabled by enabling schedule")
        return True
    else:
        # No schedule exists or not using schedule, disable the port directly
        disable_profile_id = await _get_disable_profile_id(site_client)
        await site_client.update_switch_port(
            device,
            port,
            profile_id=disable_profile_id
        )
        print(f"Port {port} disabled via profile")
        return True


async def command_switch_port(args) -> int:
    """Executes 'switch_port' command"""
    controller = get_target_argument(args)
    config = get_target_config(controller)

    async with to_omada_connection(config) as client:
        site_client = await client.get_site_client(config.site)
        mac = await get_device_mac(site_client, args["mac"])
        device = await site_client.get_device(mac)
        port = int(args["port"])

        if args["enable"]:
            result = await _enable_port_via_schedule(site_client, device, port)
        elif args["disable"]:
            result = await _disable_port_via_schedule(site_client, device, port, args["apply_schedule"])

        if args["dump"]:
            # Get the updated port details for dumping
            port_details = await site_client.get_switch_port(device, port)
            dump_raw_data(args, port_details)
        return 0


def arg_parser(subparsers) -> None:
    """Configures arguments parser for 'switch_port' command"""
    switch_port_parser: ArgumentParser = subparsers.add_parser(
        "switch_port", help="Controls switch port enable/disable state"
    )
    switch_port_parser.set_defaults(func=command_switch_port)

    switch_port_parser.add_argument(
        "mac",
        help="The MAC address or name of the switch",
    )
    switch_port_parser.add_argument("-p", "--port", help="The port number to control", required=True)

    enable_disable_grp = switch_port_parser.add_mutually_exclusive_group(required=True)
    enable_disable_grp.add_argument(
        "--enable",
        help="Enable the port. If the port has a schedule, disables the schedule. Otherwise, temporarily sets port to Disable profile then restores original profile.",
        action="store_true"
    )
    enable_disable_grp.add_argument(
        "--disable",
        help="Disable the port. If --apply-schedule is used and port has a schedule, enables the schedule. Otherwise, sets port to Disable profile.",
        action="store_true"
    )

    switch_port_parser.add_argument(
        "--apply-schedule",
        help="When disabling, use schedule if available instead of forcing port to Disable profile",
        action="store_true"
    )
    switch_port_parser.add_argument("-d", "--dump", help="Output raw port information", action="store_true")
