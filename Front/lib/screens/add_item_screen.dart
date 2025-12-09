import 'package:flutter/material.dart';
import '../models/food_item.dart';
import 'package:intl/intl.dart';

class AddItemScreen extends StatefulWidget {
  final FoodItem? existingItem;

  const AddItemScreen({
    super.key,
    this.existingItem,
  });

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();

  String _name = '';
  double? _quantity;
  String _unit = '개';
  FoodCategory? _selectedCategory;
  StorageLocation? _selectedStorage;
  DateTime _expiryDate = DateTime.now().add(const Duration(days: 7));
  bool get _isEditing => widget.existingItem != null;

  @override
  void initState() {
    super.initState();
    if (_isEditing) {
      final item = widget.existingItem!;
      _name = item.name;
      _quantity = item.quantity;
      _unit = item.unit;
      _selectedCategory = item.category;
      _selectedStorage = item.storageLocation;
      _expiryDate = item.expiryDate;
    }
  }

  void _updateExpiryDateByCategory(FoodCategory? category) {
    if (category == null || _isEditing) return;

    DateTime newDate;
    if (category == FoodCategory.cooked) {
      newDate = DateTime.now().add(const Duration(days: 3)); // 조리된 음식은 기본 3일
    } else if (category == FoodCategory.frozen) { 
      newDate = DateTime.now().add(const Duration(days: 30)); // 냉동식품은 기본 30일
    } else {
      newDate = DateTime.now().add(const Duration(days: 7)); // 그 외 기본 7일
    }

    setState(() {
      _expiryDate = newDate;
    });
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

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _expiryDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null && picked != _expiryDate) {
      setState(() {
        _expiryDate = picked;
      });
    }
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();

      FoodItem resultItem;

      if (_isEditing) {
        resultItem = widget.existingItem!.copyWith(
          name: _name,
          quantity: _quantity,
          unit: _unit,
          category: _selectedCategory,
          storageLocation: _selectedStorage,
          expiryDate: _expiryDate,
        );
      } else {
        resultItem = FoodItem(
          id: DateTime.now().toString(),
          name: _name,
          quantity: _quantity!,
          unit: _unit,
          category: _selectedCategory!,
          storageLocation: _selectedStorage!,
          expiryDate: _expiryDate,
        );
      }
      Navigator.pop(context, resultItem);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? '음식 수정하기' : '음식 등록하기'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                initialValue: _name,
                decoration: const InputDecoration(labelText: '음식 이름'),
                validator: (value) =>
                    (value == null || value.isEmpty) ? '음식 이름을 입력하세요.' : null,
                onSaved: (value) => _name = value!,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<FoodCategory>(
                decoration: const InputDecoration(labelText: '분류'),
                value: _selectedCategory,
                items: FoodCategory.values.map((category) {
                  return DropdownMenuItem(
                    value: category,
                    child: Text(_getCategoryKoreanName(category)),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _selectedCategory = value;
                    _updateExpiryDateByCategory(value);
                  });
                },
                validator: (value) => value == null ? '분류를 선택하세요.' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<StorageLocation>(
                decoration: const InputDecoration(labelText: '보관 방법'),
                value: _selectedStorage,
                items: StorageLocation.values.map((location) {
                  return DropdownMenuItem(
                    value: location,
                    child: Text(_getStorageKoreanName(location)),
                  );
                }).toList(),
                onChanged: (value) => setState(() => _selectedStorage = value),
                validator: (value) => value == null ? '보관 방법을 선택하세요.' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                decoration: const InputDecoration(labelText: '수량'),
                initialValue: (_quantity == null)
                    ? ''
                    : ((_quantity! % 1 == 0)
                        ? _quantity!.toInt().toString()
                        : _quantity!.toString()),
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) return '수량을 입력하세요.';
                  if (double.tryParse(value) == null || double.parse(value) <= 0) {
                    return '식재료 수량을 입력하세요.';
                  }
                  return null;
                },
                onSaved: (value) => _quantity = double.parse(value!),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('유통기한: ${DateFormat('yyyy.MM.dd').format(_expiryDate)}'),
                  TextButton(
                    onPressed: () => _selectDate(context),
                    child: const Text('날짜 선택'),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.white),
                    child: const Text('취소'),
                  ),
                  ElevatedButton(
                    onPressed: _submitForm,
                    child: Text(_isEditing ? '수정' : '등록'),
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