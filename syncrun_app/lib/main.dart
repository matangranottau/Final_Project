import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async'; // Needed for the Interval Timer
import 'package:audioplayers/audioplayers.dart'; // Needed for Music

void main() {
  runApp(const SyncRunApp());
}

class SyncRunApp extends StatelessWidget {
  const SyncRunApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SyncRun',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFFAFAFA),
        primaryColor: Colors.black,
        fontFamily: 'Roboto',
      ),
      home: const InputScreen(),
    );
  }
}

// --- SCREEN 1: Input Screen ---
class InputScreen extends StatefulWidget {
  const InputScreen({super.key});

  @override
  State<InputScreen> createState() => _InputScreenState();
}

class _InputScreenState extends State<InputScreen> {
  int _heightCm = 175;
  double _speedKmh = 10.0;
  bool _isLoading = false;
  
  // New State Variables for the Dropdowns
  String _selectedMode = "Free Run";
  String _selectedSong = "Seven Nation Army";

  Future<void> _startRun() async {
    setState(() => _isLoading = true);

    // Using 127.0.0.1 for Chrome/Web as we discussed!
    final url = Uri.parse('http://127.0.0.1:5000/api/calculate'); 

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"height_cm": _heightCm, "speed_kmh": _speedKmh}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        setState(() => _isLoading = false);
        if (!mounted) return;
        
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => PulseScreen(
              initialSpm: data["spm"],
              initialIntervalMs: data["pulse_interval_ms"],
              heightCm: _heightCm,
              initialSpeed: _speedKmh,
              mode: _selectedMode,
              songName: _selectedSong,
            ),
          ),
        );
      } else {
        setState(() => _isLoading = false);
        print("Server error: ${response.statusCode}");
      }
    } catch (e) {
      setState(() => _isLoading = false);
      print("Error connecting to server: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView( // Added scroll view so keyboards/small screens don't cut off
          padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 40.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Text(
                "Welcome to SyncRun",
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.w300, letterSpacing: 1.5),
              ),
              const SizedBox(height: 30),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.headphones, size: 28, color: Colors.black54),
                  SizedBox(width: 20),
                  Icon(Icons.directions_run, size: 32, color: Colors.black87),
                  SizedBox(width: 20),
                  Icon(Icons.water_drop_outlined, size: 28, color: Colors.black54),
                ],
              ),
              const SizedBox(height: 40),

              // Mode Selection Dropdown
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.grey.shade300)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedMode,
                    icon: const Icon(Icons.arrow_drop_down, color: Colors.black),
                    onChanged: (String? newValue) => setState(() => _selectedMode = newValue!),
                    items: <String>['Free Run', '5-Min Interval Practice']
                        .map<DropdownMenuItem<String>>((String value) {
                      return DropdownMenuItem<String>(value: value, child: Text(value, style: const TextStyle(fontSize: 16)));
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Song Selection Dropdown
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.grey.shade300)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedSong,
                    icon: const Icon(Icons.music_note, color: Colors.black),
                    onChanged: (String? newValue) => setState(() => _selectedSong = newValue!),
                    items: <String>['Seven Nation Army', 'Dancing Queen']
                        .map<DropdownMenuItem<String>>((String value) {
                      return DropdownMenuItem<String>(value: value, child: Text(value, style: const TextStyle(fontSize: 16)));
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 40),

              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Height: $_heightCm cm", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Slider(
                    value: _heightCm.toDouble(),
                    min: 90, max: 230, divisions: 140,
                    activeColor: Colors.black, inactiveColor: Colors.grey.shade300,
                    onChanged: (val) => setState(() => _heightCm = val.round()),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Starting Speed: ${_speedKmh.toStringAsFixed(1)} km/h", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Slider(
                    value: _speedKmh,
                    min: 1.0, max: 25.0, divisions: 240,
                    activeColor: Colors.black, inactiveColor: Colors.grey.shade300,
                    onChanged: (val) => setState(() => _speedKmh = val),
                  ),
                ],
              ),
              const SizedBox(height: 50),

              SizedBox(
                width: double.infinity, height: 55,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue, foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                  ),
                  onPressed: _isLoading ? null : _startRun,
                  child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("START RUN", style: TextStyle(fontSize: 16, letterSpacing: 2)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// --- SCREEN 2: The Pulse Screen ---
class PulseScreen extends StatefulWidget {
  final int initialSpm;
  final int initialIntervalMs;
  final int heightCm;
  final double initialSpeed;
  final String mode;
  final String songName;

  const PulseScreen({
    super.key, 
    required this.initialSpm, 
    required this.initialIntervalMs,
    required this.heightCm,
    required this.initialSpeed,
    required this.mode,
    required this.songName
  });

  @override
  State<PulseScreen> createState() => _PulseScreenState();
}

class _PulseScreenState extends State<PulseScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late AudioPlayer _audioPlayer;
  Timer? _intervalTimer;

  // Mutable state variables that will update during the 5-min practice
  late int _currentSpm;
  late int _currentIntervalMs;
  late double _currentSpeed;
  int _minutesPassed = 0;

  @override
  void initState() {
    super.initState();
    _currentSpm = widget.initialSpm;
    _currentIntervalMs = widget.initialIntervalMs;
    _currentSpeed = widget.initialSpeed;

    // 1. Setup Audio Player
    _audioPlayer = AudioPlayer();
    _playSong();

    // 2. Setup Animation
    _setupAnimation();

    // 3. Setup Practice Timer (if mode is selected)
    if (widget.mode == '5-Min Interval Practice') {
      _startPracticeTimer();
    }
  }

  void _setupAnimation() {
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: _currentIntervalMs ~/ 2),
    );
    _scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _controller.repeat(reverse: true);
  }

  Future<void> _playSong() async {
    // Map the selected song name to the correct filename
    String fileName = widget.songName == 'Seven Nation Army' 
        ? 'seven_nation_army.mp3' 
        : 'dancing_queen.mp3';
    
    // Play the audio from the assets folder
    await _audioPlayer.play(AssetSource(fileName));
  }

  void _startPracticeTimer() {
    // This timer ticks exactly once every 60 seconds
    _intervalTimer = Timer.periodic(const Duration(minutes: 1), (timer) async {
      _minutesPassed++;

      if (_minutesPassed >= 5) {
        timer.cancel(); // Stop the interval changes after 5 minutes
        return;
      }

      // Increase speed by 2 km/h
      double newSpeed = _currentSpeed + 2.0;

      // Ask Python for the new SPM based on the new speed
      final url = Uri.parse('http://127.0.0.1:5000/api/calculate'); 
      try {
        final response = await http.post(
          url,
          headers: {"Content-Type": "application/json"},
          body: jsonEncode({"height_cm": widget.heightCm, "speed_kmh": newSpeed}),
        );

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          
          setState(() {
            _currentSpeed = newSpeed;
            _currentSpm = data["spm"];
            _currentIntervalMs = data["pulse_interval_ms"];
          });

          // Update the animation to pulse at the new, faster rate!
          _controller.duration = Duration(milliseconds: _currentIntervalMs ~/ 2);
          _controller.reset();
          _controller.repeat(reverse: true);
        }
      } catch (e) {
        print("Error fetching new interval: $e");
      }
    });
  }

  // --- THE HALT FUNCTION ---
  void _haltRun() {
    _intervalTimer?.cancel(); // Kill the timer
    _audioPlayer.stop();      // Kill the music
    Navigator.pop(context);   // Go back to the first screen
  }

  @override
  void dispose() {
    _controller.dispose();
    _intervalTimer?.cancel();
    _audioPlayer.dispose(); // Stop the music when leaving the screen
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Display Song Name
            Text(
              "🎵 ${widget.songName}",
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w500, letterSpacing: 1),
            ),
            const SizedBox(height: 10),
            
            // Display Current Mode & Speed
            Text(
              "${widget.mode} • ${_currentSpeed.toStringAsFixed(1)} km/h",
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 60),

            // The Pulsing Ball
            AnimatedBuilder(
              animation: _scaleAnimation,
              builder: (context, child) {
                return Transform.scale(
                  scale: _scaleAnimation.value,
                  child: Container(
                    width: 200,
                    height: 200,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.black.withOpacity(0.85),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 30, spreadRadius: 10)
                      ]
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 60),
            
            // Subtle SPM display
            Text(
              "$_currentSpm SPM",
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w300, color: Colors.grey, letterSpacing: 2),
            ),
            const SizedBox(height: 40),

            // --- THE HALT BUTTON ---
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
              ),
              icon: const Icon(Icons.stop_circle_outlined, size: 24),
              label: const Text("STOP RUN", style: TextStyle(fontSize: 16, letterSpacing: 1.5)),
              onPressed: _haltRun,
            )
          ],
        ),
      ),
    );
  }
}