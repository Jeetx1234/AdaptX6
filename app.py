"""
Resource Optimization and Efficiency Prediction Dashboard
==========================================================
- Per-server temperature monitoring
- Full AI control (no threshold restrictions)
- 10 temperature lines in single graph
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
import os
import time
from datetime import datetime

from utils.simulation import InfrastructureSimulator
from utils.optimizer import AIOptimizer
from utils.server_manager import ServerManager
from utils.alarm import AlarmSystem

# Page config
st.set_page_config(
    page_title="Resource Optimization & Efficiency Prediction",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    
    .section-box {
        background: #f8fafc;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    .ai-box {
        background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
        border: 2px solid #818cf8;
    }
    
    .human-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 2px solid #34d399;
    }
    
    .efficiency-card {
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    
    .eff-current {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .eff-predicted {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
    }
    
    .eff-value { font-size: 2.5rem; font-weight: 800; }
    .eff-label { font-size: 0.85rem; opacity: 0.9; }
    
    .server-item {
        background: white;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 4px;
    }
    
    .server-on { border-left: 4px solid #10b981; }
    .server-off { border-left: 4px solid #ef4444; }
    .server-hot { border-left: 4px solid #f59e0b; }
    .server-critical { border-left: 4px solid #dc2626; background: #fef2f2; }
    
    .score-card {
        text-align: center;
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        font-size: 2rem;
        font-weight: 800;
    }
    
    .ai-score { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .human-score { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    
    .action-log {
        background: #1e293b;
        color: #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.8rem;
        max-height: 150px;
        overflow-y: auto;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# INITIALIZATION
# ============================================================

@st.cache_resource
def load_model():
    """Load ML model."""
    model_path = "models/efficiency_model.pkl"
    scaler_path = "models/scaler.pkl"
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        return joblib.load(model_path), joblib.load(scaler_path)
    return None, None


def init_session_state():
    """Initialize session state."""
    
    if 'initialized' not in st.session_state:
        st.session_state.ai_sim = InfrastructureSimulator()
        st.session_state.ai_mgr = ServerManager()
        
        st.session_state.human_sim = InfrastructureSimulator()
        st.session_state.human_mgr = ServerManager()
        
        st.session_state.optimizer = AIOptimizer()
        st.session_state.alarm = AlarmSystem(default_threshold=50.0)
        
        # History with per-server temperatures
        st.session_state.ai_history = {
            'time': [],
            'workload': [],
            'energy': [],
            'efficiency': [],
            'server_temps': [[] for _ in range(10)]  # 10 temperature arrays
        }
        st.session_state.human_history = {
            'time': [],
            'workload': [],
            'energy': [],
            'efficiency': [],
            'server_temps': [[] for _ in range(10)]
        }
        
        st.session_state.ai_score_sum = 0
        st.session_state.human_score_sum = 0
        st.session_state.rounds = 0
        st.session_state.ai_log = []
        
        st.session_state.initialized = True


def predict_efficiency(simulator, model, scaler) -> float:
    """Get ML prediction."""
    if model is None:
        return simulator.calculate_current_efficiency()
    
    features = simulator.get_features_for_prediction()
    scaled = scaler.transform(features)
    pred = model.predict(scaled)[0]
    return np.clip(pred, 20, 92)


def update_history(history, state, max_len=100):
    """Update history with per-server temps."""
    history['time'].append(time.time())
    history['workload'].append(state['workload'])
    history['energy'].append(state['energy'])
    history['efficiency'].append(state['current_efficiency'])
    
    # Per-server temperatures
    for i in range(10):
        history['server_temps'][i].append(state['server_temperatures'][i])
    
    # Trim all arrays
    for k in ['time', 'workload', 'energy', 'efficiency']:
        if len(history[k]) > max_len:
            history[k].pop(0)
    
    for i in range(10):
        if len(history['server_temps'][i]) > max_len:
            history['server_temps'][i].pop(0)


# ============================================================
# UI COMPONENTS
# ============================================================

def render_efficiency_cards(current: float, predicted: float):
    """Render efficiency cards."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="efficiency-card eff-current">
            <div class="eff-label">📊 CURRENT EFFICIENCY</div>
            <div class="eff-value">{current:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="efficiency-card eff-predicted">
            <div class="eff-label">🔮 PREDICTED EFFICIENCY</div>
            <div class="eff-value">{predicted:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_metrics(state):
    """Render metrics row."""
    cols = st.columns(6)
    
    metrics = [
        ("🖥️ Servers", f"{state['servers']}/10"),
        ("📊 Workload", f"{state['workload']:.1f}%"),
        ("💻 Avg CPU", f"{state['cpu']:.1f}%"),
        ("⚡ Energy", f"{state['energy']:.0f}W"),
        ("🌡️ Avg Temp", f"{state['temperature']:.1f}°C"),
        ("🔥 Max Temp", f"{state['max_temperature']:.1f}°C")
    ]
    
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def render_server_panel(simulator, manager, prefix, editable=True):
    """Render server panel with temps and fan controls."""
    
    state = simulator.get_state()
    server_states = state['server_states']
    fan_states = state['fan_states']
    temperatures = state['server_temperatures']
    cpu_loads = state['server_cpu_loads']
    
    fan_names = {0: "OFF", 1: "LOW", 2: "MED", 3: "HIGH"}
    
    for row in range(2):
        cols = st.columns(5)
        for col_idx, col in enumerate(cols):
            idx = row * 5 + col_idx
            is_on = server_states[idx]
            fan = fan_states[idx]
            temp = temperatures[idx]
            cpu = cpu_loads[idx]
            
            with col:
                # Determine status class
                if not is_on:
                    status_class = "server-off"
                    status_icon = "⚫"
                elif temp >= 60:
                    status_class = "server-critical"
                    status_icon = "🔴"
                elif temp >= 45:
                    status_class = "server-hot"
                    status_icon = "🟠"
                else:
                    status_class = "server-on"
                    status_icon = "🟢"
                
                st.markdown(f"""
                <div class="server-item {status_class}">
                    {status_icon} <b>S{idx+1}</b><br>
                    <small>🌡️{temp:.1f}°C | 💻{cpu:.0f}%</small><br>
                    <small>Fan: {fan_names[fan]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if editable:
                    # Power toggle
                    new_state = st.checkbox(
                        f"S{idx+1}", value=is_on,
                        key=f"{prefix}_pwr_{idx}",
                        label_visibility="collapsed"
                    )
                    if new_state != is_on:
                        success, _ = manager.set_server_online(idx, new_state, "Human")
                        if success:
                            simulator.set_server_state(idx, new_state)
                    
                    # Fan control
                    if is_on:
                        new_fan = st.select_slider(
                            "Fan", [0,1,2,3], value=fan,
                            format_func=lambda x: fan_names[x],
                            key=f"{prefix}_fan_{idx}",
                            label_visibility="collapsed"
                        )
                        if new_fan != fan:
                            manager.set_fan_speed(idx, new_fan, "Human")
                            simulator.set_fan_state(idx, new_fan)


def render_temperature_chart(history, prefix, threshold):
    """Render chart with all 10 server temperatures."""
    
    if len(history['time']) < 3:
        st.info("📈 Collecting temperature data...")
        return
    
    t0 = history['time'][0]
    times = [t - t0 for t in history['time']]
    
    # Color palette for 10 servers
    colors = [
        '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
        '#06b6d4', '#3b82f6', '#8b5cf6', '#d946ef', '#ec4899'
    ]
    
    fig = go.Figure()
    
    # Add trace for each server
    for i in range(10):
        fig.add_trace(go.Scatter(
            x=times,
            y=history['server_temps'][i],
            mode='lines',
            name=f'S{i+1}',
            line=dict(color=colors[i], width=2),
            hovertemplate=f'Server {i+1}: %{{y:.1f}}°C<extra></extra>'
        ))
    
    # Add threshold line
    fig.add_hline(
        y=threshold, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Alarm: {threshold}°C"
    )
    
    fig.update_layout(
        title="🌡️ Per-Server Temperature",
        xaxis_title="Time (s)",
        yaxis_title="Temperature (°C)",
        height=350,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    
    st.plotly_chart(fig, key=f"{prefix}_temp_chart", use_container_width=True)


def render_efficiency_chart(history, prefix):
    """Render workload, energy, efficiency chart."""
    
    if len(history['time']) < 3:
        return
    
    t0 = history['time'][0]
    times = [t - t0 for t in history['time']]
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=['Workload', 'Energy', 'Efficiency']
    )
    
    fig.add_trace(go.Scatter(
        x=times, y=history['workload'],
        mode='lines', name='Workload',
        line=dict(color='#6366f1', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=times, y=history['energy'],
        mode='lines', name='Energy',
        line=dict(color='#f59e0b', width=2)
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        x=times, y=history['efficiency'],
        mode='lines', name='Efficiency',
        line=dict(color='#10b981', width=2),
        fill='tozeroy', fillcolor='rgba(16,185,129,0.1)'
    ), row=1, col=3)
    
    fig.update_layout(
        height=250,
        showlegend=False,
        margin=dict(l=40, r=20, t=40, b=30)
    )
    
    st.plotly_chart(fig, key=f"{prefix}_eff_chart", use_container_width=True)


def render_scoreboard():
    """Render competition scoreboard."""
    rounds = max(1, st.session_state.rounds)
    ai_avg = st.session_state.ai_score_sum / rounds
    human_avg = st.session_state.human_score_sum / rounds
    
    st.markdown("### 🏆 Competition Scoreboard")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="score-card ai-score">
            🤖 AI<br>{ai_avg:.1f}%
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        diff = ai_avg - human_avg
        if diff > 0.5:
            result = "🤖 AI Wins!"
            color = "#667eea"
        elif diff < -0.5:
            result = "👤 Human Wins!"
            color = "#10b981"
        else:
            result = "🤝 Tie"
            color = "#6b7280"
        
        st.markdown(f"""
        <div style="text-align:center; padding: 1rem;">
            <div style="font-size: 0.9rem; color: #6b7280;">Round {rounds}</div>
            <div style="font-size: 1.2rem; color: {color}; font-weight: 700; margin-top: 0.5rem;">
                {result}
            </div>
            <div style="font-size: 0.85rem; color: #9ca3af; margin-top: 0.5rem;">
                Gap: {abs(diff):.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="score-card human-score">
            👤 Human<br>{human_avg:.1f}%
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application."""
    
    init_session_state()
    model, scaler = load_model()
    
    # Title
    st.markdown('<div class="main-title">🖥️ Resource Optimization & Efficiency Prediction</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        if model:
            st.success("✅ ML Model Loaded")
        else:
            st.warning("⚠️ No model found")
        
        st.markdown("---")
        
        # Temperature threshold
        st.markdown("### 🌡️ Temperature Alarm")
        current_threshold = st.session_state.alarm.get_threshold()
        new_threshold = st.slider(
            "Threshold (°C)", 30.0, 70.0, current_threshold, 1.0
        )
        if new_threshold != current_threshold:
            st.session_state.alarm.set_threshold(new_threshold)
            st.success(f"Threshold: {new_threshold}°C")
        
        st.markdown("---")
        
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
        refresh_rate = st.slider("Refresh Rate (s)", 1, 5, 2)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Simulation", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"**Rounds:** {st.session_state.rounds}")
    
    # Scoreboard
    render_scoreboard()
    st.markdown("---")
    
    # Main columns
    ai_col, human_col = st.columns(2)
    
    # ==================== AI SECTION ====================
    with ai_col:
        st.markdown("""
        <div class="section-box ai-box">
            <h3>🤖 AI Full Control Mode</h3>
            <p style="color: #6b7280; font-size: 0.9rem;">
                AI aggressively optimizes for maximum efficiency
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Step simulation
        ai_state = st.session_state.ai_sim.step()
        ai_predicted = predict_efficiency(st.session_state.ai_sim, model, scaler)
        ai_current = ai_state['current_efficiency']
        
        # AI FULL CONTROL - no restrictions
        decision = st.session_state.ai_mgr.ai_full_control(
            st.session_state.ai_sim,
            ai_current
        )
        
        # Apply AI actions
        if decision['should_act']:
            actions = st.session_state.ai_mgr.apply_ai_actions(
                decision, st.session_state.ai_sim
            )
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            for action in actions:
                st.session_state.ai_log.append(f"[{timestamp}] {action}")
            
            st.session_state.ai_log = st.session_state.ai_log[-15:]
        
        # Sync
        st.session_state.ai_mgr.sync_with_simulator(st.session_state.ai_sim)
        
        # Update history
        update_history(st.session_state.ai_history, ai_state)
        
        # Update score
        st.session_state.ai_score_sum += ai_current
        
        # Display
        render_efficiency_cards(ai_current, ai_predicted)
        render_metrics(ai_state)
        
        # Server panel (read-only)
        st.markdown("##### 🖥️ Server Status (AI Controlled)")
        render_server_panel(
            st.session_state.ai_sim,
            st.session_state.ai_mgr,
            "ai_view",
            editable=False
        )
        
        # AI reasoning
        st.markdown("##### 🧠 AI Decision Log")
        with st.expander("View AI Reasoning", expanded=True):
            for reason in decision['reasoning'][-5:]:
                st.markdown(f"• {reason}")
        
        # Action log
        if st.session_state.ai_log:
            st.markdown("##### 🎯 Recent Actions")
            log_html = "<div class='action-log'>" + "<br>".join(st.session_state.ai_log[-8:]) + "</div>"
            st.markdown(log_html, unsafe_allow_html=True)
        
        # Analysis
        st.markdown("##### 💡 AI Analysis")
        analysis = st.session_state.optimizer.analyze_state(ai_state, ai_predicted)
        st.markdown(
            st.session_state.optimizer.format_analysis_html(analysis),
            unsafe_allow_html=True
        )
        
        # Temperature chart with all 10 servers
        st.markdown("##### 🌡️ Per-Server Temperature")
        render_temperature_chart(
            st.session_state.ai_history, 
            "ai",
            st.session_state.alarm.get_threshold()
        )
        
        # Efficiency charts
        st.markdown("##### 📈 Performance Metrics")
        render_efficiency_chart(st.session_state.ai_history, "ai")
    
    # ==================== HUMAN SECTION ====================
    with human_col:
        st.markdown("""
        <div class="section-box human-box">
            <h3>👤 Human Control Mode</h3>
            <p style="color: #6b7280; font-size: 0.9rem;">
                You control servers and fans manually
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sync workload pattern
        st.session_state.human_sim.copy_workload_pattern_from(st.session_state.ai_sim)
        
        # Step simulation
        human_state = st.session_state.human_sim.step()
        human_predicted = predict_efficiency(st.session_state.human_sim, model, scaler)
        human_current = human_state['current_efficiency']
        
        # Sync
        st.session_state.human_mgr.sync_with_simulator(st.session_state.human_sim)
        
        # Update history
        update_history(st.session_state.human_history, human_state)
        
        # Update score
        st.session_state.human_score_sum += human_current
        
        # Display
        render_efficiency_cards(human_current, human_predicted)
        render_metrics(human_state)
        
        # Server controls
        st.markdown("##### 🖥️ Server & Fan Controls")
        render_server_panel(
            st.session_state.human_sim,
            st.session_state.human_mgr,
            "human",
            editable=True
        )
        
        # Tips
        st.markdown("##### 💡 Optimization Tips")
        st.info("""
        **Tips to maximize efficiency:**
        - 🌡️ Watch per-server temperatures
        - 🌀 Increase fans when temp > 45°C
        - 💨 Reduce fans when temp < 32°C (save energy)
        - 🖥️ Turn OFF servers when load < 25% per server
        - 📊 Target 50-60% CPU per server
        """)
        
        # Analysis
        st.markdown("##### 📊 Your Analysis")
        human_analysis = st.session_state.optimizer.analyze_state(human_state, human_predicted)
        st.markdown(
            st.session_state.optimizer.format_analysis_html(human_analysis),
            unsafe_allow_html=True
        )
        
        # Temperature chart
        st.markdown("##### 🌡️ Per-Server Temperature")
        render_temperature_chart(
            st.session_state.human_history,
            "human",
            st.session_state.alarm.get_threshold()
        )
        
        # Efficiency charts
        st.markdown("##### 📈 Performance Metrics")
        render_efficiency_chart(st.session_state.human_history, "human")
    
    # Increment rounds
    st.session_state.rounds += 1
    
    # Temperature alarm
    max_temp = max(ai_state['max_temperature'], human_state['max_temperature'])
    alarm_result = st.session_state.alarm.check_temperature(max_temp)
    
    if alarm_result['exceeded']:
        if alarm_result['alarm_triggered']:
            st.error(f"🚨 {alarm_result['message']}")
        else:
            st.warning(f"⚠️ {alarm_result['message']}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(0.1)
        st.rerun()


if __name__ == "__main__":
    main()