import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/home_screen.dart';
import 'screens/splash_screen.dart'; // [1] 새로 만든 스플래시 화면 파일을 불러옵니다.

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '냉장고 관리 앱',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F172A)),
        useMaterial3: true,
        textTheme: GoogleFonts.juaTextTheme(
          Theme.of(context).textTheme,
        ),
      ),
      // [2] 여기가 핵심입니다! 
      // 앱을 처음 켤 때 HomeScreen 대신 SplashScreen이 먼저 뜨게 합니다.
      home: const SplashScreen(), 
    );
  }
}