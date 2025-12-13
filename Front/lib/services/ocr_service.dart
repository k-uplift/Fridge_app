import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart'; 
import '../models/food_item.dart';

class OcrService {
  static const String requestUrl = "http://119.66.214.56:8000/ocr/receipt"; 

  Future<List<FoodItem>> uploadImageAndGetItems(File imageFile) async {
    final url = Uri.parse(requestUrl);

    try {
      var request = http.MultipartRequest('POST', url);
      
      String extension = imageFile.path.split('.').last.toLowerCase();
      MediaType contentType;
      if (extension == 'png') {
        contentType = MediaType('image', 'png');
      } else {
        contentType = MediaType('image', 'jpeg');
      }

      request.files.add(await http.MultipartFile.fromPath(
        'file', 
        imageFile.path,
        contentType: contentType,
      ));

      print("OCR 요청 시작 (POST): $url");

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        print("OCR 인식 성공!");
        
        final decodedData = jsonDecode(utf8.decode(response.bodyBytes));
        print("받은 데이터: $decodedData");

        List<dynamic> listData = [];
        
        if (decodedData is Map && decodedData.containsKey('data')) {
          listData = decodedData['data'];
        } else if (decodedData is List) {
          listData = decodedData;
        } else if (decodedData is Map && decodedData.containsKey('items')) {
          listData = decodedData['items'];
        } else {
          print("데이터 형식이 예상과 다릅니다: $decodedData");
          return [];
        }
        
        return listData.map((json) => _mapJsonToFoodItem(json)).toList();
      } else {
        print("OCR 실패: ${response.statusCode}");
        print("에러 내용: ${response.body}");
        return [];
      }
    } catch (e) {
      print("OCR 서버 통신 오류: $e");
      return [];
    }
  }

  FoodItem _mapJsonToFoodItem(Map<String, dynamic> json) {
    return FoodItem(
      id: DateTime.now().millisecondsSinceEpoch.toString() + (json['product_name'] ?? json['name'] ?? ''), 
      
      name: json['product_name'] ?? json['name'] ?? '알 수 없음',
      
      quantity: (json['quantity'] is num) 
          ? (json['quantity'] as num).toDouble() 
          : 1.0,
      
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