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
      appBar: AppBar(
        title: const Text('추천 레시피'),
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
                        : '등록된 레시피가 없어요.',
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
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: ListTile(
                    title: Text(recipe.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('조리 시간: ${recipe.durationInMinutes}분 | 난이도: ${recipe.difficulty}'),
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