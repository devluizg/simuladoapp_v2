//cartao_resposta_preview_screen.dart
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'resultado_screen.dart';
import 'dart:developer' as developer;

class CartaoRespostaPreviewScreen extends StatefulWidget {
  final Uint8List imagemProcessada;
  final Map<String, String> respostasAluno;
  final Map<String, String> gabarito;
  final String nomeAluno;
  final double notaFinal;
  final int tipoProva;
  final double pontuacaoTotal;

  // Adicionar campos para conectar com o site
  final int? alunoId;
  final int? simuladoId;
  final int? turmaId;
  final String? nomeTurma;
  final String? nomeSimulado;

  const CartaoRespostaPreviewScreen({
    super.key,
    required this.imagemProcessada,
    required this.respostasAluno,
    required this.gabarito,
    required this.nomeAluno,
    required this.notaFinal,
    required this.tipoProva,
    required this.pontuacaoTotal,
    this.alunoId,
    this.simuladoId,
    this.turmaId,
    this.nomeTurma,
    this.nomeSimulado,
  });

  @override
  State<CartaoRespostaPreviewScreen> createState() =>
      _CartaoRespostaPreviewScreenState();
}

class _CartaoRespostaPreviewScreenState
    extends State<CartaoRespostaPreviewScreen> {
  bool _processingCorrection = false;

  /// Confirmar correção
  Future<void> _confirmarCorrecao() async {
    await _processCorrection();
  }

  /// Processar correção
  Future<void> _processCorrection() async {
    setState(() {
      _processingCorrection = true;
    });

    // Mostrar loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => PopScope(
        canPop: false,
        child: Center(
          child: Card(
            color: const Color(0xFF1D203A), // AppColors.bgSurface
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(
                  color: Color(0xFF31355B), width: 1), // AppColors.borderColor
            ),
            child: const Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(
                    color: Color(0xFF00A4D9), // AppColors.primaryColor
                    backgroundColor: Color(0xFF31355B), // AppColors.borderColor
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Processando correção...',
                    style: TextStyle(
                      fontSize: 16,
                      color: Color(0xFFE0E6F1), // AppColors.textLight
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    try {
      // Simular um pequeno atraso para o usuário ver o loading
      await Future.delayed(const Duration(seconds: 1));

      // Fechar loading
      if (mounted) Navigator.pop(context);

      setState(() {
        _processingCorrection = false;
      });

      // Sucesso - navegar para resultados
      if (mounted) {
        // Navegar para a tela de resultados
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultadoScreen(
              nomeAluno: widget.nomeAluno,
              notaFinal: widget.notaFinal,
              respostasAluno: widget.respostasAluno,
              gabarito: widget.gabarito,
              tipoProva: widget.tipoProva,
              pontuacaoTotal: widget.pontuacaoTotal,
              alunoId: widget.alunoId,
              simuladoId: widget.simuladoId,
              turmaId: widget.turmaId,
              nomeTurma: widget.nomeTurma,
              nomeSimulado: widget.nomeSimulado,
            ),
          ),
        );
      }
    } catch (e) {
      // Fechar loading se ainda estiver aberto
      if (mounted) {
        Navigator.pop(context);

        setState(() {
          _processingCorrection = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error, color: Colors.white),
                const SizedBox(width: 16),
                Expanded(child: Text('Erro inesperado: $e')),
              ],
            ),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }

      developer.log('💳 Erro ao processar correção: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    // Calcular estatísticas
    final int totalQuestoes = widget.gabarito.length;
    final int questoesAcertadas = widget.gabarito.keys
        .where((questao) =>
            widget.respostasAluno[questao] == widget.gabarito[questao])
        .length;

    return Scaffold(
      backgroundColor: Colors.black87,
      appBar: AppBar(
        title: const Text(
          'Visualização da Correção',
          style: TextStyle(color: Colors.white),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          // Camada de fundo escura
          Container(
            color: Colors.black87,
          ),

          // Conteúdo central - Cartão resposta e informações
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Informações sobre o aluno e nota
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16.0, vertical: 8.0),
                    child: Card(
                      color: Colors.white.withOpacity(0.1),
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Column(
                          children: [
                            Text(
                              widget.nomeAluno,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            if (widget.nomeTurma != null &&
                                widget.nomeTurma!.isNotEmpty) ...[
                              const SizedBox(height: 2),
                              Text(
                                'Turma: ${widget.nomeTurma}',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.white.withOpacity(0.9),
                                ),
                              ),
                            ],
                            if (widget.nomeSimulado != null &&
                                widget.nomeSimulado!.isNotEmpty) ...[
                              const SizedBox(height: 2),
                              Text(
                                'Simulado: ${widget.nomeSimulado}',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.white.withOpacity(0.9),
                                ),
                              ),
                            ],
                            const SizedBox(height: 4),
                            Text(
                              'Versão da prova: ${widget.tipoProva}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.white.withOpacity(0.9),
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Acertos: $questoesAcertadas/$totalQuestoes questões',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.white.withOpacity(0.9),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // Cartão resposta com zoom habilitado
                  SizedBox(
                    // Define uma altura para a imagem para não causar erro de layout infinito
                    height: MediaQuery.of(context).size.height * 0.5,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8.0),
                      child: InteractiveViewer(
                        minScale: 0.5,
                        maxScale: 3.0,
                        boundaryMargin: const EdgeInsets.all(20.0),
                        child: Image.memory(
                          widget.imagemProcessada,
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24), // Espaço entre a imagem e os botões

                  // Botões agora dentro da área de rolagem
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        // Botão de recomeçar
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.only(right: 8.0),
                            child: ElevatedButton.icon(
                              onPressed: _processingCorrection
                                  ? null
                                  : () {
                                      Navigator.pop(
                                          context); // Volta para a tela anterior
                                    },
                              icon: Icon(
                                Icons.refresh,
                                color: _processingCorrection
                                    ? Colors.grey
                                    : Colors.white,
                              ),
                              label: Text(
                                'RECOMEÇAR',
                                style: TextStyle(
                                  color: _processingCorrection
                                      ? Colors.grey
                                      : Colors.white,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: _processingCorrection
                                    ? Colors.grey
                                    : Colors.red,
                                foregroundColor: Colors.white,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                              ),
                            ),
                          ),
                        ),

                        // Botão de confirmar
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.only(left: 8.0),
                            child: ElevatedButton.icon(
                              onPressed: _processingCorrection
                                  ? null
                                  : _confirmarCorrecao,
                              icon: _processingCorrection
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : Icon(
                                      Icons.check,
                                      color: _processingCorrection
                                          ? Colors.grey
                                          : Colors.white,
                                    ),
                              label: Text(
                                _processingCorrection
                                    ? 'PROCESSANDO...'
                                    : 'CONFIRMAR',
                                style: TextStyle(
                                  color: _processingCorrection
                                      ? Colors.grey
                                      : Colors.white,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: _processingCorrection
                                    ? Colors.grey
                                    : Colors.green,
                                foregroundColor: Colors.white,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24), // Espaço extra para rolagem
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
