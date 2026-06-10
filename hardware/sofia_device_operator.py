import os
import sys
import time
import socket
import subprocess
from datetime import datetime


class SofiaDeviceOperator:
    """
    Sofia Device Operator: Network telemetry and device state monitoring framework.
    
    Handles device discovery via MAC address, ARP cache resolution, and continuous
    network availability monitoring with cross-platform compatibility.
    """
    
    def __init__(self, device_name: str, mac_address: str):
        """
        Initialize the Sofia Device Operator.
        
        Args:
            device_name (str): Friendly name for the target device
            mac_address (str): MAC address of the target device (format: XX:XX:XX:XX:XX:XX)
        """
        self.device_name = device_name
        self.mac_address = mac_address.upper().replace("-", ":")
        self.ip_address = None
        self.is_active = False
        
    def _get_platform_ping_param(self) -> list:
        """
        Determines cross-platform ping parameters and timeout constraints.
        
        Returns:
            list: Platform-optimized ping command parameters
        """
        if os.name == "nt":
            return ["ping", "-n", "1", "-w", "800"]
        # Linux / Darwin / Termux / Pydroid 3 environment compliance
        return ["ping", "-c", "1", "-W", "1"]

    def _discover_local_subnet_base(self) -> str:
        """
        Dynamically extracts Sofia's current local IP to derive the active /24 subnet.
        
        Returns:
            str: Local subnet base (e.g., '192.168.1.') or None if discovery fails
        """
        try:
            # Open a dummy socket to a public address to determine active interface local IP
            # (Does not actually transmit packets out to the internet)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Extract the base subnet (e.g., '192.168.1.')
            if local_ip and local_ip.count(".") == 3:
                return ".".join(local_ip.split(".")[:3]) + "."
        except Exception:
            pass
        return None

    def force_subnet_broadcast(self):
        """
        Forces dynamic local network pings to populate the system's ARP neighbor table.
        Pings critical network nodes to force immediate ARP table synchronization.
        """
        try:
            param = self._get_platform_ping_param()
            subnet_base = self._discover_local_subnet_base()
            
            if subnet_base:
                # Ping the derived network gateway (.1) and common node boundaries
                # to force immediate ARP table synchronization without full sequential 254-node sweeps
                critical_nodes = [f"{subnet_base}1", f"{subnet_base}254", f"{subnet_base}255"]
                for target in critical_nodes:
                    subprocess.Popen(param + [target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Fallback to hardcoded industry standards if network interfaces are deeply isolated
                fallback_ips = ["192.168.1.1", "192.168.0.1", "10.0.0.1", "11.0.0.1"]
                for gateway in fallback_ips:
                    subprocess.Popen(param + [gateway], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass  # Guarantees loop stability if terminal thread execution permissions are constrained

    def resolve_ip_from_arp(self) -> str:
        """
        Scans local ARP caches and network routing tables to map the MAC address to an IP.
        
        Returns:
            str: Resolved IP address or None if not found
        """
        target_mac_clean = self.mac_address.lower()
        target_mac_alt = self.mac_address.replace(":", "-").lower()
        
        try:
            try:
                output = subprocess.check_output(["arp", "-a"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Linux net-tools replacement fallback (handles modern Linux kernels / Termux backends)
                output = subprocess.check_output(["ip", "neigh"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")

            for line in output.splitlines():
                line_lower = line.lower()
                if target_mac_clean in line_lower or target_mac_alt in line_lower:
                    parts = line_lower.replace("(", "").replace(")", "").split()
                    for part in parts:
                        if part.count(".") == 3:  # Validating standard dot-decimal IPv4 format
                            clean_ip = "".join(c for c in part if c.isdigit() or c == '.')
                            if clean_ip.endswith('.'): 
                                clean_ip = clean_ip[:-1]
                            self.ip_address = clean_ip
                            return self.ip_address
        except Exception as e:
            print(f"[Sofia Core Error] Shielding Exception during ARP parsing: {e}", file=sys.stderr)
        
        return None

    def ping_device(self) -> bool:
        """
        Executes a localized verification ping using platform-optimized protocols.
        
        Returns:
            bool: True if device is reachable, False otherwise
        """
        if not self.ip_address:
            self.resolve_ip_from_arp()
            
        if not self.ip_address:
            # Trigger dynamic subnet lookup to force neighbor tables to update
            self.force_subnet_broadcast()
            self.resolve_ip_from_arp()
            
        if not self.ip_address:
            self.is_active = False
            return False

        command = self._get_platform_ping_param() + [self.ip_address]
        
        try:
            result = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.is_active = (result == 0)
        except Exception:
            self.is_active = False
            
        return self.is_active

    def execute_symbiotic_loop(self, interval_seconds: int = 10):
        """
        Main continuous telemetry framework monitoring device state logic.
        
        Args:
            interval_seconds (int): Polling interval in seconds (default: 10)
        """
        print(f"[Sofia Core] Initializing Operator for {self.device_name} [{self.mac_address}]")
        print("[Sovereign Systems Architecture: Network Telemetry Active]")
        print("-" * 65)
        
        try:
            while True:
                is_online = self.ping_device()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if is_online:
                    print(f"[{timestamp}] [STATUS: ONLINE] Sofia communicating with {self.device_name} at IP: {self.ip_address}")
                else:
                    print(f"[{timestamp}] [STATUS: OFFLINE] {self.device_name} hardware layer unreachable.")
                    # Force target flushing to dynamically catch new DHCP lease assignments on re-entry
                    self.ip_address = None
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n[Sofia Core] Device Operator safely terminated by administrative command.")


if __name__ == "__main__":
    # Target Hardware Layer Address
    TARGET_MAC = "41:42:FF:B7:0D:88"
    
    # Initialize Core Node Tracking Configuration
    operator = SofiaDeviceOperator(device_name="Lingo_Node_Alpha", mac_address=TARGET_MAC)
    operator.execute_symbiotic_loop(interval_seconds=10)
