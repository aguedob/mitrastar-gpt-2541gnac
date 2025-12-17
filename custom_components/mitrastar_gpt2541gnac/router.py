"""Router SSH client for Mitrastar GPT-2541GNAC."""
import asyncio
import logging
import re
from typing import Any

import asyncssh

_LOGGER = logging.getLogger(__name__)


class MitrastarRouter:
    """Handle SSH connection and data parsing for Mitrastar router."""

    def __init__(self, host: str, username: str, password: str):
        """Initialize the router connection."""
        self.host = host
        self.username = username
        self.password = password

    async def _execute_ssh_command(self, command: str) -> str:
        """Execute SSH command on the router using interactive session."""
        try:
            async with asyncssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                known_hosts=None,
                server_host_key_algs=['ssh-rsa'],
                encryption_algs=['aes128-ctr', 'aes192-ctr', 'aes256-ctr', 'aes128-cbc', 'aes192-cbc', 'aes256-cbc'],
                connect_timeout=10,
            ) as conn:
                # Create an interactive session with a PTY
                async with conn.create_process(term_type='vt100') as process:
                    # Wait for initial prompt
                    await asyncio.sleep(1)
                    
                    # Clear any initial output
                    try:
                        await asyncio.wait_for(process.stdout.read(65536), timeout=0.5)
                    except asyncio.TimeoutError:
                        pass
                    
                    # Send the command
                    process.stdin.write(f"{command}\n")
                    await process.stdin.drain()
                    
                    # Wait for command to execute
                    await asyncio.sleep(3)
                    
                    # Read all available output
                    output = ""
                    try:
                        # Try to read up to 1MB of data with timeout
                        output = await asyncio.wait_for(process.stdout.read(1048576), timeout=5)
                    except asyncio.TimeoutError:
                        _LOGGER.warning("Timeout reading command output")
                    
                    # Close the session
                    try:
                        process.stdin.write("exit\n")
                        await process.stdin.drain()
                    except:
                        pass
                    
                    _LOGGER.debug("Command '%s' output length: %d, first 500 chars: %s", 
                                 command, len(output), output[:500])
                    return output
        except asyncio.TimeoutError:
            _LOGGER.error("SSH command timed out")
            raise
        except asyncssh.Error as err:
            _LOGGER.error("SSH error: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error executing SSH command: %s", err)
            raise

    async def _execute_multiple_commands(self, commands: list[str]) -> dict[str, str]:
        """Execute multiple SSH commands in a single session."""
        results = {}
        try:
            async with asyncssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                known_hosts=None,
                server_host_key_algs=['ssh-rsa'],
                encryption_algs=['aes128-ctr', 'aes192-ctr', 'aes256-ctr', 'aes128-cbc', 'aes192-cbc', 'aes256-cbc'],
                connect_timeout=10,
            ) as conn:
                # Create an interactive session with a PTY
                async with conn.create_process(term_type='vt100') as process:
                    # Wait for initial prompt
                    await asyncio.sleep(1)
                    
                    # Clear any initial output
                    try:
                        await asyncio.wait_for(process.stdout.read(65536), timeout=0.5)
                    except asyncio.TimeoutError:
                        pass
                    
                    # Execute each command and collect output
                    for command in commands:
                        # Send the command
                        process.stdin.write(f"{command}\n")
                        await process.stdin.drain()
                        
                        # Wait for command to execute
                        await asyncio.sleep(2.5)
                        
                        # Read all available output
                        output = ""
                        try:
                            output = await asyncio.wait_for(process.stdout.read(1048576), timeout=4)
                        except asyncio.TimeoutError:
                            _LOGGER.warning("Timeout reading output for command: %s", command)
                        
                        results[command] = output
                        _LOGGER.debug("Command '%s' output length: %d", command, len(output))
                    
                    # Close the session
                    try:
                        process.stdin.write("exit\n")
                        await process.stdin.drain()
                    except:
                        pass
                    
        except asyncio.TimeoutError:
            _LOGGER.error("SSH session timed out")
            raise
        except asyncssh.Error as err:
            _LOGGER.error("SSH error: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error executing SSH commands: %s", err)
            raise
        
        return results

    async def test_connection(self) -> bool:
        """Test the SSH connection to the router."""
        try:
            output = await self._execute_ssh_command("lasercheck")
            return "Rx Optical Power" in output
        except Exception:
            return False

    async def get_device_info(self) -> dict[str, str]:
        """Get device information."""
        device_info = {}
        try:
            output = await self._execute_ssh_command("sys atsh")
            
            # Parse firmware version
            fw_match = re.search(r"MLD\s+Version\s+:\s+(.+)", output)
            if fw_match:
                device_info["sw_version"] = fw_match.group(1).strip()
            
            # Parse bootloader version
            boot_match = re.search(r"Bootbase Version\s+:\s+(.+)", output)
            if boot_match:
                device_info["hw_version"] = boot_match.group(1).strip()
            
            # Parse vendor name
            vendor_match = re.search(r"Vendor Name\s+:\s+(.+)", output)
            if vendor_match:
                device_info["manufacturer"] = vendor_match.group(1).strip()
            
            # Parse product model
            model_match = re.search(r"Product Model\s+:\s+(.+)", output)
            if model_match:
                device_info["model"] = model_match.group(1).strip()
            
            # Parse serial number
            serial_match = re.search(r"Serial Number\s+:\s+(.+)", output)
            if serial_match:
                device_info["serial_number"] = serial_match.group(1).strip()
                
        except Exception as err:
            _LOGGER.error("Error getting device info: %s", err)
        
        return device_info

    def _parse_lan_stats(self, output: str) -> dict[str, Any]:
        """Parse LAN statistics output."""
        data = {}
        lines = output.split("\n")

        current_section = None
        for line in lines:
            if "Received Counters:" in line:
                current_section = "rx"
                continue
            elif "Transmitted Counters:" in line:
                current_section = "tx"
                continue

            # Parse interface data
            match = re.match(
                r"\s+(\w+)\s+(Up|Disabled|Down)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
                line,
            )
            if match and current_section:
                interface = match.group(1)
                status = match.group(2)
                total_bytes = int(match.group(3))
                total_pkts = int(match.group(4))
                errors = int(match.group(5))
                drops = int(match.group(6))
                mcast_bytes = int(match.group(7))
                mcast_pkts = int(match.group(8))
                ucast_pkts = int(match.group(9))
                bcast_pkts = int(match.group(10))

                key_prefix = f"lan_{interface}_{current_section}"
                data[f"{key_prefix}_status"] = status
                data[f"{key_prefix}_total_bytes"] = total_bytes
                data[f"{key_prefix}_total_packets"] = total_pkts
                data[f"{key_prefix}_errors"] = errors
                data[f"{key_prefix}_drops"] = drops
                data[f"{key_prefix}_multicast_bytes"] = mcast_bytes
                data[f"{key_prefix}_multicast_packets"] = mcast_pkts
                data[f"{key_prefix}_unicast_packets"] = ucast_pkts
                data[f"{key_prefix}_broadcast_packets"] = bcast_pkts

        return data

    def _parse_wan_stats(self, output: str) -> dict[str, Any]:
        """Parse WAN statistics output."""
        data = {}
        lines = output.split("\n")

        current_section = None
        for line in lines:
            if "Received Counters:" in line:
                current_section = "rx"
                continue
            elif "Transmitted Counters:" in line:
                current_section = "tx"
                continue

            # Parse interface data
            match = re.match(
                r"\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
                line,
            )
            if match and current_section:
                interface = match.group(1)
                vlan_id = match.group(2)
                total_bytes = int(match.group(3))
                total_pkts = int(match.group(4))
                errors = int(match.group(5))
                drops = int(match.group(6))
                mcast_bytes = int(match.group(7))
                mcast_pkts = int(match.group(8))
                ucast_pkts = int(match.group(9))
                bcast_pkts = int(match.group(10))

                key_prefix = f"wan_{interface}_{current_section}"
                data[f"{key_prefix}_vlan_id"] = vlan_id
                data[f"{key_prefix}_total_bytes"] = total_bytes
                data[f"{key_prefix}_total_packets"] = total_pkts
                data[f"{key_prefix}_errors"] = errors
                data[f"{key_prefix}_drops"] = drops
                data[f"{key_prefix}_multicast_bytes"] = mcast_bytes
                data[f"{key_prefix}_multicast_packets"] = mcast_pkts
                data[f"{key_prefix}_unicast_packets"] = ucast_pkts
                data[f"{key_prefix}_broadcast_packets"] = bcast_pkts

        return data

    def _parse_laser_stats(self, output: str) -> dict[str, Any]:
        """Parse laser check output."""
        data = {}

        # Parse optical power
        rx_power_match = re.search(r"Rx Optical Power\s+=\s+([-\d.]+)\s+dBm", output)
        if rx_power_match:
            data["laser_rx_power"] = float(rx_power_match.group(1))

        tx_power_match = re.search(r"Tx Optical Power\s+=\s+([-\d.]+)\s+dBm", output)
        if tx_power_match:
            data["laser_tx_power"] = float(tx_power_match.group(1))

        # Parse bias current
        bias_match = re.search(r"Tx Bias Current\s+=\s+([-\d.]+)\s+mA", output)
        if bias_match:
            data["laser_bias_current"] = float(bias_match.group(1))

        # Parse supply voltage
        voltage_match = re.search(r"Supply voltage\s+=\s+([-\d.]+)\s+V", output)
        if voltage_match:
            data["laser_voltage"] = float(voltage_match.group(1))

        # Parse temperature
        temp_match = re.search(r"SFF Temperature\s+=\s+([-\d.]+)\s+C", output)
        if temp_match:
            data["laser_temperature"] = float(temp_match.group(1))

        return data

    async def get_all_data(self) -> dict[str, Any]:
        """Fetch all data from the router in a single SSH session."""
        all_data = {}

        try:
            # Execute all commands in one SSH session
            commands = ["showlanstats", "showwanstats", "lasercheck"]
            results = await self._execute_multiple_commands(commands)
            
            # Parse LAN stats
            if "showlanstats" in results:
                lan_data = self._parse_lan_stats(results["showlanstats"])
                _LOGGER.debug("Parsed LAN data: %s keys", len(lan_data))
                all_data.update(lan_data)
            
            # Parse WAN stats
            if "showwanstats" in results:
                wan_data = self._parse_wan_stats(results["showwanstats"])
                _LOGGER.debug("Parsed WAN data: %s keys", len(wan_data))
                all_data.update(wan_data)
            
            # Parse laser stats
            if "lasercheck" in results:
                laser_data = self._parse_laser_stats(results["lasercheck"])
                _LOGGER.debug("Parsed laser data: %s keys", len(laser_data))
                all_data.update(laser_data)
                
        except Exception as err:
            _LOGGER.error("Error getting router data: %s", err)

        _LOGGER.info("Total data keys collected: %s, sample: %s", len(all_data), list(all_data.keys())[:5])
        return all_data
