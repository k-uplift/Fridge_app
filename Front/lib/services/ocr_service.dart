import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/food_item.dart';

class OcrService {
  static const String requestUrl = "http://119.66.214.56:8000/ocr/receipt"; // OCR 서버 주소

  Future<List<FoodItem>> uploadImageAndGetItems(File imageFile) async { // 서버로 이미지를 전송, 보정된 품목 리스트를 받아오는 함수
    final url = Uri.parse(requestUrl);

    try {
      var request = http.MultipartRequest('POST', url);
    
      request.files.add(await http.MultipartFile.fromPath( // 파일 첨부 (키값: "file")
        'file', 
        imageFile.path,
      ));

      print("OCR 요청 시작: $url");

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        print("인식 성공!");
        final decodedData = jsonDecode(utf8.decode(response.bodyBytes));
        print("받은 데이터: $decodedData");

        // 받은 JSON 데이터를 앱의 FoodItem 리스트로 변환
        // 서버가 주는 구조에 따라 리스트가 바로 오거나, 'items' 키 안에 있을 수 있음
        // 일단 리스트라고 가정하고, 만약 Map이라면 'items' 키를 찾도록 처리
        List<dynamic> listData = [];
        if (decodedData is List) {
          listData = decodedData;
        } else if (decodedData is Map && decodedData.containsKey('items')) {
          listData = decodedData['items'];
        } else {
          
          print("데이터 형식에 차이가 있어요.: $decodedData"); // 형식이 다를 경우 빈 리스트 반환
          return [];
        }
        
        return listData.map((json) => _mapJsonToFoodItem(json)).toList();
      } else {
        print("인식 실패: ${response.statusCode}");
        print("오류: ${response.body}");
        return [];
      }
    } catch (e) {
      print("OCR 서버 통신 오류: $e");
      return [];
    }
  }

  FoodItem _mapJsonToFoodItem(Map<String, dynamic> json) {
    return FoodItem(
      id: DateTime.now().millisecondsSinceEpoch.toString() + (json['name'] ?? ''), // 고유 ID 생성
      name: json['name'] ?? '알 수 없음',
      
      quantity: (json['quantity'] is int || json['quantity'] is double) 
          ? json['quantity'].toInt() 
          : int.tryParse(json['quantity']?.toString() ?? '1') ?? 1,
      
      unit: json['unit'] ?? '개',
      
      category: _parseCategory(json['category']),
      
      storageLocation: _parseStorage(json['storage_location'] ?? json['storage']),
      
      expiryDate: json['expiry_date'] != null 
          ? DateTime.tryParse(json['expiry_date']) ?? DateTime.now().add(const Duration(days: 7))
          : DateTime.now().add(const Duration(days: 7)),
    );
  }

  FoodCategory _parseCategory(String? categoryName) {
    switch (categoryName) {
      case '유제품': return FoodCategory.dairy;
      case '육류': return FoodCategory.meat;
      case '채소': case '야채': return FoodCategory.vegetable;
      case '과일': return FoodCategory.fruit;
      case '냉동': case '냉동식품': return FoodCategory.frozen;
      case '조미료': return FoodCategory.seasoning;
      case '조리': case '반찬': return FoodCategory.cooked;
      default: return FoodCategory.etc;
    }
  }

  StorageLocation _parseStorage(String? storageName) {
    switch (storageName) {
      case '냉동': return StorageLocation.frozen;
      case '실온': return StorageLocation.roomTemperature;
      default: return StorageLocation.refrigerated;
    }
  }
}