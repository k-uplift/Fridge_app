import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/food_item.dart';

class AddItemScreen extends StatefulWidget {
  final FoodItem? existingItem;

  const AddItemScreen({super.key, this.existingItem});

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();
  
  late String _name;
  int _quantity = 1;
  String _unit = '개';
  
  FoodCategory? _selectedCategory;
  StorageLocation? _selectedStorage;
  
  late DateTime _expiryDate; 

  String _expiryDurationStr = '7'; 
  String _expiryUnit = '일';       

  late TextEditingController _nameController;
  late TextEditingController _quantityController;
  late TextEditingController _expiryDurationController;

  @override
  void initState() {
    super.initState();
    
    if (widget.existingItem != null) {
      final item = widget.existingItem!;
      _name = item.name;
      _quantity = item.quantity.toInt();
      _unit = item.unit;
      _selectedCategory = item.category;
      _selectedStorage = item.storageLocation;
      _expiryDate = item.expiryDate;

      final remainingDays = item.expiryDate.difference(DateTime.now()).inDays;
      _expiryDurationStr = remainingDays > 0 ? remainingDays.toString() : '0';
    } else {
      _name = '';
      _expiryDate = DateTime.now().add(const Duration(days: 7)); 
      _expiryDurationStr = '7';
    }

    _nameController = TextEditingController(text: _name);
    _quantityController = TextEditingController(text: _quantity.toString());
    _expiryDurationController = TextEditingController(text: _expiryDurationStr);

    _calculateExpiryDate();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _expiryDurationController.dispose();
    super.dispose();
  }

  List<FoodCategory> get _sortedCategories {   // 카테고리 정렬(가나다순, 기타는 맨 뒤)
    final categories = FoodCategory.values.toList();
    categories.sort((a, b) {
      if (a == FoodCategory.etc) return 1;
      if (b == FoodCategory.etc) return -1;
      
      return _getCategoryKoreanName(a).compareTo(_getCategoryKoreanName(b));
    });
    return categories;
  }

  void _calculateExpiryDate() {
    final int duration = int.tryParse(_expiryDurationController.text) ?? 0;
    final DateTime now = DateTime.now();
    DateTime newDate = now;

    switch (_expiryUnit) {
      case '일': newDate = now.add(Duration(days: duration)); break;
      case '주': newDate = now.add(Duration(days: duration * 7)); break;
      case '개월': newDate = DateTime(now.year, now.month + duration, now.day); break;
      case '년': newDate = DateTime(now.year + duration, now.month, now.day); break;
    }

    _expiryDate = newDate; 
    if (mounted) setState(() {});
  }

  void _updateExpiryDefaultsByCategory(FoodCategory category) {
    if (widget.existingItem != null) return; 

    String newDuration = '7';
    String newUnit = '일';

    if (category == FoodCategory.cooked) {
      newDuration = '3';
      newUnit = '일';
    } else if (category == FoodCategory.frozen) {
      newDuration = '1';
      newUnit = '개월';
    }

    _expiryDurationController.text = newDuration;
    _expiryUnit = newUnit;
    _calculateExpiryDate(); 
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();
      _calculateExpiryDate(); 

      final newItem = FoodItem(
        id: widget.existingItem?.id ?? DateTime.now().toString(),
        name: _name,
        quantity: _quantity.toDouble(),
        unit: _unit,
        category: _selectedCategory!,
        storageLocation: _selectedStorage!,
        expiryDate: _expiryDate,
      );
      
      Navigator.of(context).pop(newItem); 
    }
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      filled: true,
      fillColor: Colors.grey[100],
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6.0, top: 4.0),
      child: Text(text, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
    );
  }

  String _getCategoryKoreanName(FoodCategory category) {
    switch (category) {
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

  String _getStorageKoreanName(StorageLocation location) {
    switch (location) {
      case StorageLocation.refrigerated: return '냉장';
      case StorageLocation.frozen: return '냉동';
      case StorageLocation.roomTemperature: return '상온';
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      contentPadding: const EdgeInsets.all(24),
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      title: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, size: 24),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
            onPressed: () => Navigator.pop(context),
          ),
          const Expanded(
            child: Center(
              child: Text(
                '음식 등록하기',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 24),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
      
      content: SizedBox(
        width: MediaQuery.of(context).size.width,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Center(
                  child: Text(
                    '음식 정보를 입력해주세요.',
                    style: TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),
                const SizedBox(height: 20),

                _buildLabel('음식 이름'),
                TextFormField(
                  controller: _nameController,
                  decoration: _inputDecoration('예: 우유, 계란, 토마토'),
                  validator: (value) => (value == null || value.isEmpty) ? '입력 필요' : null,
                  onSaved: (value) => _name = value!,
                ),
                const SizedBox(height: 16),

                _buildLabel('수량'),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextFormField(
                        controller: _quantityController,
                        decoration: _inputDecoration('수량 입력'),
                        keyboardType: TextInputType.number,
                        validator: (value) => (value == null || value.isEmpty) ? '입력 필요' : null,
                        onSaved: (value) => _quantity = double.parse(value!).toInt(),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 1,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _unit,
                            dropdownColor: Colors.white,
                            isExpanded: true,
                            items: ['개', 'g', 'kg', 'ml', 'L', '봉지', '캔', '병'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
                            onChanged: (v) => setState(() => _unit = v!),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                _buildLabel('분류'),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<FoodCategory>(
                      dropdownColor: Colors.white,
                      hint: const Text('분류를 선택하세요', style: TextStyle(color: Colors.grey)),
                      value: _selectedCategory,
                      isExpanded: true,
                      items: _sortedCategories.map((category) {
                        return DropdownMenuItem(
                          value: category,
                          child: Text(_getCategoryKoreanName(category)),
                        );
                      }).toList(),
                      onChanged: (v) {
                        setState(() {
                          _selectedCategory = v!;
                          _updateExpiryDefaultsByCategory(v);
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                _buildLabel('보관 방법'),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<StorageLocation>(
                      dropdownColor: Colors.white,
                      hint: const Text('보관 방법을 선택하세요', style: TextStyle(color: Colors.grey)),
                      value: _selectedStorage,
                      isExpanded: true,
                      items: StorageLocation.values.map((location) {
                        return DropdownMenuItem(
                          value: location,
                          child: Text(_getStorageKoreanName(location)),
                        );
                      }).toList(),
                      onChanged: (v) => setState(() => _selectedStorage = v!),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                _buildLabel('유통기한'),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextFormField(
                        controller: _expiryDurationController,
                        keyboardType: TextInputType.number,
                        decoration: _inputDecoration('기간 입력'),
                        onChanged: (val) => _calculateExpiryDate(),
                        validator: (value) => (value == null || value.isEmpty) ? '입력 필요' : null,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 1,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            dropdownColor: Colors.white,
                            value: _expiryUnit,
                            isExpanded: true,
                            items: ['일', '주', '개월', '년'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
                            onChanged: (v) {
                              if (v != null) {
                                setState(() { _expiryUnit = v; });
                                _calculateExpiryDate();
                              }
                            },
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: Text(
                    '예상 만료일: ${DateFormat('yyyy년 MM월 dd일').format(_expiryDate)}',
                    style: TextStyle(color: Colors.green, fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),

      actionsPadding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
      actions: [
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => Navigator.pop(context),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  side: const BorderSide(color: Colors.grey),
                ),
                child: const Text('취소', style: TextStyle(color: Colors.black)),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: _submitForm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0F172A),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: const Text('등록', style: TextStyle(color: Colors.white)),
              ),
            ),
          ],
        ),
      ],
    );
  }
}