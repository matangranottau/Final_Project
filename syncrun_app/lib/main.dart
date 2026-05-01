import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async'; 
import 'package:audioplayers/audioplayers.dart'; // Added Audioplayers back!

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
  bool _isLoading = false;
  
  String _selectedMode = "Free Run";
  int _intervalDurationSec = 60; 
  String _selectedSong = "Seven Nation Army"; // Added Song State
  
  List<double> _speedsList = [10.0];

  Future<void> _startRun() async {
    setState(() => _isLoading = true);

    final url = Uri.parse('http://127.0.0.1:5000/api/start_run'); 

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "height_cm": _heightCm, 
          "interval_sec": _selectedMode == "Free Run" ? 9999 : _intervalDurationSec, 
          "speeds_list": _speedsList,
          "song_name": _selectedSong // Sending the selected song
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        setState(() => _isLoading = false);
        if (!mounted) return;
        
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => PulseScreen(
              initialSpm: data["starting_spm"],
              initialIntervalMs: data["starting_pulse_ms"],
              heightCm: _heightCm,
              speedsList: _speedsList,
              mode: _selectedMode,
              intervalDurationSec: _intervalDurationSec,
              songName: _selectedSong,
              processedAudioUrl: data["processed_audio_url"], // Receiving the URL
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
        child: SingleChildScrollView( 
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

              // Height Selection
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
              const SizedBox(height: 30),

              // Mode Selection
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.grey.shade300)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedMode,
                    icon: const Icon(Icons.arrow_drop_down, color: Colors.black),
                    onChanged: (String? newValue) {
                      setState(() {
                        _selectedMode = newValue!;
                        if (_selectedMode == "Free Run") {
                          _speedsList = [_speedsList[0]];
                        }
                      });
                    },
                    items: <String>['Free Run', 'Interval Practice']
                        .map<DropdownMenuItem<String>>((String value) {
                      return DropdownMenuItem<String>(value: value, child: Text(value, style: const TextStyle(fontSize: 16)));
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Song Selection
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
              const SizedBox(height: 20),

              if (_selectedMode == 'Interval Practice') ...[
                // Interval Duration
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.grey.shade300)),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<int>(
                      isExpanded: true,
                      value: _intervalDurationSec,
                      icon: const Icon(Icons.timer, color: Colors.black),
                      onChanged: (int? newValue) => setState(() => _intervalDurationSec = newValue!),
                      items: <int>[15, 20, 25, 60]
                          .map<DropdownMenuItem<int>>((int value) {
                        return DropdownMenuItem<int>(value: value, child: Text("$value Seconds per Interval", style: const TextStyle(fontSize: 16)));
                      }).toList(),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // DYNAMIC SPEED INPUTS
              ...List.generate(_speedsList.length, (index) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _selectedMode == 'Free Run' ? "Run Speed: ${_speedsList[index].toStringAsFixed(1)} km/h" : "Interval ${index + 1} Speed: ${_speedsList[index].toStringAsFixed(1)} km/h", 
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)
                        ),
                        if (_selectedMode == 'Interval Practice' && index > 0)
                          IconButton(
                            icon: const Icon(Icons.close, color: Colors.red),
                            onPressed: () => setState(() => _speedsList.removeAt(index)),
                          )
                      ],
                    ),
                    Slider(
                      value: _speedsList[index],
                      min: 1.0, max: 25.0, divisions: 240,
                      activeColor: Colors.blueAccent, inactiveColor: Colors.grey.shade300,
                      onChanged: (val) => setState(() => _speedsList[index] = val),
                    ),
                    const SizedBox(height: 10),
                  ],
                );
              }),

              if (_selectedMode == 'Interval Practice')
                TextButton.icon(
                  onPressed: () => setState(() => _speedsList.add(10.0)), 
                  icon: const Icon(Icons.add_circle, color: Colors.black),
                  label: const Text("ADD INTERVAL", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                ),

              const SizedBox(height: 50),

              SizedBox(
                width: double.infinity, height: 55,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black, foregroundColor: Colors.white,
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
  final List<double> speedsList;
  final String mode;
  final String songName; // Needed for display
  final int intervalDurationSec;
  final String processedAudioUrl; // Needed for streaming

  const PulseScreen({
    super.key, 
    required this.initialSpm, 
    required this.initialIntervalMs,
    required this.heightCm,
    required this.speedsList,
    required this.mode,
    required this.songName,
    required this.intervalDurationSec,
    required this.processedAudioUrl,
  });

  @override
  State<PulseScreen> createState() => _PulseScreenState();
}

class _PulseScreenState extends State<PulseScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late AudioPlayer _audioPlayer; // AudioPlayer is back!
  Timer? _uiSyncTimer;

  late int _currentSpm;
  late int _currentIntervalMs;
  late double _currentSpeed;
  int _currentIntervalIndex = 0;

  @override
  void initState() {
    super.initState();
    _currentSpm = widget.initialSpm;
    _currentIntervalMs = widget.initialIntervalMs;
    _currentSpeed = widget.speedsList[0];

    _audioPlayer = AudioPlayer();
    _playProcessedSong(); 
    _setupAnimation();

    if (widget.mode == 'Interval Practice' && widget.speedsList.length > 1) {
      _startUiSyncTimer();
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

  // This is where it streams the processed song from your Python static folder!
  Future<void> _playProcessedSong() async {
    await _audioPlayer.play(UrlSource(widget.processedAudioUrl));
  }

  void _startUiSyncTimer() {
    _uiSyncTimer = Timer.periodic(Duration(seconds: widget.intervalDurationSec), (timer) {
      _currentIntervalIndex++;

      if (_currentIntervalIndex >= widget.speedsList.length) {
        _haltRun();
        return;
      }

      double nextSpeed = widget.speedsList[_currentIntervalIndex];
      
      double dynamicRatio = 0.35 + (nextSpeed * 0.025);
      dynamicRatio = dynamicRatio.clamp(0.40, 0.80);
      double spm = (nextSpeed * (1000.0 / 60.0)) / ((widget.heightCm / 100.0) * dynamicRatio);
      
      setState(() {
        _currentSpeed = nextSpeed;
        _currentSpm = spm.round();
        _currentIntervalMs = (60000 / spm).round();
      });

      _controller.duration = Duration(milliseconds: _currentIntervalMs ~/ 2);
      _controller.reset();
      _controller.repeat(reverse: true);
    });
  }

  void _haltRun() {
    _uiSyncTimer?.cancel();
    _audioPlayer.stop(); // Stops the music
    if (mounted) Navigator.pop(context);   
  }

  @override
  void dispose() {
    _controller.dispose();
    _uiSyncTimer?.cancel();
    _audioPlayer.dispose(); // Cleans up the audio player
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
            Text(
              "🎵 ${widget.songName}", // Shows the song name on screen
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w500, letterSpacing: 1),
            ),
            const SizedBox(height: 10),
            
            Text(
              "${widget.mode} • ${_currentSpeed.toStringAsFixed(1)} km/h",
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 60),

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
            
            Text(
              "$_currentSpm SPM",
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w300, color: Colors.grey, letterSpacing: 2),
            ),
            const SizedBox(height: 40),

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