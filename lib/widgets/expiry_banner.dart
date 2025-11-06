import 'package:flutter/material.dart';
import '../models/food_item.dart';

class ExpiryBanner extends StatelessWidget {
  static const int warningDays = 3;
  final List<FoodItem> items;
  const ExpiryBanner({super.key, required this.items});

  List<FoodItem> _getExpiringItems() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    final warningDateLimit = today.add(const Duration(days: warningDays));

    return items.where((item) {
      final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
      
      return (expiryDay.isAtSameMomentAs(today) || expiryDay.isAfter(today)) && 
             expiryDay.isBefore(warningDateLimit);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final List<FoodItem> expiringItems = _getExpiringItems();

    if (expiringItems.isEmpty) {
      return const SizedBox.shrink();
    }

    final firstItemName = expiringItems.first.name;
    final remainingCount = expiringItems.length - 1;
    
    String message;
    if (remainingCount > 0) {
      message = '$firstItemName 외 $remainingCount개의 유통기한이 임박했습니다.';
    } else {
      message = '$firstItemName ($warningDays일 남음)';
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: Colors.amber.shade100,
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: Colors.amber[800]),

          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}
