import './food_item.dart';

enum HistoryAction {
  used,      // 사용완료
  discarded, // 폐기
}

class HistoryItem {
  final String id;
  final String name;
  final double quantity;
  final String unit;
  final DateTime date;
  final HistoryAction action;
  
  final FoodCategory category;
  final StorageLocation storageLocation;
  final DateTime expiryDate;

  HistoryItem({
    required this.id,
    required this.name,
    required this.quantity,
    required this.unit,
    required this.date,
    required this.action,
    required this.category,
    required this.storageLocation,
    required this.expiryDate,
  });
}