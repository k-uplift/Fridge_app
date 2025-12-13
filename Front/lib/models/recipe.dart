class Recipe {
  final String id;
  final String name;
  final int durationInMinutes;
  final String difficulty;
  final List<String> ingredients; // 전체 재료
  final List<String> steps; // 조리법
  final List<String> mainIngredients; // 주재료

  Recipe({
    required this.id,
    required this.name,
    required this.durationInMinutes,
    required this.difficulty,
    required this.ingredients,
    required this.steps,
    required this.mainIngredients,
  });

  factory Recipe.fromJson(Map<String, dynamic> json) { // 백엔드 JSON 키값에 맞춰서 데이터 변환하는 생성자
    return Recipe(
      id: json['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(), // ID는 서버에서 안 주면 현재 시간으로 임시 생성
      
      name: json['recipe_name'] ?? json['title'] ?? '이름 없는 요리', // 백엔드 키: "recipe_name" -> 앱 변수: name
      
      durationInMinutes: _parseDuration(json['time_required']), // 백엔드 키: "time_required" -> 숫자만 추출해서 저장
      
      difficulty: json['difficulty'] ?? '보통', // 백엔드 키: "difficulty"
      
      ingredients: json['ingredients_needed'] != null // 백엔드 키: "ingredients_needed"
          ? List<String>.from(json['ingredients_needed']) 
          : [],
          
      steps: json['steps'] != null // 백엔드 키: "steps"
          ? List<String>.from(json['steps']) 
          : [],
          
      mainIngredients: json['ingredients_main'] != null // 백엔드 키: "ingredients_main"
          ? List<String>.from(json['ingredients_main']) 
          : [],
    );
  }

  static int _parseDuration(dynamic timeData) {
    if (timeData == null) return 0;
    if (timeData is int) return timeData;
    
    final String timeStr = timeData.toString().replaceAll(RegExp(r'[^0-9]'), '');
    return int.tryParse(timeStr) ?? 0;
  }
}

// MOCK_RECIPES 리스트는 이제 필요 없으므로 제거 -> 백엔드 서버가 역할 대신