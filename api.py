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

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    height = data.get('height_cm', 175)
    speed = data.get('speed_kmh', 10.0)
    
    result = calculate_syncrun_spm(height, speed)
    return jsonify(result)

if __name__ == '__main__':
    # host='0.0.0.0' allows external connections (like your phone or emulator)
    app.run(host='0.0.0.0', port=5000, debug=True)