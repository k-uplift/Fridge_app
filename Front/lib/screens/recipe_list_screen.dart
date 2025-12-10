import 'package:flutter/material.dart';
import '../models/recipe.dart';
import '../models/food_item.dart';
import './recipe_detail_screen.dart';

class RecipeListScreen extends StatelessWidget {
  final List<FoodItem> items;

  const RecipeListScreen({super.key, required this.items});

  @override
  Widget build(BuildContext context) {
    final List<String> myIngredientNames = items.map((e) => e.name).toList();

    final List<Recipe> matchingRecipes = MOCK_RECIPES.where(
      (recipe) => recipe.mainIngredients.any(
        (mainIngredient) => myIngredientNames.any(
          (myName) => myName.contains(mainIngredient),
        ),
      ),
    ).toList();

    matchingRecipes.sort((a, b) => a.name.compareTo(b.name));

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('추천 레시피'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: matchingRecipes.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.search_off, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  Text(
                    items.isEmpty
                        ? '선택된 재료가 없어요.'
                        : '이 재료들로는 만들 수 있는\n레시피가 없어요.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.grey, fontSize: 16),
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: matchingRecipes.length,
              itemBuilder: (context, index) {
                final recipe = matchingRecipes[index];
                return Card(
                  color: Colors.white,
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: ListTile(
                    title: Text(recipe.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('${recipe.durationInMinutes}분  |  난이도: ${recipe.difficulty}'),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => RecipeDetailScreen(recipe: recipe),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
    );
  }
}