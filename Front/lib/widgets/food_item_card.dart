import 'package:flutter/material.dart';
import '../models/food_item.dart';
import 'package:intl/intl.dart';

class FoodItemCard extends StatelessWidget {
  final FoodItem item;
  final VoidCallback onTap;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;
  final VoidCallback onLongPress;

  const FoodItemCard({
    super.key,
    required this.item,
    required this.onTap,
    required this.onIncrement,
    required this.onDecrement,
    required this.onLongPress,
  });

  Widget _buildExpiryChip() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
    final difference = expiryDay.difference(today).inDays;
    
    String label;
    Color chipColor;
    
    if (difference < 0) {
      label = '${difference.abs()}일 지남';
      chipColor = const Color(0xFF1A1A1A);
    } else if (difference == 0) {
      label = '오늘까지';
      chipColor = Colors.red.shade500;
    } else if (difference <= 3) {
      label = '$difference일 남음';
      chipColor = Colors.red.shade400;
    } else if (difference <= 7) {
      label = '$difference일 남음';
      chipColor = Colors.orange.shade400;
    } else {
      label = '$difference일 남음';
      chipColor = Colors.green.shade400;
    }
    
    return Chip(
      label: Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
      backgroundColor: chipColor,
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
      side: BorderSide.none,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  Widget _buildStorageChip() {
    String label;
    Color textColor;

    switch (item.storageLocation) {
      case StorageLocation.refrigerated:
        label = '냉장';
        textColor = Colors.blue.shade700;
        break;
      case StorageLocation.frozen:
        label = '냉동';
        textColor = Colors.indigo.shade800;
        break;
      case StorageLocation.roomTemperature:
        label = '실온';
        textColor = Colors.brown.shade600;
        break;
    }
    return Chip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: textColor,
          fontWeight: FontWeight.bold
        )
      ),
      backgroundColor: Colors.grey.shade200,
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
      side: BorderSide.none,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  String _getCategoryString() {
    switch (item.category) {
      case FoodCategory.dairy: return '유제품';
      case FoodCategory.meat: return '육류';
      case FoodCategory.vegetable: return '채소';
      case FoodCategory.fruit: return '과일';
      case FoodCategory.frozen: return '냉동식품';
      case FoodCategory.seasoning: return '조미료';
      case FoodCategory.cooked: return '조리음식';
      case FoodCategory.etc: return '기타';
    }
  }

  @override
  Widget build(BuildContext context) {
    final formattedDate = DateFormat('yyyy. MM. dd.').format(item.expiryDate);

    return Card(
      color: Colors.white,
      surfaceTintColor: Colors.white,
      elevation: 2,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      clipBehavior: Clip.hardEdge,
      
      child: InkWell(
        onTap: onTap,
        onLongPress: onLongPress,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            item.name,
                            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        _buildStorageChip(), // 보관 장소 칩
                        const SizedBox(width: 8),
                        _buildExpiryChip(), // 유통기한 칩
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('수량: ${item.quantity.toInt()}${item.unit}  |  분류: ${_getCategoryString()}'),
                    const SizedBox(height: 4),
                    Text('유통기한: $formattedDate'),
                  ],
                ),
              ),

              Column(
                children: [
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline),
                    onPressed: onIncrement,
                  ),
                  IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: onDecrement,
                  ),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }
}