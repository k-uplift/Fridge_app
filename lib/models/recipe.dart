class Recipe {
  final String id;
  final String name;
  final int durationInMinutes;
  final String difficulty;
  final List<String> ingredients;
  final List<String> steps;
  final List<String> mainIngredients;

  Recipe({
    required this.id,
    required this.name,
    required this.durationInMinutes,
    required this.difficulty,
    required this.ingredients,
    required this.steps,
    required this.mainIngredients,
  });
}

// 임시 레시피 데이터
final List<Recipe> MOCK_RECIPES = [
  Recipe(
    id: 'r1',
    name: '프렌치 토스트',
    durationInMinutes: 15,
    difficulty: '쉬움',
    mainIngredients: ['우유', '계란', '식빵'],
    ingredients: [
      '우유 100ml',
      '계란 2개',
      '식빵 2조각',
      '설탕 1스푼',
      '버터 1조각',
    ],
    steps: [
      '계란과 우유, 설탕을 섞어 계란물을 만듭니다.',
      '식빵을 계란물에 충분히 적십니다.',
      '달궈진 팬에 버터를 녹이고 식빵을 굽습니다.',
      '양면이 노릇해질 때까지 구워주세요.',
      '설탕이나 시럽을 뿌려 완성합니다.',
    ],
  ),
  
  Recipe(
    id: 'r2',
    name: '크림 스프',
    durationInMinutes: 30,
    difficulty: '보통',
    mainIngredients: ['우유', '감자', '양파'],
    ingredients: [
      '우유 200ml',
      '감자 1개',
      '양파 1/2개',
      '버터 1조각',
      '소금 약간',
      '후추 약간',
    ],
    steps: [
      '감자와 양파는 껍질을 벗기고 잘게 썬다.',
      '냄비에 버터를 녹이고 양파를 볶는다.',
      '양파가 투명해지면 감자를 넣고 볶는다.',
      '물을 약간 붓고 감자가 익을 때까지 끓인다.',
      '믹서기로 곱게 간 후 다시 냄비에 붓는다.',
      '우유를 붓고 약한 불에서 끓이다가 소금, 후추로 간을 맞춘다.',
    ],
  ),
  
  Recipe(
    id: 'r3',
    name: '계란말이',
    durationInMinutes: 10,
    difficulty: '쉬움',
    mainIngredients: ['계란'],
    ingredients: [
      '계란 3개',
      '당근 약간',
      '쪽파 약간',
      '소금 한 꼬집',
    ],
    steps: [
      '당근과 쪽파를 잘게 다집니다.',
      '계란을 풀고 다진 야채와 소금을 넣어 섞습니다.',
      '팬에 기름을 두르고 계란물의 1/3을 붓습니다.',
      '계란이 반쯤 익으면 돌돌 말아 팬 한쪽으로 옮깁니다.',
      '남은 계란물을 2번에 나눠 부으면서 반복하여 두툼하게 만듭니다.',
    ],
  ),
];
