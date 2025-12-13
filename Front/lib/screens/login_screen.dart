import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _idController = TextEditingController();
  final TextEditingController _pwController = TextEditingController();

  String? _loginIdErrorText;
  String? _loginPwErrorText;

  Future<void> _handleLogin() async {
    final id = _idController.text.trim();
    final pw = _pwController.text.trim();

    setState(() {
      _loginIdErrorText = id.isEmpty ? "아이디를 입력하세요." : null;
      _loginPwErrorText = pw.isEmpty ? "비밀번호를 입력하세요." : null;
    });

    if (id.isEmpty || pw.isEmpty) return;

    final prefs = await SharedPreferences.getInstance();
    final String? storedPw = prefs.getString(id);

    if (storedPw == null) {
      if (!mounted) return;
      
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: Colors.white,
          surfaceTintColor: Colors.white,
          content: const Text(
            "가입 되지 않은 계정이에요!\n회원가입을 해주세요.",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
          ),
          actions: [
            Center(
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  
                  Future.delayed(const Duration(milliseconds: 100), () { // 팝업 닫힘 대기 후 실행: 오류 방지
                    if (mounted) _showSignupDialog();
                  });
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0F172A),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: const Text("확인"),
              ),
            ),
          ],
        ),
      );
      
    } else if (storedPw != pw) {
      setState(() {
        _loginPwErrorText = "아이디나 비밀번호를 다시 확인해주세요.";
      });
    } else {
      if (!mounted) return;
      
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => HomeScreen(userId: id), 
        ),
      );
    }
  }

  void _showSignupDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const SignUpDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inputDecoration = InputDecoration(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      filled: true,
      fillColor: Colors.grey[50],
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );

    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(30.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Image.asset(
                'assets/icon/logo.png',
                height: 150,
                fit: BoxFit.contain,
              ),
              const SizedBox(height: 20),
              
              const Text(
                '환영합니다! 로그인을 해주세요.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 40),

              TextField(
                controller: _idController,
                decoration: inputDecoration.copyWith(
                  labelText: '아이디',
                  prefixIcon: const Icon(Icons.person_outline),
                  errorText: _loginIdErrorText,
                ),
                onChanged: (val) {
                  if (_loginIdErrorText != null) {
                    setState(() {
                      _loginIdErrorText = null;
                    });
                  }
                },
              ),
              const SizedBox(height: 16),

              TextField(
                controller: _pwController,
                obscureText: true,
                decoration: inputDecoration.copyWith(
                  labelText: '비밀번호',
                  prefixIcon: const Icon(Icons.lock_outline),
                  errorText: _loginPwErrorText,
                ),
                onChanged: (val) {
                  if (_loginPwErrorText != null) {
                    setState(() {
                      _loginPwErrorText = null;
                    });
                  }
                },
              ),
              const SizedBox(height: 30),

              ElevatedButton(
                onPressed: _handleLogin,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0F172A),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),

                child: Text(
                  '로그인',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    fontFamily: DefaultTextStyle.of(context).style.fontFamily, 
                  ),
                ),
              ),
              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    '계정이 없으신가요?',
                    style: TextStyle(color: Colors.grey),
                  ),
                  TextButton(
                    onPressed: _showSignupDialog,
                    child: const Text(
                      '회원가입',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SignUpDialog extends StatefulWidget { // 회원가입 팝업 위젯
  const SignUpDialog({super.key});

  @override
  State<SignUpDialog> createState() => _SignUpDialogState();
}

class _SignUpDialogState extends State<SignUpDialog> {
  final TextEditingController _idController = TextEditingController();
  final TextEditingController _pwController = TextEditingController();

  String _checkMsg = "";
  Color _msgColor = Colors.grey;
  bool _isIdChecked = false;

  String? _idErrorText;
  String? _pwErrorText;

  Future<void> _checkDuplicate() async {
    final inputId = _idController.text.trim();
    
    if (inputId.isEmpty) {
      setState(() {
        _idErrorText = "아이디를 입력하세요.";
        _checkMsg = "";
        _isIdChecked = false;
      });
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    if (prefs.containsKey(inputId)) {
      setState(() {
        _checkMsg = "이미 사용 중인 아이디에요.";
        _msgColor = Colors.red;
        _isIdChecked = false;
        _idErrorText = null;
      });
    } else {
      setState(() {
        _checkMsg = "사용 가능한 아이디에요.";
        _msgColor = Colors.green;
        _isIdChecked = true;
        _idErrorText = null;
      });
    }
  }

  Future<void> _submitSignup() async {
    final id = _idController.text.trim();
    final pw = _pwController.text.trim();

    setState(() {
      if (id.isEmpty) {
        _idErrorText = "아이디를 입력하세요.";
      } else if (!_isIdChecked) {
        _idErrorText = "아이디 중복 확인을 해주세요.";
      } else {
        _idErrorText = null;
      }

      if (pw.isEmpty) {
        _pwErrorText = "비밀번호를 입력하세요.";
      } else {
        _pwErrorText = null;
      }
    });

    if (_idErrorText != null || _pwErrorText != null) {
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(id, pw);

    if (!mounted) return;
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("회원가입을 완료했어요.")),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inputDecoration = InputDecoration(
      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      filled: true,
      fillColor: Colors.grey[50],
    );

    return AlertDialog(
      title: const Text("회원가입", style: TextStyle(fontWeight: FontWeight.bold)),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      content: SingleChildScrollView(
        child: SizedBox(
          width: 300,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _idController,
                      decoration: inputDecoration.copyWith(
                        labelText: "아이디",
                        errorText: _idErrorText,
                      ),
                      onChanged: (val) {
                        setState(() {
                          _isIdChecked = false;
                          _checkMsg = "";
                          if (val.isNotEmpty) _idErrorText = null;
                        });
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: ElevatedButton(
                      onPressed: _checkDuplicate,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0F172A),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 10),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: const Text("중복 확인", style: TextStyle(fontSize: 12)),
                    ),
                  ),
                ],
              ),
              if (_checkMsg.isNotEmpty && _idErrorText == null)
                Padding(
                  padding: const EdgeInsets.only(top: 5, left: 2),
                  child: Text(
                    _checkMsg,
                    style: TextStyle(
                      color: _msgColor,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              const SizedBox(height: 15),
              TextField(
                controller: _pwController,
                obscureText: true,
                decoration: inputDecoration.copyWith(
                  labelText: "비밀번호",
                  errorText: _pwErrorText,
                ),
                onChanged: (val) {
                  if (val.isNotEmpty && _pwErrorText != null) {
                    setState(() {
                      _pwErrorText = null;
                    });
                  }
                },
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("취소", style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton(
          onPressed: _submitSignup,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0F172A),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: const Text("가입하기"),
        ),
      ],
    );
  }
}