import streamlit as st
import time
from datetime import datetime, timedelta
import base64

# Configure page
st.set_page_config(
    page_title="Enhanced Exam Timer",
    page_icon="⏰",
    layout="wide"
)

# Initialize session state
if 'num_timers' not in st.session_state:
    st.session_state.num_timers = 4
if 'timer_configs' not in st.session_state:
    # Default configurations
    st.session_state.timer_configs = [
        {"name": "Standard Time", "minutes": 75, "frequency": 440},
        {"name": "5 min/hr ext", "minutes": 81.25, "frequency": 523},
        {"name": "10 min/hr ext", "minutes": 87.5, "frequency": 659},
        {"name": "15 min/hr ext", "minutes": 93.75, "frequency": 783},
        {"name": "Custom Timer 5", "minutes": 60, "frequency": 880},
        {"name": "Custom Timer 6", "minutes": 90, "frequency": 1047}
    ]
if 'timer_states' not in st.session_state:
    st.session_state.timer_states = {}
if 'finished_timers' not in st.session_state:
    st.session_state.finished_timers = set()

# Available frequencies for different timers
AVAILABLE_FREQUENCIES = [440, 523, 659, 783, 880, 1047, 1175, 1319]  # A4, C5, E5, G5, A5, C6, D6, E6
FREQUENCY_NAMES = ["A4", "C5", "E5", "G5", "A5", "C6", "D6", "E6"]

def generate_beep_sound(frequency=440, duration=0.5, sample_rate=44100):
    """Generate a simple beep sound as base64 encoded audio"""
    try:
        import numpy as np
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out to avoid clicks
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # Convert to 16-bit PCM
        audio = (wave * 32767).astype(np.int16)
        
        # Create WAV file in memory
        import io
        import struct
        
        buffer = io.BytesIO()
        
        # WAV header
        buffer.write(b'RIFF')
        buffer.write(struct.pack('<I', 36 + len(audio) * 2))
        buffer.write(b'WAVE')
        buffer.write(b'fmt ')
        buffer.write(struct.pack('<I', 16))
        buffer.write(struct.pack('<H', 1))  # PCM
        buffer.write(struct.pack('<H', 1))  # mono
        buffer.write(struct.pack('<I', sample_rate))
        buffer.write(struct.pack('<I', sample_rate * 2))
        buffer.write(struct.pack('<H', 2))
        buffer.write(struct.pack('<H', 16))
        buffer.write(b'data')
        buffer.write(struct.pack('<I', len(audio) * 2))
        buffer.write(audio.tobytes())
        
        # Encode to base64
        audio_b64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:audio/wav;base64,{audio_b64}"
    except ImportError:
        st.error("NumPy is required for audio generation. Install with: pip install numpy")
        return None

def format_time(seconds):
    """Format seconds into MM:SS format"""
    if seconds <= 0:
        return "00:00"
    
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def get_time_remaining(timer_id):
    """Calculate remaining time for a specific timer"""
    if timer_id not in st.session_state.timer_states:
        return None
    
    timer_state = st.session_state.timer_states[timer_id]
    if timer_state['start_time'] is None or not timer_state['is_running']:
        return timer_state['duration'] * 60
    
    elapsed = (datetime.now() - timer_state['start_time']).total_seconds()
    remaining = (timer_state['duration'] * 60) - elapsed
    return max(0, remaining)

def play_notification_sound(frequency):
    """Play a notification sound using HTML audio"""
    try:
        audio_data = generate_beep_sound(frequency, 1.0)  # 1 second beep
        if audio_data:
            audio_html = f"""
            <audio autoplay>
                <source src="{audio_data}" type="audio/wav">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback: show a visual notification if audio fails
        st.warning(f"🔔 Timer finished! (Audio unavailable: {str(e)})")

def initialize_timer_state(timer_id, duration):
    """Initialize state for a timer if it doesn't exist"""
    if timer_id not in st.session_state.timer_states:
        st.session_state.timer_states[timer_id] = {
            'start_time': None,
            'is_running': False,
            'duration': duration
        }

def start_timer(timer_id):
    """Start a specific timer"""
    if timer_id in st.session_state.timer_states:
        st.session_state.timer_states[timer_id]['start_time'] = datetime.now()
        st.session_state.timer_states[timer_id]['is_running'] = True

def stop_timer(timer_id):
    """Stop a specific timer"""
    if timer_id in st.session_state.timer_states:
        st.session_state.timer_states[timer_id]['is_running'] = False

