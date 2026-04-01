"""
Infrastructure Simulation Engine - PER-SERVER TEMPERATURE
==========================================================
Each server has its own temperature that responds to its fan.
Realistic thermal dynamics with proper cooling effects.
"""

import numpy as np
from typing import Dict, List
import time


class InfrastructureSimulator:
    """
    Simulates realistic data center with per-server temperature.
    Each server has independent thermal behavior.
    """
    
    NUM_SERVERS = 10
    
    # Energy constants
    BASE_ENERGY_PER_SERVER = 45          # Watts idle
    MAX_ENERGY_PER_SERVER = 120          # Watts full load
    ENERGY_PER_FAN_LEVEL = 8             # Watts per fan level
    
    # Temperature constants  
    AMBIENT_TEMP = 22.0                  # Room temperature
    MAX_TEMP = 75.0                      # Maximum temperature
    
    # Per-server thermal constants
    HEAT_GENERATION_RATE = 0.4           # Heat per CPU% per step
    COOLING_PER_FAN_LEVEL = 0.8          # Cooling per fan level per step
    NATURAL_COOLING_RATE = 0.05          # Natural heat dissipation
    THERMAL_INERTIA = 0.85               # How slowly temperature changes
    
    def __init__(self):
        """Initialize the simulator."""
        self.reset()
        
    def reset(self):
        """Reset simulator to initial state."""
        # Server states: True = ON, False = OFF
        self.server_states = [True] * self.NUM_SERVERS
        
        # Fan states: 0=OFF, 1=LOW, 2=MEDIUM, 3=HIGH
        self.fan_states = [2] * self.NUM_SERVERS
        
        # Per-server metrics
        self.server_temperatures = [32.0] * self.NUM_SERVERS  # Individual temps
        self.server_cpu_loads = [50.0] * self.NUM_SERVERS     # Individual CPU loads
        
        # Global metrics
        self.workload = 50.0
        self.energy = 600.0
        
        # Time tracking
        self.time_step = 0
        
        # Workload pattern variables
        self.workload_base = 50.0
        self.workload_trend = 0.0
        self.workload_phase = 0.0
        self.trend_duration = 0
        
    def get_active_servers(self) -> int:
        """Return count of active servers."""
        return sum(self.server_states)
    
    def get_active_fans(self) -> int:
        """Return count of fans that are ON."""
        return sum(1 for i, speed in enumerate(self.fan_states) 
                   if speed > 0 and self.server_states[i])
    
    def get_average_temperature(self) -> float:
        """Get average temperature of active servers."""
        active_temps = [self.server_temperatures[i] 
                        for i in range(self.NUM_SERVERS) 
                        if self.server_states[i]]
        if active_temps:
            return sum(active_temps) / len(active_temps)
        return self.AMBIENT_TEMP
    
    def get_max_temperature(self) -> float:
        """Get maximum temperature among active servers."""
        active_temps = [self.server_temperatures[i] 
                        for i in range(self.NUM_SERVERS) 
                        if self.server_states[i]]
        if active_temps:
            return max(active_temps)
        return self.AMBIENT_TEMP
    
    def get_cpu_usage(self) -> float:
        """Get average CPU usage of active servers."""
        active_cpus = [self.server_cpu_loads[i] 
                       for i in range(self.NUM_SERVERS) 
                       if self.server_states[i]]
        if active_cpus:
            return sum(active_cpus) / len(active_cpus)
        return 0.0
    
    def set_server_state(self, server_id: int, state: bool) -> bool:
        """Set a server's power state."""
        if 0 <= server_id < self.NUM_SERVERS:
            old_state = self.server_states[server_id]
            self.server_states[server_id] = state
            
            if not state:
                # Server turned off - fan off, start cooling
                self.fan_states[server_id] = 0
                self.server_cpu_loads[server_id] = 0
            elif state and not old_state:
                # Server turned on - set defaults
                self.fan_states[server_id] = 2
                self.server_cpu_loads[server_id] = 50.0
                self.server_temperatures[server_id] = 35.0
                
            return old_state != state
        return False
    
    def set_fan_state(self, server_id: int, speed: int) -> bool:
        """Set a fan's speed level (0-3)."""
        if 0 <= server_id < self.NUM_SERVERS and 0 <= speed <= 3:
            if self.server_states[server_id] or speed == 0:
                old_speed = self.fan_states[server_id]
                self.fan_states[server_id] = speed
                return old_speed != speed
        return False
    
    def _generate_workload_pattern(self) -> float:
        """Generate realistic workload pattern."""
        # Update phase (creates cyclical patterns)
        self.workload_phase += 0.06
        if self.workload_phase > 2 * np.pi:
            self.workload_phase -= 2 * np.pi
        
        # Occasionally change trend direction
        self.trend_duration -= 1
        if self.trend_duration <= 0:
            self.workload_trend = np.random.uniform(-0.6, 0.6)
            self.trend_duration = np.random.randint(30, 80)
        
        # Base workload follows trend
        self.workload_base += self.workload_trend
        self.workload_base = np.clip(self.workload_base, 20, 90)
        
        # Add cyclical component
        cyclical = 15 * np.sin(self.workload_phase)
        
        # Add small noise
        noise = np.random.normal(0, 1.0)
        
        return np.clip(self.workload_base + cyclical + noise, 10, 100)
    
    def _update_workload(self):
        """Update global workload."""
        target_workload = self._generate_workload_pattern()
        self.workload = 0.9 * self.workload + 0.1 * target_workload
        self.workload = np.clip(self.workload, 10, 100)
    
    def _distribute_workload(self):
        """Distribute workload across active servers."""
        active_servers = self.get_active_servers()
        
        if active_servers == 0:
            return
        
        # Base load per server
        base_load = self.workload / active_servers
        
        # Distribute with slight variation
        for i in range(self.NUM_SERVERS):
            if self.server_states[i]:
                # Each server gets base load ± small variation
                variation = np.random.normal(0, 3)
                target_load = base_load * 10 + variation  # Scale to percentage
                
                # Smooth transition
                self.server_cpu_loads[i] = (
                    0.8 * self.server_cpu_loads[i] + 0.2 * target_load
                )
                self.server_cpu_loads[i] = np.clip(self.server_cpu_loads[i], 5, 100)
            else:
                self.server_cpu_loads[i] = 0
    
    def _update_server_temperature(self, server_id: int):
        """
        Update temperature for a single server.
        THIS IS THE KEY FUNCTION - temperature responds to fan speed.
        """
        if not self.server_states[server_id]:
            # Server is OFF - cool down to ambient
            cooling_rate = 0.15
            self.server_temperatures[server_id] = (
                self.server_temperatures[server_id] + 
                (self.AMBIENT_TEMP - self.server_temperatures[server_id]) * cooling_rate
            )
            return
        
        current_temp = self.server_temperatures[server_id]
        cpu_load = self.server_cpu_loads[server_id]
        fan_speed = self.fan_states[server_id]
        
        # === HEAT GENERATION ===
        # Heat generated based on CPU load
        heat_generated = (cpu_load / 100.0) * self.HEAT_GENERATION_RATE
        
        # Additional heat at high loads
        if cpu_load > 70:
            heat_generated += (cpu_load - 70) / 100.0 * 0.2
        
        # === COOLING EFFECTS ===
        # 1. Fan cooling - THIS IS CRITICAL
        fan_cooling = fan_speed * self.COOLING_PER_FAN_LEVEL
        
        # Fan effectiveness increases with temperature difference
        temp_diff = current_temp - self.AMBIENT_TEMP
        if temp_diff > 0:
            fan_cooling *= (1 + temp_diff / 50.0)
        
        # 2. Natural cooling
        natural_cooling = temp_diff * self.NATURAL_COOLING_RATE
        
        # Total cooling
        total_cooling = fan_cooling + natural_cooling
        
        # === NET TEMPERATURE CHANGE ===
        net_change = heat_generated - total_cooling / 10.0
        
        # Apply thermal inertia (temperature changes slowly)
        new_temp = (
            self.THERMAL_INERTIA * current_temp + 
            (1 - self.THERMAL_INERTIA) * (current_temp + net_change)
        )
        
        # Add tiny noise for realism
        new_temp += np.random.normal(0, 0.1)
        
        # Clamp temperature
        self.server_temperatures[server_id] = np.clip(
            new_temp, self.AMBIENT_TEMP, self.MAX_TEMP
        )
    
    def _update_all_temperatures(self):
        """Update temperatures for all servers."""
        for i in range(self.NUM_SERVERS):
            self._update_server_temperature(i)
    
    def _update_energy(self):
        """Calculate total energy consumption."""
        total_energy = 0
        
        for i in range(self.NUM_SERVERS):
            if self.server_states[i]:
                # Base energy
                base = self.BASE_ENERGY_PER_SERVER
                
                # Load-dependent energy
                load_factor = self.server_cpu_loads[i] / 100.0
                load_energy = (self.MAX_ENERGY_PER_SERVER - base) * load_factor
                
                # Fan energy
                fan_energy = self.fan_states[i] * self.ENERGY_PER_FAN_LEVEL
                
                total_energy += base + load_energy + fan_energy
        
        # Smooth transition
        self.energy = 0.8 * self.energy + 0.2 * total_energy
        self.energy = max(10, self.energy)
    
    def calculate_current_efficiency(self) -> float:
        """
        Calculate CURRENT efficiency based on actual metrics.
        Considers utilization, energy, temperature, and fan optimization.
        """
        active_servers = self.get_active_servers()
        
        if active_servers == 0:
            return 20.0
        
        avg_cpu = self.get_cpu_usage()
        avg_temp = self.get_average_temperature()
        max_temp = self.get_max_temperature()
        
        # === UTILIZATION EFFICIENCY (0-100) ===
        # Optimal CPU: 40-70%
        if avg_cpu < 20:
            util_eff = 30 + avg_cpu * 1.5
        elif avg_cpu < 40:
            util_eff = 60 + (avg_cpu - 20) * 1.0
        elif avg_cpu <= 70:
            util_eff = 80 + (avg_cpu - 40) * 0.4
        elif avg_cpu <= 85:
            util_eff = 92 - (avg_cpu - 70) * 0.5
        else:
            util_eff = 85 - (avg_cpu - 85) * 1.5
        util_eff = np.clip(util_eff, 20, 95)
        
        # === ENERGY EFFICIENCY (0-100) ===
        if self.energy > 0 and active_servers > 0:
            work_output = self.workload * active_servers
            energy_per_work = self.energy / max(work_output, 1)
            energy_eff = max(20, 95 - energy_per_work * 10)
        else:
            energy_eff = 50
        energy_eff = np.clip(energy_eff, 20, 95)
        
        # === TEMPERATURE EFFICIENCY (0-100) ===
        # Based on max temperature (worst case)
        if max_temp < 30:
            temp_eff = 85
        elif max_temp <= 38:
            temp_eff = 95
        elif max_temp <= 45:
            temp_eff = 95 - (max_temp - 38) * 2
        elif max_temp <= 55:
            temp_eff = 81 - (max_temp - 45) * 2.5
        elif max_temp <= 65:
            temp_eff = 56 - (max_temp - 55) * 2
        else:
            temp_eff = 36 - (max_temp - 65) * 1.5
        temp_eff = np.clip(temp_eff, 10, 95)
        
        # === FAN EFFICIENCY ===
        # Penalize over-cooling or under-cooling
        fan_eff = 90
        for i in range(self.NUM_SERVERS):
            if self.server_states[i]:
                temp = self.server_temperatures[i]
                fan = self.fan_states[i]
                
                # Optimal fan for temperature
                if temp > 50:
                    optimal_fan = 3
                elif temp > 40:
                    optimal_fan = 2
                elif temp > 32:
                    optimal_fan = 1
                else:
                    optimal_fan = 0
                
                # Penalize deviation
                deviation = abs(fan - optimal_fan)
                fan_eff -= deviation * 2
        
        fan_eff = np.clip(fan_eff, 40, 95)
        
        # === COMBINED EFFICIENCY ===
        efficiency = (
            util_eff * 0.30 +
            energy_eff * 0.25 +
            temp_eff * 0.30 +
            fan_eff * 0.15
        )
        
        # Never exceed 92%
        efficiency = np.clip(efficiency, 20, 92)
        
        return round(efficiency, 2)
    
    def step(self) -> Dict:
        """Advance simulation by one step."""
        self.time_step += 1
        
        # Update in order
        self._update_workload()
        self._distribute_workload()
        self._update_all_temperatures()
        self._update_energy()
        
        return self.get_state()
    
    def get_state(self) -> Dict:
        """Get current state."""
        return {
            'servers': self.get_active_servers(),
            'workload': round(self.workload, 2),
            'cpu': round(self.get_cpu_usage(), 2),
            'energy': round(self.energy, 2),
            'temperature': round(self.get_average_temperature(), 2),
            'max_temperature': round(self.get_max_temperature(), 2),
            'current_efficiency': self.calculate_current_efficiency(),
            'server_states': self.server_states.copy(),
            'fan_states': self.fan_states.copy(),
            'server_temperatures': [round(t, 2) for t in self.server_temperatures],
            'server_cpu_loads': [round(c, 2) for c in self.server_cpu_loads],
            'active_fans': self.get_active_fans(),
            'time_step': self.time_step
        }
    
    def get_features_for_prediction(self) -> np.ndarray:
        """Get feature array for ML model."""
        return np.array([[
            self.get_active_servers(),
            self.workload,
            self.get_cpu_usage(),
            self.energy,
            self.get_average_temperature()
        ]])
    
    def clone(self) -> 'InfrastructureSimulator':
        """Create a deep copy for prediction testing."""
        clone = InfrastructureSimulator()
        clone.server_states = self.server_states.copy()
        clone.fan_states = self.fan_states.copy()
        clone.server_temperatures = self.server_temperatures.copy()
        clone.server_cpu_loads = self.server_cpu_loads.copy()
        clone.workload = self.workload
        clone.energy = self.energy
        clone.time_step = self.time_step
        clone.workload_base = self.workload_base
        clone.workload_trend = self.workload_trend
        clone.workload_phase = self.workload_phase
        clone.trend_duration = self.trend_duration
        return clone
    
    def copy_workload_pattern_from(self, other: 'InfrastructureSimulator'):
        """Copy workload pattern for fair competition."""
        self.workload_base = other.workload_base
        self.workload_trend = other.workload_trend
        self.workload_phase = other.workload_phase
        self.trend_duration = other.trend_duration
        self.workload = other.workload