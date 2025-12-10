import 'package:flutter/material.dart';
import '../models/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  final Recipe recipe;

  const RecipeDetailScreen({super.key, required this.recipe});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(recipe.name),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(24.0),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.timer_outlined, size: 20),
                  const SizedBox(width: 4),
                  Text(
                    '${recipe.durationInMinutes}분',
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(width: 24),
                  const Icon(Icons.leaderboard_outlined, size: 20),
                  const SizedBox(width: 4),
                  Text(
                    '난이도: ${recipe.difficulty}',
                    style: const TextStyle(fontSize: 16),
                  ),
                ],
              ),
              const Divider(height: 48),

              Text(
                '필요한 재료',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 12),
              ...recipe.ingredients.map((ingredient) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(fontSize: 16)),
                      Expanded(
                        child: Text(ingredient, style: const TextStyle(fontSize: 16)),
                      ),
                    ],
                  ),
                );
              }).toList(),
              const Divider(height: 48),

              Text(
                '조리 방법',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 12),
              ...recipe.steps.asMap().entries.map((entry) {
                int index = entry.key + 1;
                String step = entry.value;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$index. ',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      Expanded(
                        child: Text(
                          step,
                          style: const TextStyle(fontSize: 16, height: 1.5),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ],
          ),
        ),
      ),
    );
  }
}