// 보관 위치 (냉장, 냉동, 상온)
enum StorageLocation {
  refrigerated,
  frozen,
  roomTemperature,
}

// 식재료 분류 (유제품, 육류 등)
enum FoodCategory {
  dairy,
  meat,
  vegetable,
  fruit,
  frozen,
  seasoning,
  cooked,
  etc,
}

class FoodItem {
  final String id;
  final String name;

  double quantity;

  final String unit;
  final FoodCategory category;
  final StorageLocation storageLocation;
  final DateTime expiryDate;

  FoodItem({
    required this.id,
    required this.name,
    required this.quantity,
    required this.unit,
    required this.category,
    required this.storageLocation,
    required this.expiryDate,
  });

  // 객체 복사를 위한 copyWith 메서드(수량 변경 외에 다른 속성도 바꿀 수 있도록 확장 가능)
  FoodItem copyWith({
    String? id,
    String? name,
    double? quantity,
    String? unit,
    FoodCategory? category,
    StorageLocation? storageLocation,
    DateTime? expiryDate,
  }) {
    return FoodItem(
      id: id ?? this.id,
      name: name ?? this.name,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      category: category ?? this.category,
      storageLocation: storageLocation ?? this.storageLocation,
      expiryDate: expiryDate ?? this.expiryDate,
    );
  }
}