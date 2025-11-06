import 'package:flutter/material.dart';
import '../models/food_item.dart';

class ExpiryBanner extends StatelessWidget {
  static const int warningDays = 6; // 유통 기한이 5일 이내로 남으면 배너 표시
  final List<FoodItem> items;
  const ExpiryBanner({super.key, required this.items});

  List<FoodItem> _getExpiringItems() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final warningDateLimit = today.add(const Duration(days: warningDays));

    List<FoodItem> expiringItems = items.where((item) {
      final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
      
      return (expiryDay.isAtSameMomentAs(today) || expiryDay.isAfter(today)) && 
             expiryDay.isBefore(warningDateLimit);
    }).toList();

    expiringItems.sort((a, b) => a.expiryDate.compareTo(b.expiryDate));

    return expiringItems;
  }

  @override
  Widget build(BuildContext context) {
    final List<FoodItem> expiringItems = _getExpiringItems();

    if (expiringItems.isEmpty) {
      return const SizedBox.shrink();
    }

    final firstItem = expiringItems.first;
    final remainingCount = expiringItems.length - 1;
    
    String message;
    if (remainingCount > 0) {
      message = '${firstItem.name} 외 $remainingCount개의 유통기한이 임박했습니다.';
    } else {
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final expiryDay = DateTime(firstItem.expiryDate.year, firstItem.expiryDate.month, firstItem.expiryDate.day);
      final difference = expiryDay.difference(today).inDays;

      String dayLabel;

      if (difference == 0) {
        dayLabel = '오늘 만료';
      } else {
        dayLabel = '$difference일 남음'; 
      }

      message = '${firstItem.name} ($dayLabel)';
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