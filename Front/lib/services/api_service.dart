import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/food_item.dart'; // FoodItem 모델 import

class ApiService {
  static const String baseUrl = "http://119.66.214.56:8000/8000/recipes/recommend"; // 서버 주소 설정

  // 식재료 리스트를 서버로 보내고, 추천된 레시피 결과를 받아옴
  Future<Map<String, dynamic>?> getRecipeRecommendation(List<FoodItem> items) async {
    final url = Uri.parse('$baseUrl/recipes/recommend');

    try {
      List<Map<String, dynamic>> ingredientsList = items.map((item) { // 식재료 데이터를 JSON 모양으로 변환
        return {
          "name": item.name,
          "quantity": item.quantity,
          "unit": item.unit,
        };
      }).toList();

      final bodyData = {
        "ingredients": ingredientsList
      };

      print("서버로 보내는 데이터: ${jsonEncode(bodyData)}");

      final response = await http.post( // POST 요청 보내기
        url,
        headers: {
          "Content-Type": "application/json", // JSON 형식으로 보낸다고 명시
          "accept": "application/json",
        },
        body: jsonEncode(bodyData), // 데이터를 JSON 문자열로 변환하여 전송
      );


      if (response.statusCode == 200) { // 서버 응답 처리
        print("레시피 추천 성공");
        
        final decodedData = jsonDecode(utf8.decode(response.bodyBytes));
        
        print("받은 데이터: $decodedData");
        return decodedData; // 성공 시 데이터 반환
      } else {
        print("레시피 추천 실패: ${response.statusCode}");
        print("에러 내용: ${response.body}");
        return null;
      }
    } catch (e) {
      print("서버 통신 오류 발생: $e");
      return null;
    }
  }
}