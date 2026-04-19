from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def calculate_syncrun_spm(height_cm, speed_kmh):
    if height_cm <= 0 or speed_kmh <= 0:
        return {"spm": 0, "pulse_interval_ms": 0}

    height_m = height_cm / 100.0
    speed_m_per_min = speed_kmh * (1000.0 / 60.0)

    # The dynamic step ratio
    dynamic_ratio = 0.35 + (speed_kmh * 0.025)
    dynamic_ratio = max(0.40, min(dynamic_ratio, 0.80))

    step_length_m = height_m * dynamic_ratio
    spm = speed_m_per_min / step_length_m
    pulse_interval_ms = 60000 / spm

    return {
        "height_cm": height_cm,
        "speed_kmh": speed_kmh,
        "calculated_ratio": round(dynamic_ratio, 3),
        "spm": round(spm),
        "pulse_interval_ms": round(pulse_interval_ms)
    }

def generate_practice_array(height_cm, starting_speed_kmh, intervals=5, speed_jump=2.0):
    """
    Generates an array of target SPMs for an interval run.
    Each element represents the target SPM for that specific chunk/interval.
    """
    target_spms = []
    current_speed = starting_speed_kmh

    for _ in range(intervals):
        height_m = height_cm / 100.0
        speed_m_per_min = current_speed * (1000.0 / 60.0)

        dynamic_ratio = 0.35 + (current_speed * 0.025)
        dynamic_ratio = max(0.40, min(dynamic_ratio, 0.80))

        step_length_m = height_m * dynamic_ratio
        spm = speed_m_per_min / step_length_m
        
        target_spms.append(round(spm))
        current_speed += speed_jump

    return target_spms

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    height = data.get('height_cm', 175)
    speed = data.get('speed_kmh', 10.0)
    
    result = calculate_syncrun_spm(height, speed)
    return jsonify(result)

@app.route('/api/practice_array', methods=['POST'])
def practice_array():
    """
    API endpoint to get the entire 5-minute array at once via HTTP POST.
    """
    data = request.json
    height = data.get('height_cm', 175)
    speed = data.get('starting_speed_kmh', 10.0)
    intervals = data.get('intervals', 5)
    speed_jump = data.get('speed_jump', 2.0)
    
    result_array = generate_practice_array(height, speed, intervals, speed_jump)
    return jsonify({"target_spms": result_array})

if __name__ == '__main__':
    # host='0.0.0.0' allows external connections (like your phone or emulator)
    app.run(host='0.0.0.0', port=5000, debug=True)


    ''' how to use generate
    
        # Import the function from your api.py file
    from api import generate_practice_array

    # Call it before you start processing the audio chunks
    user_height = 175
    user_start_speed = 10

    bpm_targets = generate_practice_array(user_height, user_start_speed)

    # bpm_targets now equals exactly: [159, 176, 190, 203, 214]
    print(f"I need to stretch the audio chunks to these BPMs: {bpm_targets}")

    # Loop through your audio chunks here...
        
        
    
    
    
    '''