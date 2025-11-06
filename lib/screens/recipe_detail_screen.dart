import 'package:flutter/material.dart';
import '../models/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  final Recipe recipe;

  const RecipeDetailScreen({super.key, required this.recipe});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(recipe.name),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.timer_outlined, size: 16),
                const SizedBox(width: 4),
                Text('${recipe.durationInMinutes}분'),
                const SizedBox(width: 16),
                const Icon(Icons.leaderboard_outlined, size: 16),
                const SizedBox(width: 4),
                Text('난이도: ${recipe.difficulty}'),
              ],
            ),
            const Divider(height: 32),

            Text(
              '필요한 재료',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            ...recipe.ingredients.map((ingredient) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4.0),
                child: Text('• $ingredient'), 
              );
            }).toList(),
            const Divider(height: 32),

            Text(
              '조리 방법',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            ...recipe.steps.asMap().entries.map((entry) {
              int index = entry.key + 1;
              String step = entry.value;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: Text('$index. $step'),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }
}