"""
AI Optimizer Module - Updated Analysis
=======================================
Provides detailed per-server analysis.
"""

from typing import Dict, List
import numpy as np


class AIOptimizer:
    """AI-powered analyzer with per-server insights."""
    
    TEMP_COLD = 28
    TEMP_COOL = 32
    TEMP_OPTIMAL = 38
    TEMP_WARM = 45
    TEMP_HOT = 55
    TEMP_CRITICAL = 65
    
    EFFICIENCY_POOR = 45
    EFFICIENCY_AVERAGE = 60
    EFFICIENCY_GOOD = 75
    EFFICIENCY_EXCELLENT = 85
    
    def __init__(self):
        """Initialize optimizer."""
        pass
    
    def analyze_state(self, state: Dict, predicted_efficiency: float) -> Dict:
        """Comprehensive per-server analysis."""
        
        servers = state.get('servers', 10)
        workload = state.get('workload', 50)
        current_efficiency = state.get('current_efficiency', 50)
        server_states = state.get('server_states', [True] * 10)
        fan_states = state.get('fan_states', [2] * 10)
        temperatures = state.get('server_temperatures', [35.0] * 10)
        cpu_loads = state.get('server_cpu_loads', [50.0] * 10)
        max_temp = state.get('max_temperature', 35)
        avg_temp = state.get('temperature', 35)
        
        analysis = {
            'overall_status': 'normal',
            'efficiency_rating': '',
            'temperature_status': '',
            'workload_status': '',
            'server_analysis': [],
            'suggestions': [],
            'critical_servers': [],
            'warnings': []
        }
        
        # === EFFICIENCY RATING ===
        if current_efficiency >= self.EFFICIENCY_EXCELLENT:
            analysis['efficiency_rating'] = '🌟 EXCELLENT'
            analysis['overall_status'] = 'optimal'
        elif current_efficiency >= self.EFFICIENCY_GOOD:
            analysis['efficiency_rating'] = '✅ GOOD'
            analysis['overall_status'] = 'good'
        elif current_efficiency >= self.EFFICIENCY_AVERAGE:
            analysis['efficiency_rating'] = '📊 AVERAGE'
        elif current_efficiency >= self.EFFICIENCY_POOR:
            analysis['efficiency_rating'] = '⚠️ BELOW AVERAGE'
            analysis['overall_status'] = 'warning'
        else:
            analysis['efficiency_rating'] = '❌ POOR'
            analysis['overall_status'] = 'critical'
        
        # === TEMPERATURE STATUS ===
        if max_temp >= self.TEMP_CRITICAL:
            analysis['temperature_status'] = '🚨 CRITICAL - Immediate cooling required!'
            analysis['overall_status'] = 'critical'
        elif max_temp >= self.TEMP_HOT:
            analysis['temperature_status'] = '🔴 HOT - Increase cooling'
        elif max_temp >= self.TEMP_WARM:
            analysis['temperature_status'] = '🟠 WARM - Monitor closely'
        elif max_temp >= self.TEMP_OPTIMAL:
            analysis['temperature_status'] = '🟢 OPTIMAL'
        elif max_temp >= self.TEMP_COOL:
            analysis['temperature_status'] = '🔵 COOL'
        else:
            analysis['temperature_status'] = '❄️ COLD - Can reduce cooling'
        
        # === WORKLOAD STATUS ===
        if servers > 0:
            load_per_server = workload / servers
            if load_per_server > 80:
                analysis['workload_status'] = '🔴 OVERLOADED'
            elif load_per_server > 65:
                analysis['workload_status'] = '🟠 HIGH LOAD'
            elif load_per_server >= 40:
                analysis['workload_status'] = '🟢 OPTIMAL'
            elif load_per_server >= 25:
                analysis['workload_status'] = '🔵 LIGHT LOAD'
            else:
                analysis['workload_status'] = '⚪ VERY LIGHT'
        else:
            analysis['workload_status'] = '⚫ NO SERVERS'
        
        # === PER-SERVER ANALYSIS ===
        for i in range(10):
            if server_states[i]:
                temp = temperatures[i]
                cpu = cpu_loads[i]
                fan = fan_states[i]
                
                status = "🟢"
                issues = []
                
                if temp >= self.TEMP_CRITICAL:
                    status = "🔴"
                    issues.append("CRITICAL TEMP")
                    analysis['critical_servers'].append(i)
                elif temp >= self.TEMP_HOT:
                    status = "🟠"
                    issues.append("High temp")
                
                if cpu > 85:
                    issues.append("High CPU")
                
                # Check if fan matches temperature needs
                optimal_fan = 3 if temp > 50 else (2 if temp > 38 else (1 if temp > 30 else 0))
                if fan < optimal_fan and temp > 40:
                    issues.append("Fan too low")
                elif fan > optimal_fan + 1 and temp < 32:
                    issues.append("Fan too high")
                
                analysis['server_analysis'].append({
                    'id': i,
                    'status': status,
                    'temp': temp,
                    'cpu': cpu,
                    'fan': fan,
                    'issues': issues
                })
            else:
                analysis['server_analysis'].append({
                    'id': i,
                    'status': "⚫",
                    'temp': temperatures[i],
                    'cpu': 0,
                    'fan': 0,
                    'issues': ["Offline"]
                })
        
        # === GENERATE SUGGESTIONS ===
        hot_servers = [s for s in analysis['server_analysis'] 
                       if s['temp'] > self.TEMP_WARM and s['status'] != "⚫"]
        
        if hot_servers:
            analysis['suggestions'].append(
                f"🌡️ {len(hot_servers)} server(s) running hot - increase fan speeds"
            )
        
        if analysis['critical_servers']:
            analysis['warnings'].append(
                f"🚨 CRITICAL: Server(s) {[s+1 for s in analysis['critical_servers']]} need immediate cooling!"
            )
        
        if servers > 0:
            load_per_server = workload / servers
            if load_per_server < 25 and servers > 2:
                analysis['suggestions'].append(
                    f"💤 Low utilization ({load_per_server:.0f}%/server) - consider turning off servers"
                )
            elif load_per_server > 75:
                analysis['suggestions'].append(
                    f"📈 High load ({load_per_server:.0f}%/server) - consider adding servers"
                )
        
        cold_servers = [s for s in analysis['server_analysis'] 
                        if s['temp'] < self.TEMP_COOL and s['fan'] > 1 and s['status'] != "⚫"]
        if cold_servers:
            analysis['suggestions'].append(
                f"💚 {len(cold_servers)} server(s) are cool - can reduce fan speed to save energy"
            )
        
        if not analysis['suggestions'] and not analysis['warnings']:
            analysis['suggestions'].append("✅ System operating optimally")
        
        return analysis
    
    def format_analysis_html(self, analysis: Dict) -> str:
        """Format analysis as HTML."""
        
        status_colors = {
            'critical': '#fee2e2',
            'warning': '#fef3c7',
            'normal': '#f3f4f6',
            'good': '#d1fae5',
            'optimal': '#cffafe'
        }
        
        bg_color = status_colors.get(analysis['overall_status'], '#f3f4f6')
        
        html = f"""
        <div style="background: {bg_color}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
                {analysis['efficiency_rating']}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div>🌡️ {analysis['temperature_status']}</div>
                <div>📊 {analysis['workload_status']}</div>
            </div>
        </div>
        """
        
        # Warnings
        if analysis['warnings']:
            html += '<div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 0.75rem; border-radius: 4px; margin-bottom: 0.5rem;">'
            for warning in analysis['warnings']:
                html += f'<div style="color: #b91c1c;">{warning}</div>'
            html += '</div>'
        
        # Suggestions
        if analysis['suggestions']:
            html += '<div style="background: #f0fdf4; border-radius: 8px; padding: 0.75rem;">'
            html += '<div style="font-weight: 600; margin-bottom: 0.5rem;">💡 Suggestions:</div>'
            for suggestion in analysis['suggestions'][:4]:
                html += f'<div style="margin-left: 0.5rem; font-size: 0.9rem;">• {suggestion}</div>'
            html += '</div>'
        
        return html