import 'dart:io';
import '../models/food_item.dart';

class OcrService { // 서버로 이미지를 전송하고, 보정된 품목 리스트를 받아오는 함수
  Future<List<FoodItem>> uploadImageAndGetItems(File imageFile) async {
    // (실제 구현 시) 여기서 http.MultipartRequest 등을 사용해 서버로 이미지 전송
    // 가짜 지연 시간 (서버 처리 시간 시뮬레이션)
    await Future.delayed(const Duration(seconds: 2));

    // 서버에서 LLM 보정 후 돌아올 것으로 예상되는 데이터 (품목명, 개수, 보관 위치, 유통기한")
    return [
      FoodItem(
        id: DateTime.now().toString() + '_1',
        name: '사과',
        quantity: 3,
        unit: '개',
        category: FoodCategory.fruit,
        storageLocation: StorageLocation.refrigerated, // 냉장
        expiryDate: DateTime.now().add(const Duration(days: 14)), // 2주 후
      ),
      FoodItem(
        id: DateTime.now().toString() + '_2',
        name: '삼겹살',
        quantity: 600,
        unit: 'g',
        category: FoodCategory.meat,
        storageLocation: StorageLocation.frozen, // 냉동
        expiryDate: DateTime.now().add(const Duration(days: 30)), // 1달 후
      ),
      FoodItem(
        id: DateTime.now().toString() + '_3',
        name: '양파',
        quantity: 1,
        unit: '망',
        category: FoodCategory.vegetable,
        storageLocation: StorageLocation.roomTemperature, // 실온
        expiryDate: DateTime.now().add(const Duration(days: 7)), // 1주 후
      ),
    ];
  }
}