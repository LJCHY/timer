import streamlit as st
import time
from datetime import datetime, timedelta
import base64

# Configure page
st.set_page_config(
    page_title="Multi-Timer Countdown",
    page_icon="⏰",
    layout="wide"
)

# Initialize session state
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'finished_timers' not in st.session_state:
    st.session_state.finished_timers = set()

# Timer configurations (minutes, display name, sound frequency)
TIMERS = [
    (75, "75+0", 440),    # A4 note
    (81.25, "75+6.25", 523),    # C5 note
    (87.5, "75+12.5", 659),   # E5 note
    (93.75, "75+18.75", 783)
]

def generate_beep_sound(frequency=440, duration=0.5, sample_rate=44100):
    """Generate a simple beep sound as base64 encoded audio"""
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

def format_time(seconds):
    """Format seconds into MM:SS format"""
    if seconds <= 0:
        return "00:00"
    
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def get_time_remaining(duration_minutes, start_time):
    """Calculate remaining time for a timer"""
    if start_time is None:
        return duration_minutes * 60
    
    elapsed = (datetime.now() - start_time).total_seconds()
    remaining = (duration_minutes * 60) - elapsed
    return max(0, remaining)

def play_notification_sound(frequency):
    """Play a notification sound using HTML audio"""
    try:
        audio_data = generate_beep_sound(frequency, 1.0)  # 1 second beep
        audio_html = f"""
        <audio autoplay>
            <source src="{audio_data}" type="audio/wav">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback: show a visual notification if audio fails
        st.warning(f"🔔 Timer finished! (Audio unavailable: {str(e)})")

# Title
st.title("⏰ Multi-Timer Countdown")
st.markdown("**Each timer has a unique sound when it finishes!**")
st.markdown("---")

# Control buttons
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("🚀 Start All Timers", disabled=st.session_state.is_running):
        st.session_state.start_time = datetime.now()
        st.session_state.is_running = True
        st.session_state.finished_timers = set()
        st.rerun()

with col2:
    if st.button("🔄 Reset All Timers"):
        st.session_state.start_time = None
        st.session_state.is_running = False
        st.session_state.finished_timers = set()
        st.rerun()

# Status
if st.session_state.is_running:
    st.success("✅ Timers are running!")
else:
    st.info("⏹️ Timers are stopped")

st.markdown("---")

# Sound frequency legend
st.markdown("### 🎵 Sound Legend:")
sound_cols = st.columns(6)
for i, (duration, name, freq) in enumerate(TIMERS):
    with sound_cols[i]:
        note_names = ["A4", "C5", "E5"]
        st.markdown(f"**{name}**: {note_names[i]} ({freq}Hz)")

st.markdown("---")

# Display timers in a grid
col1, col2, col3 = st.columns(3)
columns = [col1, col2, col3]

newly_finished = []

for i, (duration_minutes, display_name, frequency) in enumerate(TIMERS):
    col_index = i % 3
    
    with columns[col_index]:
        # Calculate remaining time
        remaining_seconds = get_time_remaining(duration_minutes, st.session_state.start_time)
        
        # Check if timer just finished
        timer_id = f"{display_name}_{duration_minutes}"
        just_finished = (remaining_seconds <= 0 and 
                        st.session_state.is_running and 
                        timer_id not in st.session_state.finished_timers)
        
        if just_finished:
            newly_finished.append((timer_id, frequency, display_name))
            st.session_state.finished_timers.add(timer_id)
        
        # Determine status and color
        if remaining_seconds <= 0 and st.session_state.is_running:
            status = "🔔 FINISHED!"
            color = "red"
        elif st.session_state.is_running:
            status = "🏃 Running"
            color = "green"
        else:
            status = "⏸️ Ready"
            color = "blue"
        
        # Create a container for each timer
        with st.container():
            st.markdown(f"### {display_name}")
            st.markdown(f"**Duration:** {duration_minutes} minutes")
            
            # Large time display
            time_display = format_time(remaining_seconds)
            st.markdown(f"<h1 style='text-align: center; color: {color}; font-family: monospace;'>{time_display}</h1>", 
                       unsafe_allow_html=True)
            
            st.markdown(f"<p style='text-align: center; color: {color}; font-weight: bold;'>{status}</p>", 
                       unsafe_allow_html=True)
            
            # Progress bar
            if st.session_state.is_running:
                progress = max(0, 1 - (remaining_seconds / (duration_minutes * 60)))
                st.progress(progress)
            else:
                st.progress(0)
            
            # Test sound button
            if st.button(f"🔊 Test Sound", key=f"test_{timer_id}"):
                play_notification_sound(frequency)
            
            st.markdown("---")

# Play sounds for newly finished timers
for timer_id, frequency, name in newly_finished:
    play_notification_sound(frequency)
    st.success(f"🎵 {name} timer finished!")

# Auto-refresh when running
if st.session_state.is_running:
    # Check if all timers are finished
    all_finished = True
    for duration_minutes, _, _ in TIMERS:
        remaining = get_time_remaining(duration_minutes, st.session_state.start_time)
        if remaining > 0:
            all_finished = False
            break
    
    if all_finished:
        st.session_state.is_running = False
        st.balloons()
        st.success("🎉 All timers have finished!")
    else:
        # Refresh every second
        time.sleep(1)
        st.rerun()

# Instructions
st.markdown("---")
st.markdown("### Instructions:")
st.markdown("1. Click **'Start All Timers'** to begin all countdowns simultaneously")
st.markdown("2. Each timer will play a different musical note when it finishes")
st.markdown("3. Use the **'Test Sound'** buttons to preview each timer's sound")
st.markdown("4. Finished timers will be highlighted in red")
st.markdown("5. Click **'Reset All Timers'** to stop and reset all timers")

# Technical note
st.markdown("---")
st.markdown("### 🔧 Audio Notes:")
st.markdown("- Sounds are generated as pure sine wave tones")
st.markdown("- Different musical notes help distinguish which timer finished")
st.markdown("- If audio doesn't work, check your browser's audio permissions")
st.markdown("- Each timer plays a 1-second tone when it reaches zero")

# Footer
st.markdown("---")

st.markdown("*Timer names indicate base time (70 minutes) plus additional minutes*")
