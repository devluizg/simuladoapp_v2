import '/utils/string_decoder.dart';

class QuestaoModel {
  final int id;
  final String disciplina;
  final String conteudo;
  final String enunciado;
  final String alternativaA;
  final String alternativaB;
  final String alternativaC;
  final String alternativaD;
  final String alternativaE;
  final String respostaCorreta;
  final String nivelDificuldade;

  QuestaoModel({
    required this.id,
    required this.disciplina,
    required this.conteudo,
    required this.enunciado,
    required this.alternativaA,
    required this.alternativaB,
    required this.alternativaC,
    required this.alternativaD,
    required this.alternativaE,
    required this.respostaCorreta,
    required this.nivelDificuldade,
  });

  factory QuestaoModel.fromJson(Map<String, dynamic> json) {
    return QuestaoModel(
      id: json['id'] as int,
      disciplina: StringDecoder.decode(json['disciplina'] as String),
      conteudo: StringDecoder.decode(json['conteudo'] as String),
      enunciado: StringDecoder.decode(json['enunciado'] as String),
      alternativaA: StringDecoder.decode(json['alternativa_a'] as String),
      alternativaB: StringDecoder.decode(json['alternativa_b'] as String),
      alternativaC: StringDecoder.decode(json['alternativa_c'] as String),
      alternativaD: StringDecoder.decode(json['alternativa_d'] as String),
      alternativaE: StringDecoder.decode(json['alternativa_e'] as String),
      respostaCorreta: json['resposta_correta'] as String,
      nivelDificuldade:
          StringDecoder.decode(json['nivel_dificuldade'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'disciplina': disciplina,
      'conteudo': conteudo,
      'enunciado': enunciado,
      'alternativa_a': alternativaA,
      'alternativa_b': alternativaB,
      'alternativa_c': alternativaC,
      'alternativa_d': alternativaD,
      'alternativa_e': alternativaE,
      'resposta_correta': respostaCorreta,
      'nivel_dificuldade': nivelDificuldade,
    };
  }
}

class QuestaoSimuladoModel {
  final int ordem;
  final QuestaoModel questao;

  QuestaoSimuladoModel({
    required this.ordem,
    required this.questao,
  });

  factory QuestaoSimuladoModel.fromJson(Map<String, dynamic> json) {
    return QuestaoSimuladoModel(
      ordem: json['ordem'] as int,
      questao: QuestaoModel.fromJson(json['questao'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ordem': ordem,
      'questao': questao.toJson(),
    };
  }
}

class SimuladoModel {
  final int id;
  final String titulo;
  final String descricao;
  final String? cabecalho;
  final String? instrucoes;
  final List<QuestaoSimuladoModel> questoes;
  final DateTime dataCriacao;
  final DateTime ultimaModificacao;
  final List<int> classes;
  final DateTime createdAt;
  final DateTime updatedAt;

  SimuladoModel({
    required this.id,
    required this.titulo,
    required this.descricao,
    this.cabecalho,
    this.instrucoes,
    required this.questoes,
    required this.dataCriacao,
    required this.ultimaModificacao,
    required this.classes,
    required this.createdAt,
    required this.updatedAt,
  });

  // Método para decodificar especificamente títulos como "1ªav"
  static String _decodeTitulo(String rawTitle) {
    // Verificar padrão de "número + ª + texto"
    final RegExp regexOrdinal = RegExp(r'(\d+)[A\[].*\s+(av|AV)\s+(.+)');
    final match = regexOrdinal.firstMatch(rawTitle);

    if (match != null) {
      final numero = match.group(1);
      final resto = match.group(3);
      return '$numero${StringDecoder.decode('ª')} av $resto';
    }

    // Se não corresponder ao padrão específico, decodifique normalmente
    return StringDecoder.decode(rawTitle);
  }

  factory SimuladoModel.fromJson(Map<String, dynamic> json) {
    final dataCriacao = DateTime.parse(json['data_criacao'] as String);
    final ultimaModificacao =
        DateTime.parse(json['ultima_modificacao'] as String);

    return SimuladoModel(
      id: json['id'] as int,
      titulo: _decodeTitulo(json['titulo'] as String),
      descricao: StringDecoder.decode(json['descricao'] as String),
      cabecalho: json['cabecalho'] != null
          ? StringDecoder.decode(json['cabecalho'] as String)
          : null,
      instrucoes: json['instrucoes'] != null
          ? StringDecoder.decode(json['instrucoes'] as String)
          : null,
      questoes: (json['questoes'] as List<dynamic>)
          .map((q) => QuestaoSimuladoModel.fromJson(q as Map<String, dynamic>))
          .toList(),
      dataCriacao: dataCriacao,
      ultimaModificacao: ultimaModificacao,
      classes: List<int>.from(json['classes']),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : dataCriacao,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : ultimaModificacao,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'titulo': titulo,
      'descricao': descricao,
      'cabecalho': cabecalho,
      'instrucoes': instrucoes,
      'questoes': questoes.map((q) => q.toJson()).toList(),
      'data_criacao': dataCriacao.toIso8601String(),
      'ultima_modificacao': ultimaModificacao.toIso8601String(),
      'classes': classes,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class SimuladoListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<SimuladoModel> results;

  SimuladoListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory SimuladoListResponse.fromJson(Map<String, dynamic> json) {
    return SimuladoListResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => SimuladoModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
