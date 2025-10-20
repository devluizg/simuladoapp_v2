import '/utils/string_decoder.dart';

class ClassModel {
  final int id;
  final String name;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;

  ClassModel({
    required this.id,
    required this.name,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ClassModel.fromJson(Map<String, dynamic> json) {
    return ClassModel(
      id: json['id'] as int,
      name: StringDecoder.decode(json['name'] as String),
      description: StringDecoder.decode(json['description'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class ClassListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<ClassModel> results;

  ClassListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory ClassListResponse.fromJson(Map<String, dynamic> json) {
    return ClassListResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => ClassModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
