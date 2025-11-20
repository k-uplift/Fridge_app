import 'package:flutter/material.dart';
import '../models/recipe.dart';
import './recipe_detail_screen.dart';

class RecipeListScreen extends StatelessWidget {
  final String ingredientName;

  const RecipeListScreen({super.key, required this.ingredientName});

  @override
  Widget build(BuildContext context) {
    final List<Recipe> matchingRecipes = MOCK_RECIPES.where(
      (recipe) => recipe.mainIngredients.any(
        (mainIngredient) => ingredientName.contains(mainIngredient),
      ),
    ).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('$ingredientName(으)로 만들 수 있는 요리'),
      ),
      body: matchingRecipes.isEmpty
          ? const Center(
              child: Text('등록된 레시피가 없어요.'),
            )
          : ListView.builder(
              itemCount: matchingRecipes.length,
              itemBuilder: (context, index) {
                final recipe = matchingRecipes[index];
                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: ListTile(
                    title: Text(recipe.name),
                    subtitle: Text('${recipe.durationInMinutes}분 / 난이도: ${recipe.difficulty}'),
                    trailing: const Icon(Icons.arrow_forward_ios),
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