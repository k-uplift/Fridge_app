import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/food_item.dart'; 

class ApiService {
  // [수정 1] baseUrl은 'IP주소:포트번호'까지만 적습니다. (뒤에 경로 삭제)
  static const String baseUrl = "http://119.66.214.56:8000"; 

  Future<Map<String, dynamic>?> getRecipeRecommendation(List<FoodItem> items) async {
    // [수정 2] 여기서 상세 경로(/recipes/recommend)를 붙여줍니다.
    final url = Uri.parse('$baseUrl/recipes/recommend');

    try {
      List<Map<String, dynamic>> ingredientsList = items.map((item) {
        return {
          "name": item.name,
          "quantity": item.quantity,
          "unit": item.unit,
        };
      }).toList();

      final bodyData = {
        "ingredients": ingredientsList
      };

      print("요청 URL: $url"); // 주소가 맞는지 확인용 로그
      print("보내는 데이터: ${jsonEncode(bodyData)}");

      final response = await http.post(
        url,
        headers: {
          "Content-Type": "application/json",
          "accept": "application/json",
        },
        body: jsonEncode(bodyData),
      );

      if (response.statusCode == 200) {
        print("레시피 추천 성공");
        // 한글 깨짐 방지 디코딩
        final decodedData = jsonDecode(utf8.decode(response.bodyBytes));
        print("📥 받은 데이터: $decodedData");
        return decodedData;
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