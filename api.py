from flask import Flask, request, jsonify
from flask_cors import CORS
from main import process_music # Import your algorithm's main function
import threading
import matplotlib.pyplot as plt 
import os # Added to handle folders


# ==============================================================================
#  IMPORT YOUR ALGORITHM HERE
# Assuming your algorithm is in a file named "my_audio_algorithm.py" 
# and the main function is called "process_music"
# ==============================================================================
# from my_audio_algorithm import process_music 

app = Flask(__name__, static_folder='static') # Added static_folder for audio streaming
CORS(app)

# Dictionary mapping song names to their file paths
SONGS = {
    'Seven Nation Army': 'songs/Seven Nation Army.mp3',
    'Dancing Queen': 'songs/Dancing Queen.mp3',
}

def calculate_syncrun_spm(height_cm, speed_kmh):
    if height_cm <= 0 or speed_kmh <= 0:
        return {"spm": 0, "pulse_interval_ms": 0}

    height_m = height_cm / 100.0
    speed_m_per_min = speed_kmh * (1000.0 / 60.0)

    dynamic_ratio = 0.35 + (speed_kmh * 0.025)
    dynamic_ratio = max(0.40, min(dynamic_ratio, 0.80))

    step_length_m = height_m * dynamic_ratio
    spm = speed_m_per_min / step_length_m
    pulse_interval_ms = 60000 / spm

    return {
        "spm": round(spm),
        "pulse_interval_ms": round(pulse_interval_ms)
    }

def generate_chunked_array_manual(height_cm, speeds_list, interval_sec):
    """
    Generates the exact 2.5s chunk array based on a manual list of speeds.
    """
    chunk_sec = 2.5
    chunks_per_interval = int(interval_sec / chunk_sec)
    
    target_spms = []
    
    for speed in speeds_list:
        # Calculate SPM for this specific interval's speed
        spm = calculate_syncrun_spm(height_cm, speed)["spm"]
        
        # Duplicate that SPM for exactly the right number of 2.5s chunks
        target_spms.extend([spm] * chunks_per_interval)
        
    return target_spms

def calculate_interval_metadata(drift_array, spm_array, interval_sec, segment_duration=2.5):
    """
    Pre-calculate interval boundaries accounting for drift.
    Returns: list of intervals with {start_time_ms, end_time_ms, spm}
    """
    intervals = []
    current_time_sec = 0.0
    chunks_per_interval = int(interval_sec / segment_duration)
    num_intervals = len(drift_array) // chunks_per_interval
    
    for i in range(num_intervals):
        start_chunk_idx = i * chunks_per_interval
        end_chunk_idx = (i + 1) * chunks_per_interval
        
        # Get SPM values for this interval
        interval_spms = spm_array[start_chunk_idx:end_chunk_idx]
        interval_drifts = drift_array[start_chunk_idx:end_chunk_idx]
        
        # Sum drift for this interval to get time adjustment
        total_drift_sec = sum(interval_drifts)
        
        # Actual duration = baseline + accumulated drift for this interval
        baseline_duration = chunks_per_interval * segment_duration
        actual_duration = baseline_duration + total_drift_sec
        
        # Use first segment's SPM as the display SPM
        display_spm = int(interval_spms[0])
        
        intervals.append({
            "start_time_ms": int(current_time_sec * 1000),
            "end_time_ms": int((current_time_sec + actual_duration) * 1000),
            "spm": display_spm,
            "duration_sec": actual_duration
        })
        
        current_time_sec += actual_duration
    
    return intervals

@app.route('/api/start_run', methods=['POST'])
def start_run():
    data = request.json
    height = data.get('height_cm', 175)
    interval_sec = data.get('interval_sec', 60)
    speeds_list = data.get('speeds_list', [10.0]) 
    song_name = data.get('song_name', 'Seven Nation Army') # Added Song Name!
    song_path = SONGS.get(song_name, 'songs/Seven Nation Army.mp3') # Use the dictionary to get the song path

    # 1. Generate your 2.5-second chunk array
    spm_array = generate_chunked_array_manual(height, speeds_list, interval_sec)
    
    # ==========================================
    # Print the raw numbers to your Python terminal:
    print(f"\n--- GENERATED SPM ARRAY ({len(spm_array)} chunks) ---")
    print(spm_array)
    print("------------------------------------------------\n")
    

    # 2. TRIGGER YOUR ALGORITHM IN THE BACKGROUND
    # Pass the song_name and spm_array to your algorithm and capture the result
    result = process_music(song_path, spm_array)
    drift_array = result.get('drift_array', []) if result else []
    
    # NEW: Calculate interval metadata accounting for drift
    intervals = calculate_interval_metadata(drift_array, spm_array, interval_sec)
    
    # 3. Calculate specs
    starting_specs = calculate_syncrun_spm(height, speeds_list[0])
    processed_audio_url = "http://127.0.0.1:5000/static/processed_output.wav"
    
    return jsonify({
        "status": "Algorithm Started",
        "starting_spm": starting_specs["spm"],
        "starting_pulse_ms": starting_specs["pulse_interval_ms"],
        "processed_audio_url": processed_audio_url,
        "intervals": intervals  # NEW: Pre-calculated interval data
    })

if __name__ == '__main__':
    # Automatically create the 'static' folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)