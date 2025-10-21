import '/utils/string_decoder.dart';

class DetalhesRespostaModel {
  final String ordem;
  final int questaoId;
  final String disciplina;
  final String respostaAluno;
  final String respostaCorreta;
  final bool acertou;

  DetalhesRespostaModel({
    required this.ordem,
    required this.questaoId,
    required this.disciplina,
    required this.respostaAluno,
    required this.respostaCorreta,
    required this.acertou,
  });

  factory DetalhesRespostaModel.fromJson(Map<String, dynamic> json) {
    return DetalhesRespostaModel(
      ordem: json['ordem'].toString(),
      questaoId: json['questao_id'],
      disciplina: StringDecoder.decode(json['disciplina']),
      respostaAluno: json['resposta_aluno'],
      respostaCorreta: json['resposta_correta'],
      acertou: json['acertou'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ordem': ordem,
      'questao_id': questaoId,
      'disciplina': disciplina,
      'resposta_aluno': respostaAluno,
      'resposta_correta': respostaCorreta,
      'acertou': acertou,
    };
  }
}

class ResultadoModel {
  final int id;
  final String aluno;
  final String simulado;
  final double pontuacao;
  final int acertos;
  final int totalQuestoes;
  final DateTime dataCorrecao;
  final List<DetalhesRespostaModel> detalhes;

  ResultadoModel({
    required this.id,
    required this.aluno,
    required this.simulado,
    required this.pontuacao,
    required this.acertos,
    required this.totalQuestoes,
    required this.dataCorrecao,
    required this.detalhes,
  });

  factory ResultadoModel.fromJson(Map<String, dynamic> json) {
    var detalhesResultado = <DetalhesRespostaModel>[];
    if (json['detalhes'] != null) {
      detalhesResultado = List<DetalhesRespostaModel>.from(
        json['detalhes'].map((d) => DetalhesRespostaModel.fromJson(d)),
      );
    }

    return ResultadoModel(
      id: json['id'],
      aluno: StringDecoder.decode(json['aluno']),
      simulado: StringDecoder.decode(json['simulado']),
      pontuacao: json['pontuacao'].toDouble(),
      acertos: json['acertos'],
      totalQuestoes: json['total_questoes'],
      dataCorrecao: DateTime.parse(json['data_correcao']),
      detalhes: detalhesResultado,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'aluno': aluno,
      'simulado': simulado,
      'pontuacao': pontuacao,
      'acertos': acertos,
      'total_questoes': totalQuestoes,
      'data_correcao': dataCorrecao.toIso8601String(),
      'detalhes': detalhes.map((d) => d.toJson()).toList(),
    };
  }
}

class ResultadoListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<ResultadoModel> results;

  ResultadoListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory ResultadoListResponse.fromJson(Map<String, dynamic> json) {
    return ResultadoListResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => ResultadoModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class DashboardDisciplinaModel {
  final String disciplina;
  final int totalQuestoes;
  final int acertos;
  final double taxaAcerto;

  DashboardDisciplinaModel({
    required this.disciplina,
    required this.totalQuestoes,
    required this.acertos,
    required this.taxaAcerto,
  });

  factory DashboardDisciplinaModel.fromJson(Map<String, dynamic> json) {
    return DashboardDisciplinaModel(
      disciplina: json['disciplina'],
      totalQuestoes: json['total_questoes'],
      acertos: json['acertos'],
      taxaAcerto: json['taxa_acerto'].toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'disciplina': disciplina,
      'total_questoes': totalQuestoes,
      'acertos': acertos,
      'taxa_acerto': taxaAcerto,
    };
  }
}

class DashboardAlunoModel {
  final String aluno;
  final int totalSimulados;
  final double mediaGeral;
  final List<DashboardDisciplinaModel> desempenhoDisciplinas;
  final List<Map<String, dynamic>> evolucaoTimeline;

  DashboardAlunoModel({
    required this.aluno,
    required this.totalSimulados,
    required this.mediaGeral,
    required this.desempenhoDisciplinas,
    required this.evolucaoTimeline,
  });

  factory DashboardAlunoModel.fromJson(Map<String, dynamic> json) {
    var disciplinas = <DashboardDisciplinaModel>[];
    if (json['desempenho_disciplinas'] != null) {
      disciplinas = List<DashboardDisciplinaModel>.from(
        json['desempenho_disciplinas']
            .map((d) => DashboardDisciplinaModel.fromJson(d)),
      );
    }

    return DashboardAlunoModel(
      aluno: json['aluno'],
      totalSimulados: json['total_simulados'],
      mediaGeral: json['media_geral'].toDouble(),
      desempenhoDisciplinas: disciplinas,
      evolucaoTimeline:
          List<Map<String, dynamic>>.from(json['evolucao_timeline']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'aluno': aluno,
      'total_simulados': totalSimulados,
      'media_geral': mediaGeral,
      'desempenho_disciplinas':
          desempenhoDisciplinas.map((d) => d.toJson()).toList(),
      'evolucao_timeline': evolucaoTimeline,
    };
  }
}
