import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ResultadoScreen extends StatefulWidget {
  final String nomeAluno;
  final double notaFinal;
  final Map<String, String> respostasAluno;
  final Map<String, String> gabarito;
  final int tipoProva;
  final double pontuacaoTotal;

  // Adicionando os campos necessários para enviar para o site
  final int? alunoId;
  final int? simuladoId;
  final int? turmaId;
  final String? nomeTurma;
  final String? nomeSimulado;

  const ResultadoScreen({
    super.key,
    required this.nomeAluno,
    required this.notaFinal,
    required this.respostasAluno,
    required this.gabarito,
    this.tipoProva = 1,
    this.pontuacaoTotal = 10.0,
    this.alunoId,
    this.simuladoId,
    this.turmaId,
    this.nomeTurma,
    this.nomeSimulado,
  });

  @override
  State<ResultadoScreen> createState() => _ResultadoScreenState();
}

class _ResultadoScreenState extends State<ResultadoScreen> {
  bool _isSubmitting = false;
  bool _hasSubmitted = false;
  String _submissionMessage = '';

  // Paleta de cores baseada no site
  static const Color primaryColor = Color(0xFF00A4D9); // Ciano vibrante
  static const Color secondaryColor = Color(0xFF434891); // Índigo profundo
  static const Color bgDark = Color(0xFF121425); // Fundo ultra escuro
  static const Color bgSurface = Color(0xFF1D203A); // Superfícies
  static const Color borderColor = Color(0xFF31355B); // Bordas
  static const Color textLight = Color(0xFFE0E6F1); // Texto claro
  static const Color textMuted = Color(0xFF8C96C3); // Texto secundário
  static const Color successColor = Color(0xFF2DD8A3); // Verde de sucesso
  static const Color dangerColor = Color(0xFFE94B6A); // Vermelho de erro

  @override
  void initState() {
    super.initState();
    // Enviar resultados automaticamente após a tela carregar
    _autoSubmitResults();
  }

  // Novo método para envio automático
  Future<void> _autoSubmitResults() async {
    // Aguardar um pouco para a tela carregar completamente
    await Future.delayed(const Duration(milliseconds: 500));

    // Verificar se temos os dados necessários e ainda não enviou
    if (widget.alunoId != null && widget.simuladoId != null && !_hasSubmitted) {
      await _submitResultsToWebsite();
    }
  }