def reset_timer(timer_id):
    """Reset a specific timer"""
    if timer_id in st.session_state.timer_states:
        st.session_state.timer_states[timer_id]['start_time'] = None
        st.session_state.timer_states[timer_id]['is_running'] = False
        if timer_id in st.session_state.finished_timers:
            st.session_state.finished_timers.remove(timer_id)

# Title and description
st.title("⏰ Enhanced Exam Timer")
st.markdown("**Customizable timer system with individual controls**")
st.markdown("---")

# Configuration section
st.subheader("🛠️ Timer Configuration")

# Number of timers selector
new_num_timers = st.slider("Number of Timers", min_value=1, max_value=6, value=st.session_state.num_timers)

if new_num_timers != st.session_state.num_timers:
    st.session_state.num_timers = new_num_timers
    st.rerun()

# Timer configuration
config_cols = st.columns(min(3, st.session_state.num_timers))
for i in range(st.session_state.num_timers):
    col_idx = i % len(config_cols)
    with config_cols[col_idx]:
        st.markdown(f"**Timer {i+1}**")
        
        # Timer name
        new_name = st.text_input(
            f"Name", 
            value=st.session_state.timer_configs[i]["name"], 
            key=f"name_{i}"
        )
        if new_name != st.session_state.timer_configs[i]["name"]:
            st.session_state.timer_configs[i]["name"] = new_name
        
        # Timer duration
        new_minutes = st.number_input(
            f"Minutes", 
            min_value=0.25, 
            max_value=300.0, 
            value=float(st.session_state.timer_configs[i]["minutes"]), 
            step=0.25,
            key=f"minutes_{i}"
        )
        if new_minutes != st.session_state.timer_configs[i]["minutes"]:
            st.session_state.timer_configs[i]["minutes"] = new_minutes
            # Update timer state if not running
            timer_id = f"timer_{i}"
            if timer_id in st.session_state.timer_states and not st.session_state.timer_states[timer_id]['is_running']:
                st.session_state.timer_states[timer_id]['duration'] = new_minutes
        
        # Sound frequency
        freq_idx = AVAILABLE_FREQUENCIES.index(st.session_state.timer_configs[i]["frequency"]) if st.session_state.timer_configs[i]["frequency"] in AVAILABLE_FREQUENCIES else 0
        new_freq_idx = st.selectbox(
            f"Sound", 
            range(len(AVAILABLE_FREQUENCIES)),
            index=freq_idx,
            format_func=lambda x: f"{FREQUENCY_NAMES[x]} ({AVAILABLE_FREQUENCIES[x]}Hz)",
            key=f"freq_{i}"
        )
        if AVAILABLE_FREQUENCIES[new_freq_idx] != st.session_state.timer_configs[i]["frequency"]:
            st.session_state.timer_configs[i]["frequency"] = AVAILABLE_FREQUENCIES[new_freq_idx]

# Global controls
st.subheader("🎮 Global Controls")
global_cols = st.columns(4)

with global_cols[0]:
    if st.button("🚀 Start All Timers"):
        for i in range(st.session_state.num_timers):
            timer_id = f"timer_{i}"
            initialize_timer_state(timer_id, st.session_state.timer_configs[i]["minutes"])
            start_timer(timer_id)
        st.rerun()

with global_cols[1]:
    if st.button("⏹️ Stop All Timers"):
        for i in range(st.session_state.num_timers):
            timer_id = f"timer_{i}"
            stop_timer(timer_id)
        st.rerun()

with global_cols[2]:
    if st.button("🔄 Reset All Timers"):
        for i in range(st.session_state.num_timers):
            timer_id = f"timer_{i}"
            reset_timer(timer_id)
        st.rerun()

with global_cols[3]:
    # Status indicator
    running_count = sum(1 for i in range(st.session_state.num_timers) 
                       if f"timer_{i}" in st.session_state.timer_states 
                       and st.session_state.timer_states[f"timer_{i}"]["is_running"])
    
    if running_count > 0:
        st.success(f"✅ {running_count} timer(s) running")
    else:
        st.info("⏹️ All timers stopped")

st.markdown("---")

# Display timers
st.subheader("⏱️ Timer Display")

# Calculate columns for timer display
cols_per_row = 3 if st.session_state.num_timers > 4 else 2
rows_needed = (st.session_state.num_timers + cols_per_row - 1) // cols_per_row

newly_finished = []

