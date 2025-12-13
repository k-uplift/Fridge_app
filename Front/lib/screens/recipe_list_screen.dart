import 'package:flutter/material.dart';
import '../models/recipe.dart';
import '../models/food_item.dart';
import '../services/api_service.dart'; // 서버 통신을 위해 추가
import './recipe_detail_screen.dart';

class RecipeListScreen extends StatefulWidget {
  final List<FoodItem> items;

  const RecipeListScreen({super.key, required this.items});

  @override
  State<RecipeListScreen> createState() => _RecipeListScreenState();
}

class _RecipeListScreenState extends State<RecipeListScreen> {
  bool _isLoading = true; // 로딩 상태 확인
  List<Recipe> _recommendedRecipes = []; // 서버에서 받은 레시피 저장할 리스트

  @override
  void initState() {
    super.initState();
    _fetchRecipeRecommendation(); // 화면이 켜지면 바로 서버 요청 시작
  }

  // [핵심] 서버에 레시피 추천 요청
  Future<void> _fetchRecipeRecommendation() async {
    try {
      // ApiService를 통해 서버에 현재 식재료 리스트 전송
      final apiResult = await ApiService().getRecipeRecommendation(widget.items);

      if (apiResult != null) {
        // 성공 시: JSON 데이터를 Recipe 객체로 변환
        final recipe = Recipe.fromJson(apiResult);
        
        if (mounted) {
          setState(() {
            _recommendedRecipes = [recipe]; // 리스트에 추가 (현재는 1개만 추천됨)
            _isLoading = false;
          });
        }
      } else {
        // 실패 시 (null 반환)
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('레시피를 받아오지 못했어요.')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
      print("레시피 로딩 에러: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('AI 추천 레시피'),
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text("AI가 맛있는 레시피를 생각 중이에요...", style: TextStyle(color: Colors.grey)),
                ],
              ),
            )
          : _recommendedRecipes.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.search_off, size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      Text(
                        '추천받은 레시피가 없어요.\n다시 시도해 주세요.',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: Colors.grey, fontSize: 16),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _recommendedRecipes.length,
                  itemBuilder: (context, index) {
                    final recipe = _recommendedRecipes[index];
                    
                    return Card(
                      color: Colors.white,
                      elevation: 2,
                      margin: const EdgeInsets.only(bottom: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () {
                          // 레시피 상세 화면으로 이동
                          showDialog(
                            context: context,
                            builder: (context) => RecipeDetailScreen(recipe: recipe),
                          );
                        },
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Text(
                                      recipe.name,
                                      style: const TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF0F172A),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Text(
                                      "추천",
                                      style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  const Icon(Icons.access_time, size: 16, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Text('${recipe.durationInMinutes}분', style: const TextStyle(color: Colors.grey)),
                                  const SizedBox(width: 16),
                                  const Icon(Icons.bar_chart, size: 16, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Text(recipe.difficulty, style: const TextStyle(color: Colors.grey)),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Text(
                                "필요 재료: ${recipe.ingredients.take(3).join(', ')}...",
                                style: TextStyle(color: Colors.grey[600], fontSize: 14),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}