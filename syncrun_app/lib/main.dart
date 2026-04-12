import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

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

  Future<void> _startRun() async {
    setState(() => _isLoading = true);

    // CRITICAL: Choose the correct URL based on your testing environment:
    // Android Emulator: http://10.0.2.2:5000/api/calculate
    // iOS Simulator: http://127.0.0.1:5000/api/calculate
    // Physical Phone/Web: http://<YOUR_COMPUTER_IP>:5000/api/calculate
    final url = Uri.parse('http://127.0.0.1:5000/api/calculate'); 

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "height_cm": _heightCm,
          "speed_kmh": _speedKmh
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
              spm: data["spm"],
              intervalMs: data["pulse_interval_ms"], 
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
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                "Welcome to SyncRun",
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.w300, letterSpacing: 1.5, color: Colors.black),
              ),
              const SizedBox(height: 40),
              
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
              const SizedBox(height: 60),

              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Height: $_heightCm cm", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Slider(
                    value: _heightCm.toDouble(),
                    min: 90,
                    max: 230,
                    divisions: 140,
                    activeColor: Colors.black,
                    inactiveColor: Colors.grey.shade300,
                    onChanged: (val) => setState(() => _heightCm = val.round()),
                  ),
                ],
              ),
              const SizedBox(height: 30),

              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Target Speed: ${_speedKmh.toStringAsFixed(1)} km/h", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Slider(
                    value: _speedKmh,
                    min: 1.0,
                    max: 25.0,
                    divisions: 240,
                    activeColor: Colors.black,
                    inactiveColor: Colors.grey.shade300,
                    onChanged: (val) => setState(() => _speedKmh = val),
                  ),
                ],
              ),
              const SizedBox(height: 60),

              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
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
  final int spm;
  final int intervalMs;

  const PulseScreen({super.key, required this.spm, required this.intervalMs});

  @override
  State<PulseScreen> createState() => _PulseScreenState();
}

class _PulseScreenState extends State<PulseScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    
    // Divide by 2 because the animation expands AND shrinks to complete one cycle
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: widget.intervalMs ~/ 2),
    );

    _scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
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
                        BoxShadow(
                          color: Colors.black.withOpacity(0.2),
                          blurRadius: 30,
                          spreadRadius: 10,
                        )
                      ]
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 60),
            
            Text(
              "${widget.spm} SPM",
              style: const TextStyle(
                fontSize: 16, 
                fontWeight: FontWeight.w300, 
                color: Colors.grey,
                letterSpacing: 2
              ),
            ),
          ],
        ),
      ),
    );
  }
}