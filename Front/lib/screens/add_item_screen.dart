import 'dart:math'; 
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/food_item.dart';

class AddItemScreen extends StatefulWidget {
  final FoodItem? existingItem;

  const AddItemScreen({super.key, this.existingItem});

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();

  late String _name;
  int? _quantity;
  String? _unit;
  
  FoodCategory? _selectedCategory;
  StorageLocation? _selectedStorage;
  
  DateTime? _expiryDate; 

  String? _expiryDurationStr;
  String? _expiryUnit;

  late TextEditingController _nameController;
  late TextEditingController _quantityController;
  late TextEditingController _expiryDurationController;

  late AnimationController _shakeController;
  
  final Map<String, bool> _errorMap = {};

  final TextStyle _commonTextStyle = const TextStyle(
    fontSize: 13,
    color: Colors.black87,
    fontWeight: FontWeight.normal,
  );
  
  final TextStyle _commonHintStyle = TextStyle(
    fontSize: 13,
    color: Colors.grey[500],
    fontWeight: FontWeight.normal,
  );

  @override
  void initState() {
    super.initState();
    
    _shakeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );

    _nameController = TextEditingController();
    _quantityController = TextEditingController();
    _expiryDurationController = TextEditingController();
    
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
      _expiryUnit = '일';

      _nameController.text = _name;
      _quantityController.text = _quantity.toString();
      _expiryDurationController.text = _expiryDurationStr!;
    } else {
      _name = '';
      _expiryDate = null;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _expiryDurationController.dispose();
    _shakeController.dispose();
    super.dispose();
  }

  List<FoodCategory> get _sortedCategories {
    final categories = FoodCategory.values.toList();
    categories.sort((a, b) {
      if (a == FoodCategory.etc) return 1;
      if (b == FoodCategory.etc) return -1;
      return _getCategoryKoreanName(a).compareTo(_getCategoryKoreanName(b));
    });
    return categories;
  }

  void _calculateExpiryDate() {
    if (_expiryDurationController.text.isEmpty || _expiryUnit == null) {
      _expiryDate = null;
      if (mounted) setState(() {});
      return;
    }

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

  void _clearError(String key) {
    if (_errorMap[key] == true) {
      setState(() {
        _errorMap[key] = false;
      });
    }
  }

  void _submitForm() {
    setState(() {
      _errorMap.clear(); 

      if (_nameController.text.isEmpty) _errorMap['name'] = true;
      if (_quantityController.text.isEmpty) _errorMap['quantity'] = true;
      if (_unit == null) _errorMap['unit'] = true;
      if (_selectedCategory == null) _errorMap['category'] = true;
      if (_selectedStorage == null) _errorMap['storage'] = true;
      if (_expiryDurationController.text.isEmpty) _errorMap['expiryDuration'] = true;
      if (_expiryUnit == null) _errorMap['expiryUnit'] = true;
    });

    if (_errorMap.isNotEmpty) {
      _shakeController.forward(from: 0); 
      return;
    }

    _name = _nameController.text;
    _quantity = int.parse(_quantityController.text);
    _calculateExpiryDate();

    final newItem = FoodItem(
      id: widget.existingItem?.id ?? DateTime.now().toString(),
      name: _name,
      quantity: _quantity!.toDouble(),
      unit: _unit!,
      category: _selectedCategory!,
      storageLocation: _selectedStorage!,
      expiryDate: _expiryDate!,
    );
    
    Navigator.of(context).pop(newItem); 
  }

  InputDecoration _inputDecoration(String hint, {String? errorText}) {
    return InputDecoration(
      hintText: hint,
      hintStyle: _commonHintStyle,
      filled: true,
      fillColor: Colors.grey[100],
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      
      errorText: errorText, 
      errorStyle: const TextStyle(color: Colors.red, fontSize: 12, height: 1.0),
      
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
      
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Colors.red, width: 1.5),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Colors.red, width: 1.5),
      ),
    );
  }

  Widget _buildShakeableField(String key, Widget child) {
    return AnimatedBuilder(
      animation: _shakeController,
      builder: (context, child) {
        final double offset = (_errorMap[key] == true) 
            ? sin(_shakeController.value * pi * 4) * 6 
            : 0.0;
        return Transform.translate(
          offset: Offset(offset, 0),
          child: child,
        );
      },
      child: child,
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
      
      title: const Center(
        child: Text(
          '음식 등록하기',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
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
                _buildShakeableField('name', 
                  TextFormField(
                    controller: _nameController,
                    style: _commonTextStyle,
                    onTap: () => _clearError('name'),
                    onChanged: (val) => _clearError('name'),
                    decoration: _inputDecoration(
                      '음식 이름을 입력하세요.', 
                      errorText: _errorMap['name'] == true ? '음식 이름을 입력하세요.' : null
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                _buildLabel('수량'),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start, 
                  children: [
                    Expanded(
                      flex: 2,
                      child: _buildShakeableField('quantity', 
                        TextFormField(
                          controller: _quantityController,
                          style: _commonTextStyle,
                          keyboardType: TextInputType.number,
                          onTap: () => _clearError('quantity'),
                          onChanged: (val) => _clearError('quantity'),
                          decoration: _inputDecoration(
                            '수량을 입력하세요.',
                            errorText: _errorMap['quantity'] == true ? '수량을 입력하세요.' : null
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 1,
                      child: _buildShakeableField('unit',
                        DropdownButtonFormField<String>(
                          value: _unit,
                          dropdownColor: Colors.white,
                          onTap: () => _clearError('unit'),
                          onChanged: (v) {
                            setState(() => _unit = v!);
                            _clearError('unit');
                          },
                          decoration: _inputDecoration(
                            '', 
                            errorText: _errorMap['unit'] == true ? '선택' : null
                          ),
                          hint: Text('선택', style: _commonHintStyle),
                          isExpanded: true,
                          isDense: true,  
                          items: ['개', 'g', 'kg', 'ml', 'L', '봉지', '캔', '병'].map((v) => DropdownMenuItem(
                            value: v, 
                            child: Text(v, style: _commonTextStyle)
                          )).toList(),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                _buildLabel('분류'),
                _buildShakeableField('category',
                  DropdownButtonFormField<FoodCategory>(
                    dropdownColor: Colors.white,
                    value: _selectedCategory,
                    onTap: () => _clearError('category'),
                    onChanged: (v) {
                      setState(() {
                        _selectedCategory = v!;
                      });
                      _clearError('category');
                    },
                    decoration: _inputDecoration(
                      '',
                      errorText: _errorMap['category'] == true ? '분류를 선택하세요.' : null
                    ),
                    hint: Text('분류를 선택하세요.', style: _commonHintStyle),
                    isExpanded: true,
                    isDense: true,  
                    items: _sortedCategories.map((category) {
                      return DropdownMenuItem(
                        value: category,
                        child: Text(_getCategoryKoreanName(category), style: _commonTextStyle),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 16),

                _buildLabel('보관 방법'),
                _buildShakeableField('storage',
                  DropdownButtonFormField<StorageLocation>(
                    dropdownColor: Colors.white,
                    value: _selectedStorage,
                    onTap: () => _clearError('storage'),
                    onChanged: (v) {
                      setState(() => _selectedStorage = v!);
                      _clearError('storage');
                    },
                    decoration: _inputDecoration(
                      '',
                      errorText: _errorMap['storage'] == true ? '보관 방법을 선택하세요.' : null
                    ),
                    hint: Text('보관 방법을 선택하세요.', style: _commonHintStyle),
                    isExpanded: true,
                    isDense: true,
                    items: StorageLocation.values.map((location) {
                      return DropdownMenuItem(
                        value: location,
                        child: Text(_getStorageKoreanName(location), style: _commonTextStyle),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 16),

                _buildLabel('유통기한'),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      flex: 2,
                      child: _buildShakeableField('expiryDuration', 
                        TextFormField(
                          controller: _expiryDurationController,
                          keyboardType: TextInputType.number,
                          style: _commonTextStyle,
                          onTap: () => _clearError('expiryDuration'),
                          onChanged: (val) {
                            _calculateExpiryDate();
                            _clearError('expiryDuration');
                          },
                          decoration: _inputDecoration(
                            '유통기한을 입력하세요.',
                            errorText: _errorMap['expiryDuration'] == true ? '유통기한을 입력하세요.' : null
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 1,
                      child: _buildShakeableField('expiryUnit',
                        DropdownButtonFormField<String>(
                          dropdownColor: Colors.white,
                          value: _expiryUnit,
                          onTap: () => _clearError('expiryUnit'),
                          onChanged: (v) {
                            if (v != null) {
                              setState(() { _expiryUnit = v; });
                              _calculateExpiryDate();
                              _clearError('expiryUnit');
                            }
                          },
                          decoration: _inputDecoration(
                            '',
                            errorText: _errorMap['expiryUnit'] == true ? '선택' : null
                          ),
                          hint: Text('선택', style: _commonHintStyle),
                          isExpanded: true,
                          isDense: true,
                          items: ['일', '주', '개월', '년'].map((v) => DropdownMenuItem(
                            value: v, 
                            child: Text(v, style: _commonTextStyle)
                          )).toList(),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: _expiryDate == null 
                    ? const SizedBox.shrink()
                    : Text(
                        '유통기한: ${DateFormat('yyyy년 MM월 dd일').format(_expiryDate!)}',
                        style: const TextStyle(color: Colors.green, fontSize: 13, fontWeight: FontWeight.bold),
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