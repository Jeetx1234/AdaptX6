"""
Resource Optimization and Efficiency Prediction Dashboard
==========================================================
- Per-server temperature monitoring
- Full AI control (no threshold restrictions)
- 10 temperature lines in single graph
- Includes phone server metrics
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
    /* ... your previous CSS unchanged ... */
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
        
        # History with per-server temperatures (10 servers only)
        st.session_state.ai_history = {
            'time': [],
            'workload': [],
            'energy': [],
            'efficiency': [],
            'server_temps': [[] for _ in range(10)]
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
# PHONE SERVER PANEL
# ============================================================

def render_phone_servers(manager):
    """Show phone server metrics (temperature & battery)."""
    if not hasattr(manager, 'phone_servers'):
        return
    
    st.markdown("### 📱 Phone Servers Metrics")
    for idx, phone in enumerate(manager.phone_servers):
        st.subheader(f"Phone Server {idx + 1}")
        st.metric("Temperature", f"{phone.get_temperature():.1f} °C")
        st.metric("Battery", f"{phone.get_battery():.0f} %")
        st.text(f"Status: {phone.state}")


# ============================================================
# OTHER UI COMPONENTS (unchanged)
# ============================================================

# render_efficiency_cards, render_metrics, render_server_panel,
# render_temperature_chart, render_efficiency_chart, render_scoreboard
# ... leave all previous functions as-is ...


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application."""
    
    init_session_state()
    model, scaler = load_model()
    
    # Title
    st.markdown('<div class="main-title">🖥️ Resource Optimization & Efficiency Prediction</div>', unsafe_allow_html=True)
    
    # Phone servers (top panel)
    render_phone_servers(st.session_state.ai_mgr)
    
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
        new_threshold = st.slider("Threshold (°C)", 30.0, 70.0, current_threshold, 1.0)
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
            st.experimental_rerun()
        
        st.markdown("---")
        st.markdown(f"**Rounds:** {st.session_state.rounds}")
    
    # Scoreboard
    render_scoreboard()
    st.markdown("---")
    
    # Main columns
    ai_col, human_col = st.columns(2)
    
    # ==================== AI SECTION ====================
    with ai_col:
        # ... everything AI section unchanged ...
        pass
    
    # ==================== HUMAN SECTION ====================
    with human_col:
        # ... everything Human section unchanged ...
        pass
    
    # Increment rounds
    st.session_state.rounds += 1
    
    # Temperature alarm
    ai_max = max(st.session_state.ai_sim.get_state()['max_temperature'], 0)
    human_max = max(st.session_state.human_sim.get_state()['max_temperature'], 0)
    max_temp = max(ai_max, human_max)
    alarm_result = st.session_state.alarm.check_temperature(max_temp)
    
    if alarm_result['exceeded']:
        if alarm_result['alarm_triggered']:
            st.error(f"🚨 {alarm_result['message']}")
        else:
            st.warning(f"⚠️ {alarm_result['message']}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.experimental_rerun()


if __name__ == "__main__":
    main()
