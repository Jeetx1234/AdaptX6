"""
Server and Fan Management System - FULL AI CONTROL
===================================================
AI has full control with no restrictions.
Optimizes aggressively for maximum efficiency.
Supports 10 virtual servers + 4 real phone servers.
"""

from utils.phone_server import PhoneServer
from utils.adb_manager import get_connected_devices
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time
import numpy as np


@dataclass
class ServerStatus:
    """Status of a single server."""
    server_id: int
    name: str
    is_online: bool
    fan_speed: int
    temperature: float
    cpu_load: float
    last_action: str
    last_action_time: float


class ServerManager:
    """
    Manages 10 virtual servers + connected phones.
    AI optimizes for efficiency and fan control.
    """
    
    NUM_SERVERS = 10  # virtual servers
    MIN_SERVERS = 2
    
    # Temperature thresholds for fan control
    TEMP_COLD = 28
    TEMP_COOL = 32
    TEMP_WARM = 38
    TEMP_HOT = 45
    TEMP_VERY_HOT = 55
    TEMP_CRITICAL = 65
    
    # Workload thresholds
    WORKLOAD_VERY_LOW = 20
    WORKLOAD_LOW = 35
    WORKLOAD_OPTIMAL = 55
    WORKLOAD_HIGH = 75
    WORKLOAD_VERY_HIGH = 90
    
    def __init__(self):
        """Initialize server manager."""
        self.servers: Dict[int, ServerStatus] = {}
        self._initialize_servers()
        self.action_history: List[str] = []

        # Detect connected phones
        self.phone_servers: List[PhoneServer] = []
        devices = get_connected_devices()
        for device in devices[:4]:  # limit to 4 phones
            self.phone_servers.append(PhoneServer(device))

        # Combined list for dashboard/AI reference
        self.all_servers = list(self.servers.values()) + self.phone_servers
    
    def _initialize_servers(self):
        """Create all 10 virtual servers."""
        for i in range(self.NUM_SERVERS):
            self.servers[i] = ServerStatus(
                server_id=i,
                name=f"Server {i + 1}",
                is_online=True,
                fan_speed=2,
                temperature=32.0,
                cpu_load=50.0,
                last_action="Initialized",
                last_action_time=time.time()
            )

    # -------------------------
    # Server control methods
    # -------------------------
    def get_active_count(self) -> int:
        """Get count of online virtual servers."""
        return sum(1 for s in self.servers.values() if s.is_online)

    def set_server_online(self, server_id: int, online: bool, actor: str = "Manual") -> Tuple[bool, str]:
        """
        Set a server's online status.
        Works for virtual servers AND phone servers.
        """
        # Phone server IDs are NUM_SERVERS+
        if server_id >= self.NUM_SERVERS:
            phone_index = server_id - self.NUM_SERVERS
            if phone_index >= len(self.phone_servers):
                return False, f"Phone server {server_id} does not exist"
            phone = self.phone_servers[phone_index]

            if online:
                phone.screen_on()
            else:
                phone.screen_off()

            action = f"{actor}: Phone S{server_id + 1} → {'ON' if online else 'OFF'}"
            self.action_history.append(action)
            if len(self.action_history) > 50:
                self.action_history.pop(0)
            return True, action

        # Virtual server
        if server_id not in self.servers:
            return False, f"Server {server_id} does not exist"
        
        server = self.servers[server_id]
        if not online and self.get_active_count() <= self.MIN_SERVERS:
            return False, f"Minimum {self.MIN_SERVERS} servers required"
        
        old_state = server.is_online
        server.is_online = online
        
        if not online:
            server.fan_speed = 0
        elif online and not old_state:
            server.fan_speed = 2
            
        server.last_action = f"{'ON' if online else 'OFF'} by {actor}"
        server.last_action_time = time.time()
        
        action = f"{actor}: Server {server_id + 1} → {'ON' if online else 'OFF'}"
        self.action_history.append(action)
        if len(self.action_history) > 50:
            self.action_history.pop(0)
        
        return True, action

    def set_fan_speed(self, server_id: int, speed: int, actor: str = "Manual") -> Tuple[bool, str]:
        """Set a fan's speed level for virtual servers only."""
        if server_id not in self.servers:
            return False, f"Server {server_id} does not exist"
        if not 0 <= speed <= 3:
            return False, f"Invalid speed: {speed}"
        
        server = self.servers[server_id]
        if not server.is_online and speed > 0:
            return False, f"Server {server_id + 1} is offline"
        
        old_speed = server.fan_speed
        server.fan_speed = speed
        speed_names = {0: "OFF", 1: "LOW", 2: "MED", 3: "HIGH"}
        server.last_action = f"Fan → {speed_names[speed]} by {actor}"
        server.last_action_time = time.time()
        
        action = f"{actor}: S{server_id + 1} fan → {speed_names[speed]}"
        self.action_history.append(action)
        if len(self.action_history) > 50:
            self.action_history.pop(0)
        
        return True, action

    # -------------------------
    # Phone metrics
    # -------------------------
    def get_phone_temperatures(self) -> Dict[int, float]:
        temps = {}
        for idx, phone in enumerate(self.phone_servers):
            temps[self.NUM_SERVERS + idx] = phone.get_temperature()
        return temps

    def get_phone_battery_levels(self) -> Dict[int, int]:
        battery = {}
        for idx, phone in enumerate(self.phone_servers):
            battery[self.NUM_SERVERS + idx] = phone.get_battery()
        return battery

