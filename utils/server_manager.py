"""
Server and Fan Management System - FULL AI CONTROL
===================================================
AI has full control with no restrictions.
Optimizes aggressively for maximum efficiency.
"""

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
    Manages 10 servers with full AI control.
    No threshold restrictions - AI optimizes aggressively.
    """
    
    NUM_SERVERS = 10
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
        
    def _initialize_servers(self):
        """Create all 10 servers."""
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
    
    def get_active_count(self) -> int:
        """Get count of online servers."""
        return sum(1 for s in self.servers.values() if s.is_online)
    
    def set_server_online(self, server_id: int, online: bool, 
                          actor: str = "Manual") -> Tuple[bool, str]:
        """Set a server's online status."""
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
    
    def set_fan_speed(self, server_id: int, speed: int,
                      actor: str = "Manual") -> Tuple[bool, str]:
        """Set a fan's speed level."""
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
    
    def sync_with_simulator(self, simulator):
        """Sync manager state with simulator."""
        for i in range(self.NUM_SERVERS):
            self.servers[i].is_online = simulator.server_states[i]
            self.servers[i].fan_speed = simulator.fan_states[i]
            self.servers[i].temperature = simulator.server_temperatures[i]
            self.servers[i].cpu_load = simulator.server_cpu_loads[i]
    
    def get_optimal_fan_for_temp(self, temperature: float) -> int:
        """Get optimal fan speed for a given temperature."""
        if temperature >= self.TEMP_CRITICAL:
            return 3  # MAX
        elif temperature >= self.TEMP_VERY_HOT:
            return 3
        elif temperature >= self.TEMP_HOT:
            return 2
        elif temperature >= self.TEMP_WARM:
            return 2
        elif temperature >= self.TEMP_COOL:
            return 1
        elif temperature >= self.TEMP_COLD:
            return 1
        else:
            return 0  # Very cold, save energy
    
    def get_optimal_server_count(self, workload: float) -> int:
        """Get optimal number of servers for workload."""
        # Target: ~50-60% load per server for best efficiency
        optimal_load_per_server = 5.5  # workload units per server
        optimal_count = int(np.ceil(workload / optimal_load_per_server))
        return np.clip(optimal_count, self.MIN_SERVERS, self.NUM_SERVERS)
    
    def _simulate_changes(self, simulator, server_changes: Dict, 
                          fan_changes: Dict) -> float:
        """Simulate efficiency after changes."""
        test_sim = simulator.clone()
        
        for server_id, state in server_changes.items():
            test_sim.set_server_state(server_id, state)
        
        for server_id, speed in fan_changes.items():
            test_sim.set_fan_state(server_id, speed)
        
        test_sim._distribute_workload()
        test_sim._update_all_temperatures()
        test_sim._update_energy()
        
        return test_sim.calculate_current_efficiency()
    
    def ai_full_control(self, simulator, current_efficiency: float) -> Dict:
        """
        AI FULL CONTROL - Optimizes aggressively.
        No threshold restrictions - takes ANY action that improves efficiency.
        """
        state = simulator.get_state()
        server_states = state['server_states']
        fan_states = state['fan_states']
        temperatures = state['server_temperatures']
        cpu_loads = state['server_cpu_loads']
        workload = state['workload']
        active_servers = state['servers']
        
        result = {
            'actions': [],
            'server_changes': {},
            'fan_changes': {},
            'reasoning': [],
            'predicted_efficiency': current_efficiency,
            'should_act': False
        }
        
        best_efficiency = current_efficiency
        best_server_changes = {}
        best_fan_changes = {}
        
        # === STRATEGY 1: Optimize Fan Speeds Based on Temperature ===
        fan_changes_temp = {}
        for i in range(self.NUM_SERVERS):
            if server_states[i]:
                temp = temperatures[i]
                current_fan = fan_states[i]
                optimal_fan = self.get_optimal_fan_for_temp(temp)
                
                if optimal_fan != current_fan:
                    fan_changes_temp[i] = optimal_fan
        
        if fan_changes_temp:
            eff = self._simulate_changes(simulator, {}, fan_changes_temp)
            if eff > best_efficiency:
                best_efficiency = eff
                best_server_changes = {}
                best_fan_changes = fan_changes_temp.copy()
                result['reasoning'].append(f"🌡️ Optimize fans for temperature: {eff:.1f}%")
        
        # === STRATEGY 2: Optimize Server Count ===
        optimal_servers = self.get_optimal_server_count(workload)
        
        if optimal_servers < active_servers:
            # Turn off excess servers
            online_servers = [i for i in range(self.NUM_SERVERS) if server_states[i]]
            servers_to_off = active_servers - optimal_servers
            
            # Turn off servers with lowest load first
            sorted_servers = sorted(online_servers, key=lambda i: cpu_loads[i])
            
            for count in range(1, min(servers_to_off + 1, active_servers - self.MIN_SERVERS + 1)):
                server_changes = {sorted_servers[j]: False for j in range(count)}
                eff = self._simulate_changes(simulator, server_changes, fan_changes_temp)
                
                if eff > best_efficiency:
                    best_efficiency = eff
                    best_server_changes = server_changes.copy()
                    best_fan_changes = fan_changes_temp.copy()
                    result['reasoning'].append(f"📉 Turn off {count} server(s): {eff:.1f}%")
        
        elif optimal_servers > active_servers:
            # Turn on more servers
            offline_servers = [i for i in range(self.NUM_SERVERS) if not server_states[i]]
            servers_to_on = optimal_servers - active_servers
            
            for count in range(1, min(servers_to_on + 1, len(offline_servers) + 1)):
                server_changes = {offline_servers[j]: True for j in range(count)}
                eff = self._simulate_changes(simulator, server_changes, {})
                
                if eff > best_efficiency:
                    best_efficiency = eff
                    best_server_changes = server_changes.copy()
                    best_fan_changes = {}
                    result['reasoning'].append(f"📈 Turn on {count} server(s): {eff:.1f}%")
        
        # === STRATEGY 3: Emergency Cooling ===
        max_temp = max(temperatures[i] for i in range(self.NUM_SERVERS) if server_states[i]) if active_servers > 0 else 22
        
        if max_temp > self.TEMP_VERY_HOT:
            emergency_fans = {}
            for i in range(self.NUM_SERVERS):
                if server_states[i] and fan_states[i] < 3:
                    emergency_fans[i] = 3
            
            if emergency_fans:
                eff = self._simulate_changes(simulator, {}, emergency_fans)
                # For emergency, don't require efficiency improvement
                if max_temp > self.TEMP_CRITICAL or eff >= best_efficiency:
                    best_efficiency = eff
                    best_server_changes = {}
                    best_fan_changes = emergency_fans
                    result['reasoning'].append(f"🚨 Emergency cooling (temp: {max_temp:.1f}°C)")
        
        # === STRATEGY 4: Energy Saving When Cool ===
        if max_temp < self.TEMP_COOL:
            energy_save_fans = {}
            for i in range(self.NUM_SERVERS):
                if server_states[i] and fan_states[i] > 1:
                    energy_save_fans[i] = 1
            
            if energy_save_fans:
                eff = self._simulate_changes(simulator, {}, energy_save_fans)
                if eff > best_efficiency:
                    best_efficiency = eff
                    best_server_changes = {}
                    best_fan_changes = energy_save_fans
                    result['reasoning'].append(f"💚 Energy saving mode: {eff:.1f}%")
        
        # === STRATEGY 5: Combined Optimization ===
        if best_server_changes or best_fan_changes:
            combined_eff = self._simulate_changes(simulator, best_server_changes, best_fan_changes)
            if combined_eff > best_efficiency:
                best_efficiency = combined_eff
                result['reasoning'].append(f"🔄 Combined optimization: {combined_eff:.1f}%")
        
        # === APPLY BEST STRATEGY ===
        improvement = best_efficiency - current_efficiency
        
        if best_server_changes or best_fan_changes:
            result['should_act'] = True
            result['server_changes'] = best_server_changes
            result['fan_changes'] = best_fan_changes
            result['predicted_efficiency'] = best_efficiency
            
            sign = "+" if improvement >= 0 else ""
            result['reasoning'].append(f"✅ Applying changes: {sign}{improvement:.2f}%")
            
            # Generate action descriptions
            speed_names = {0: "OFF", 1: "LOW", 2: "MED", 3: "HIGH"}
            
            for server_id, state in best_server_changes.items():
                action = f"🖥️ S{server_id+1} → {'ON' if state else 'OFF'}"
                result['actions'].append(action)
            
            for server_id, speed in best_fan_changes.items():
                action = f"🌀 S{server_id+1} fan → {speed_names[speed]}"
                result['actions'].append(action)
        else:
            result['reasoning'].append("✅ System already optimized")
        
        return result
    
    def apply_ai_actions(self, result: Dict, simulator) -> List[str]:
        """Apply AI actions to simulator."""
        if not result['should_act']:
            return []
        
        actions_taken = []
        
        for server_id, state in result['server_changes'].items():
            success, msg = self.set_server_online(server_id, state, "AI")
            if success:
                simulator.set_server_state(server_id, state)
                actions_taken.append(msg)
        
        for server_id, speed in result['fan_changes'].items():
            success, msg = self.set_fan_speed(server_id, speed, "AI")
            if success:
                simulator.set_fan_state(server_id, speed)
                actions_taken.append(msg)
        
        return actions_taken