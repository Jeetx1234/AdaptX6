"""
Dataset Generation - Updated for per-server temperatures
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path


def generate_dataset(num_samples: int = 5000, output_path: str = "dataset/dataset.csv"):
    print(f"🔄 Generating {num_samples} samples...")
    
    servers = 10
    workload = 50.0
    energy = 600.0
    avg_temp = 32.0
    avg_cpu = 50.0
    
    workload_base = 50.0
    workload_trend = 0.0
    workload_phase = 0.0
    trend_duration = 0
    
    data = {
        'servers': [],
        'workload': [],
        'cpu': [],
        'energy': [],
        'temperature': [],
        'efficiency': []
    }
    
    for i in range(num_samples):
        # Workload pattern
        workload_phase += 0.06
        if workload_phase > 2 * np.pi:
            workload_phase -= 2 * np.pi
        
        trend_duration -= 1
        if trend_duration <= 0:
            workload_trend = np.random.uniform(-0.6, 0.6)
            trend_duration = np.random.randint(30, 80)
        
        workload_base += workload_trend
        workload_base = np.clip(workload_base, 20, 90)
        
        cyclical = 15 * np.sin(workload_phase)
        target_workload = workload_base + cyclical + np.random.normal(0, 1)
        workload = 0.9 * workload + 0.1 * target_workload
        workload = np.clip(workload, 10, 100)
        
        # Adjust servers
        load_per_server = workload / servers
        if np.random.random() < 0.03:
            if load_per_server < 25 and servers > 2:
                servers = max(2, servers - 1)
            elif load_per_server > 70 and servers < 10:
                servers = min(10, servers + 1)
        
        # CPU
        target_cpu = (workload / servers) * 10 + np.random.normal(0, 2)
        avg_cpu = 0.8 * avg_cpu + 0.2 * target_cpu
        avg_cpu = np.clip(avg_cpu, 5, 100)
        
        # Energy
        base_energy = servers * 45
        load_energy = servers * 75 * (avg_cpu / 100.0)
        fan_energy = servers * 2 * 8  # Assume medium fans
        target_energy = base_energy + load_energy + fan_energy
        energy = 0.8 * energy + 0.2 * target_energy
        
        # Temperature
        heat = (avg_cpu / 100.0) * 0.4
        cooling = 2 * 0.8 + (avg_temp - 22) * 0.05
        net = heat - cooling / 10
        avg_temp = 0.85 * avg_temp + 0.15 * (avg_temp + net)
        avg_temp = np.clip(avg_temp + np.random.normal(0, 0.1), 22, 75)
        
        # Efficiency
        if avg_cpu < 20:
            util_eff = 30 + avg_cpu * 1.5
        elif avg_cpu < 40:
            util_eff = 60 + (avg_cpu - 20)
        elif avg_cpu <= 70:
            util_eff = 80 + (avg_cpu - 40) * 0.4
        else:
            util_eff = 92 - (avg_cpu - 70) * 0.5
        util_eff = np.clip(util_eff, 20, 95)
        
        if energy > 0:
            energy_eff = max(20, 95 - energy / (workload * servers + 1) * 10)
        else:
            energy_eff = 50
        
        if avg_temp <= 38:
            temp_eff = 95
        elif avg_temp <= 50:
            temp_eff = 95 - (avg_temp - 38) * 2
        else:
            temp_eff = 71 - (avg_temp - 50) * 2
        temp_eff = np.clip(temp_eff, 10, 95)
        
        efficiency = util_eff * 0.35 + energy_eff * 0.25 + temp_eff * 0.30 + 85 * 0.10
        efficiency = np.clip(efficiency, 20, 92)
        
        data['servers'].append(servers)
        data['workload'].append(round(workload, 2))
        data['cpu'].append(round(avg_cpu, 2))
        data['energy'].append(round(energy, 2))
        data['temperature'].append(round(avg_temp, 2))
        data['efficiency'].append(round(efficiency, 2))
        
        if (i + 1) % 1000 == 0:
            print(f"  {i + 1}/{num_samples}")
    
    df = pd.DataFrame(data)
    
    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Saved to {output_path}")
    print(f"\nStats:\n{df.describe().round(2)}")
    
    return df


if __name__ == "__main__":
    generate_dataset()