for row in range(rows_needed):
    timer_cols = st.columns(cols_per_row)
    
    for col in range(cols_per_row):
        timer_idx = row * cols_per_row + col
        if timer_idx >= st.session_state.num_timers:
            break
            
        with timer_cols[col]:
            timer_id = f"timer_{timer_idx}"
            config = st.session_state.timer_configs[timer_idx]
            
            # Initialize timer state if needed
            initialize_timer_state(timer_id, config["minutes"])
            
            # Calculate remaining time
            remaining_seconds = get_time_remaining(timer_id)
            
            # Check if timer just finished
            just_finished = (remaining_seconds is not None and 
                           remaining_seconds <= 0 and 
                           st.session_state.timer_states[timer_id]["is_running"] and 
                           timer_id not in st.session_state.finished_timers)
            
            if just_finished:
                newly_finished.append((timer_id, config["frequency"], config["name"]))
                st.session_state.finished_timers.add(timer_id)
                st.session_state.timer_states[timer_id]["is_running"] = False
            
            # Determine status and color
            is_running = st.session_state.timer_states[timer_id]["is_running"]
            if remaining_seconds <= 0 and timer_id in st.session_state.finished_timers:
                status = "🔔 FINISHED!"
                color = "red"
            elif is_running:
                status = "🏃 Running"
                color = "green"
            else:
                status = "⏸️ Ready"
                color = "blue"
            
            # Timer container
            with st.container():
                st.markdown(f"### {config['name']}")
                
                # Show exact duration
                total_seconds = int(config["minutes"] * 60)
                mins = total_seconds // 60
                secs = total_seconds % 60
                st.markdown(f"**Duration:** {mins} min {secs} sec")
                
                # Large time display
                time_display = format_time(remaining_seconds) if remaining_seconds is not None else "00:00"
                st.markdown(f"<h1 style='text-align: center; color: {color}; font-family: monospace;'>{time_display}</h1>", 
                           unsafe_allow_html=True)
                
                st.markdown(f"<p style='text-align: center; color: {color}; font-weight: bold;'>{status}</p>", 
                           unsafe_allow_html=True)
                
                # Progress bar
                if remaining_seconds is not None:
                    if is_running or timer_id in st.session_state.finished_timers:
                        progress = max(0, 1 - (remaining_seconds / (config["minutes"] * 60)))
                        st.progress(progress)
                    else:
                        st.progress(0)
                
                # Individual controls
                control_cols = st.columns(4)
                
                with control_cols[0]:
                    if st.button("▶️", key=f"start_{timer_id}", help="Start", disabled=is_running):
                        start_timer(timer_id)
                        st.rerun()
                
                with control_cols[1]:
                    if st.button("⏹️", key=f"stop_{timer_id}", help="Stop", disabled=not is_running):
                        stop_timer(timer_id)
                        st.rerun()
                
                with control_cols[2]:
                    if st.button("🔄", key=f"reset_{timer_id}", help="Reset"):
                        reset_timer(timer_id)
                        st.rerun()
                
                with control_cols[3]:
                    if st.button("🔊", key=f"test_{timer_id}", help="Test Sound"):
                        play_notification_sound(config["frequency"])
                
                st.markdown("---")

# Play sounds for newly finished timers
for timer_id, frequency, name in newly_finished:
    play_notification_sound(frequency)
    st.success(f"🎵 {name} finished!")

# Auto-refresh when any timer is running
any_running = any(st.session_state.timer_states.get(f"timer_{i}", {}).get("is_running", False) 
                  for i in range(st.session_state.num_timers))

if any_running:
    time.sleep(1)
    st.rerun()

# Instructions
st.markdown("---")
st.subheader("📋 Instructions")
st.markdown("**Configuration:**")
st.markdown("- Adjust the number of timers using the slider")
st.markdown("- Set custom names, durations, and sounds for each timer")
st.markdown("- Each timer can have a different musical note")

st.markdown("**Global Controls:**")
st.markdown("- **Start All**: Begin all timers simultaneously")
st.markdown("- **Stop All**: Pause all running timers")
st.markdown("- **Reset All**: Reset all timers to their original duration")

st.markdown("**Individual Controls:**")
st.markdown("- **▶️**: Start individual timer")
st.markdown("- **⏹️**: Stop individual timer")
st.markdown("- **🔄**: Reset individual timer")
st.markdown("- **🔊**: Test the timer's notification sound")

st.markdown("**Features:**")
st.markdown("- Timers run independently - start/stop any combination")
st.markdown("- Each timer plays its unique sound when finished")
st.markdown("- Real-time progress bars and countdown displays")
st.markdown("- Automatic audio notifications when timers complete")

# Footer
st.markdown("---")
st.markdown("*Configure each timer with custom durations and sounds for maximum flexibility*")

