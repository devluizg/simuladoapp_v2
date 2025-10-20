import '/utils/string_decoder.dart';

class StudentModel {
  /// Identificador único do aluno.
  final int id;

  /// Nome completo do aluno.
  final String name;

  /// Endereço de e-mail do aluno (pode ser nulo).
  final String? email;

  /// Matrícula ou código de identificação do aluno.
  final dynamic studentId;

  /// Lista de identificadores das turmas às quais o aluno está matriculado.
  final List<int> classes;

  /// Cria uma instância de [StudentModel].
  ///
  /// Os campos id, name e classes são obrigatórios.
  StudentModel({
    required this.id,
    required this.name,
    this.email,
    required this.studentId,
    required this.classes,
  });

  /// Constrói um [StudentModel] a partir de um [Map] JSON.
  ///
  /// Utilizado para desserialização dos dados recebidos da API.
  factory StudentModel.fromJson(Map<String, dynamic> json) {
    return StudentModel(
      id: json['id'],
      name: StringDecoder.decode(json['name']),
      email: json['email'] != null ? StringDecoder.decode(json['email']) : null,
      studentId: json['student_id'],
      classes: List<int>.from(json['classes']),
    );
  }

  /// Converte a instância de [StudentModel] em um [Map] JSON.
  ///
  /// Útil para serializar o objeto antes de enviá-lo para a API.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'student_id': studentId,
      'classes': classes,
    };
  }
}

class StudentListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<StudentModel> results;

  StudentListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory StudentListResponse.fromJson(Map<String, dynamic> json) {
    return StudentListResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => StudentModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