  @override
  Widget build(BuildContext context) {
    // Calcular o percentual de acerto
    final int totalQuestoes = widget.gabarito.length;
    final int questoesAcertadas = widget.gabarito.keys
        .where(
          (questao) =>
              widget.respostasAluno[questao] == widget.gabarito[questao],
        )
        .length;
    final double percentualAcerto =
        totalQuestoes > 0 ? (questoesAcertadas / totalQuestoes) * 100 : 0;

    return Scaffold(
      backgroundColor: bgDark,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: bgSurface,
        foregroundColor: textLight,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [primaryColor, secondaryColor],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.assessment,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'Resultado do Aluno',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 20,
                color: textLight,
              ),
            ),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            height: 1,
            color: borderColor,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Área de scroll contínuo
            Expanded(
              child: CustomScrollView(
                slivers: [
                  // Header com informações do aluno
                  SliverToBoxAdapter(
                    child: Container(
                      padding: const EdgeInsets.all(16.0),
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [secondaryColor, primaryColor],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: borderColor, width: 1),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.4),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                      color: Colors.white.withOpacity(0.3),
                                      width: 1,
                                    ),
                                  ),
                                  child: const Icon(
                                    Icons.person_outline,
                                    color: textLight,
                                    size: 24,
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'Aluno:',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 14,
                                        ),
                                      ),
                                      Text(
                                        widget.nomeAluno,
                                        style: const TextStyle(
                                          color: textLight,
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                                if (_hasSubmitted)
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: successColor.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(4),
                                      border: Border.all(
                                          color: successColor.withOpacity(0.5)),
                                    ),
                                    child: const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.check,
                                            size: 16, color: textLight),
                                        SizedBox(width: 4),
                                        Text(
                                          'Enviado',
                                          style: TextStyle(
                                            color: textLight,
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      if (widget.nomeTurma != null)
                                        Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'Turma:',
                                              style: TextStyle(
                                                color: Colors.white,
                                                fontSize: 12,
                                              ),
                                            ),
                                            Text(
                                              widget.nomeTurma!,
                                              style: const TextStyle(
                                                color: textLight,
                                                fontSize: 14,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        ),
                                      if (widget.nomeSimulado != null) ...[
                                        const SizedBox(height: 8),
                                        Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'Simulado:',
                                              style: TextStyle(
                                                color: Colors.white,
                                                fontSize: 12,
                                              ),
                                            ),
                                            Text(
                                              widget.nomeSimulado!,
                                              style: const TextStyle(
                                                color: textLight,
                                                fontSize: 14,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    const Text(
                                      'Versão da Prova:',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 12,
                                      ),
                                    ),
                                    Text(
                                      '${widget.tipoProva}',
                                      style: const TextStyle(
                                        color: textLight,
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // Card com resultados
                  SliverToBoxAdapter(
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 16.0),
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: bgSurface.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: borderColor, width: 1),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.3),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [primaryColor, secondaryColor],
                                  ),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Icon(
                                  Icons.assessment_outlined,
                                  color: Colors.white,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 12),
                              const Text(
                                'Resultados',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: primaryColor,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: Column(
                                  children: [
                                    const Text(
                                      'Nota Final',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: textMuted,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '${widget.notaFinal.toStringAsFixed(1)}/${widget.pontuacaoTotal}',
                                      style: TextStyle(
                                        fontSize: 20,
                                        fontWeight: FontWeight.bold,
                                        color: widget.notaFinal >=
                                                (widget.pontuacaoTotal / 2)
                                            ? successColor
                                            : dangerColor,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                width: 1,
                                height: 40,
                                color: borderColor,
                              ),
                              Expanded(
                                child: Column(
                                  children: [
                                    const Text(
                                      'Acertos',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: textMuted,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '$questoesAcertadas/$totalQuestoes',
                                      style: TextStyle(
                                        fontSize: 20,
                                        fontWeight: FontWeight.bold,
                                        color: percentualAcerto >= 60
                                            ? successColor
                                            : dangerColor,
                                      ),
                                    ),
                                    Text(
                                      '(${percentualAcerto.toStringAsFixed(1)}%)',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: textMuted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Mensagem de submissão
                  if (_submissionMessage.isNotEmpty)
                    SliverToBoxAdapter(
                      child: Container(
                        margin: const EdgeInsets.symmetric(
                            horizontal: 16.0, vertical: 8.0),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: _hasSubmitted
                              ? successColor.withOpacity(0.1)
                              : dangerColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: _hasSubmitted ? successColor : dangerColor,
                            width: 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              _hasSubmitted ? Icons.check_circle : Icons.error,
                              color: _hasSubmitted ? successColor : dangerColor,
                              size: 16,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _submissionMessage,
                                style: TextStyle(
                                  color: _hasSubmitted
                                      ? successColor
                                      : dangerColor,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                  // Indicador de envio automático
                  if (_isSubmitting)
                    SliverToBoxAdapter(
                      child: Container(
                        margin: const EdgeInsets.symmetric(
                            horizontal: 16.0, vertical: 8.0),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: primaryColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border:
                              Border.all(color: primaryColor.withOpacity(0.3)),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: primaryColor,
                              ),
                            ),
                            SizedBox(width: 16),
                            Text(
                              'Enviando resultados automaticamente...',
                              style: TextStyle(
                                color: primaryColor,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                  // Título da seção de detalhamento
                  SliverToBoxAdapter(
                    child: Container(
                      margin: const EdgeInsets.only(
                          left: 16.0, right: 16.0, top: 24.0, bottom: 16.0),
                      child: const Row(
                        children: [
                          Icon(
                            Icons.list_alt_outlined,
                            color: primaryColor,
                            size: 20,
                          ),
                          SizedBox(width: 8),
                          Text(
                            'Detalhamento por questão:',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: primaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Lista de questões
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final numeroQuestao = (index + 1).toString();
                        final respostaCorreta =
                            widget.gabarito[numeroQuestao] ?? '-';
                        final respostaAlunoRaw =
                            widget.respostasAluno[numeroQuestao] ?? 'N/A';

                        // Determinar o texto a ser exibido e se a resposta é válida
                        String respostaAlunoDisplay;
                        final bool isRespostaValida =
                            respostaAlunoRaw.length == 1 &&
                                'ABCDE'.contains(respostaAlunoRaw);

                        if (isRespostaValida) {
                          respostaAlunoDisplay = respostaAlunoRaw;
                        } else if (respostaAlunoRaw == 'N/A' ||
                            respostaAlunoRaw.toLowerCase().contains('não')) {
                          respostaAlunoDisplay = '-'; // Resposta em branco
                        } else {
                          respostaAlunoDisplay =
                              '*'; // Múltipla ou inválida
                        }

                        final bool acertou =
                            isRespostaValida && respostaAlunoRaw == respostaCorreta;

                        // Calcular valor da questão com base na pontuação total
                        final double valorQuestao =
                            widget.pontuacaoTotal / widget.gabarito.length;

                        return Container(
                          margin: const EdgeInsets.only(
                            left: 16.0,
                            right: 16.0,
                            bottom: 8.0,
                          ),
                          decoration: BoxDecoration(
                            color: bgSurface.withOpacity(0.5),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: borderColor, width: 1),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.3),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 8),
                            leading: Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                color: acertou ? successColor : dangerColor,
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  numeroQuestao,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    color: textLight,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                            title: Row(
                              children: [
                                const Text(
                                  'Sua resposta: ',
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: textMuted,
                                  ),
                                ),
                                Text(
                                  respostaAlunoDisplay,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: acertou ? successColor : dangerColor,
                                  ),
                                ),
                              ],
                            ),
                            subtitle: Row(
                              children: [
                                const Text(
                                  'Correta: ',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: textMuted,
                                  ),
                                ),
                                Text(
                                  respostaCorreta,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: textLight,
                                  ),
                                ),
                              ],
                            ),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: acertou
                                        ? successColor.withOpacity(0.1)
                                        : dangerColor.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                      color:
                                          acertou ? successColor : dangerColor,
                                      width: 1,
                                    ),
                                  ),
                                  child: Text(
                                    acertou
                                        ? '+${valorQuestao.toStringAsFixed(1)}'
                                        : '0,0',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color:
                                          acertou ? successColor : dangerColor,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Icon(
                                  acertou ? Icons.check_circle : Icons.cancel,
                                  color: acertou ? successColor : dangerColor,
                                  size: 20,
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                      childCount: widget.gabarito.length,
                    ),
                  ),

                  // Espaçamento extra no final para os botões
                  const SliverToBoxAdapter(
                    child: SizedBox(height: 80),
                  ),
                ],
              ),
            ),

            // Botões de navegação - fixed at bottom
            Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: bgSurface,
                border: const Border(top: BorderSide(color: borderColor)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 5,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: () => Navigator.pop(context),
                        borderRadius: BorderRadius.circular(4),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          decoration: BoxDecoration(
                            color: bgSurface,
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: borderColor, width: 2),
                          ),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.arrow_back,
                                  size: 18, color: textLight),
                              SizedBox(width: 8),
                              Text(
                                'Voltar',
                                style: TextStyle(
                                  color: textLight,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: () {
                          Navigator.of(context)
                              .popUntil((route) => route.isFirst);
                        },
                        borderRadius: BorderRadius.circular(4),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [primaryColor, secondaryColor],
                              begin: Alignment.centerLeft,
                              end: Alignment.centerRight,
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.home, size: 18, color: Colors.white),
                              SizedBox(width: 8),
                              Text(
                                'Início',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Método para enviar resultados para o site
  Future<void> _submitResultsToWebsite() async {
    if (widget.alunoId == null || widget.simuladoId == null) {
      setState(() {
        _submissionMessage =
            'Não foi possível enviar: dados do aluno ou simulado faltando';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _submissionMessage = '';
    });

    try {
      final apiService = ApiService();
      final versao = 'versao${widget.tipoProva}';

      final success = await apiService.submitStudentResults(
        studentId: widget.alunoId!,
        simuladoId: widget.simuladoId!,
        versao: versao,
        nota: widget.notaFinal,
        respostasAluno: widget.respostasAluno,
        gabarito: widget.gabarito,
      );

      setState(() {
        _isSubmitting = false;
        _hasSubmitted = success;
        _submissionMessage = success
            ? 'Resultados enviados com sucesso para o site!'
            : 'Falha ao enviar resultados. Tente novamente.';
      });

      // ignore: use_build_context_synchronously
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(
                success ? Icons.check_circle : Icons.error,
                color: Colors.white,
              ),
              const SizedBox(width: 16),
              Text(
                success
                    ? 'Resultados enviados com sucesso!'
                    : 'Falha ao enviar resultados.',
                style: const TextStyle(color: Colors.white),
              ),
            ],
          ),
          backgroundColor: success ? successColor : dangerColor,
          duration: const Duration(seconds: 3),
        ),
      );
    } catch (e) {
      setState(() {
        _isSubmitting = false;
        _submissionMessage = 'Erro ao enviar: $e';
      });

      // ignore: use_build_context_synchronously
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.error, color: Colors.white),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  'Erro ao enviar: $e',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
          backgroundColor: dangerColor,
          duration: const Duration(seconds: 5),
        ),
      );
    }
  }
}
