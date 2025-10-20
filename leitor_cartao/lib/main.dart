import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert' show utf8, latin1, jsonDecode, json, base64Decode;
import 'package:logging/logging.dart' show Logger;
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/cartao_resposta_preview_screen.dart';
import 'screens/selection_screen.dart';

// Importar a tela de login
import 'screens/login_screen.dart';
// Importar o serviço de API
import 'services/api_service.dart';

final Logger _logger = Logger('CartaoRespostaApp');
final ApiService _apiService = ApiService();

// Paleta de cores do site Django
class AppColors {
  static const Color primaryColor = Color(0xFF00A4D9); // Ciano vibrante
  static const Color secondaryColor = Color(0xFF434891); // Índigo profundo
  static const Color bgDark = Color(0xFF121425); // Fundo ultra escuro
  static const Color bgSurface = Color(0xFF1D203A); // Superfícies
  static const Color borderColor = Color(0xFF31355B); // Bordas sutis
  static const Color textLight = Color(0xFFE0E6F1); // Texto claro
  static const Color textMuted = Color(0xFF8C96C3); // Texto secundário
  static const Color successColor = Color(0xFF2DD8A3); // Sucesso
  static const Color dangerColor = Color(0xFFE94B6A); // Erro
  static const Color warningColor = Color(0xFFF2A93B); // Aviso
}

void main() {
  runApp(const CartaoRespostaApp());
}

class CartaoRespostaApp extends StatefulWidget {
  const CartaoRespostaApp({super.key});

  @override
  State<CartaoRespostaApp> createState() => _CartaoRespostaAppState();
}

class _CartaoRespostaAppState extends State<CartaoRespostaApp> {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SimuladoApp',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        scaffoldBackgroundColor: AppColors.bgDark,
        cardTheme: CardTheme(
          color: AppColors.bgSurface,
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: AppColors.borderColor, width: 1),
          ),
        ),
      ),
      home: const AuthenticationWrapper(),
    );
  }
}

// Classe para verificar a autenticação do usuário
class AuthenticationWrapper extends StatefulWidget {
  const AuthenticationWrapper({super.key});

  @override
  State<AuthenticationWrapper> createState() => _AuthenticationWrapperState();
}

class _AuthenticationWrapperState extends State<AuthenticationWrapper> {
  bool _checkingAuth = true;
  bool _isAuthenticated = false;

  @override
  void initState() {
    super.initState();
    _checkAuthentication();
  }

  Future<void> _checkAuthentication() async {
    final prefs = await SharedPreferences.getInstance();
    final accessToken = prefs.getString('access_token');

    setState(() {
      _isAuthenticated = accessToken != null;
      _checkingAuth = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_checkingAuth) {
      return const Scaffold(
        backgroundColor: AppColors.bgDark,
        body: Center(
          child: CircularProgressIndicator(
            color: AppColors.primaryColor,
          ),
        ),
      );
    }

    if (_isAuthenticated) {
      return const SelectionScreen();
    } else {
      return const LoginScreen();
    }
  }
}

class TelaInicial extends StatefulWidget {
  final int turmaId;
  final int simuladoId;
  final int alunoId;
  final Map<String, dynamic> aluno;
  final Map<String, dynamic> simulado;
  final Map<String, dynamic>? turma; // ADICIONADO

  const TelaInicial({
    super.key,
    required this.turmaId,
    required this.simuladoId,
    required this.alunoId,
    required this.aluno,
    required this.simulado,
    this.turma, // ADICIONADO
  });

  @override
  State<TelaInicial> createState() => _TelaInicialState();
}

class _TelaInicialState extends State<TelaInicial> {
  File? _imagemSelecionada;
  final ImagePicker _picker = ImagePicker();
  bool _enviando = false;
  String? _mensagemErro;

  // Variáveis para dados do simulado
  bool _carregandoSimulado = true;
  int? _numeroQuestoes;
  double? _pontuacaoTotal; // Vem do Django
  String _tituloSimulado = '';
  String _nomeAluno = '';

  Uint8List? _imagemOriginalProcessada;
  bool _temImagensProcessadas = false;

  final TextEditingController _enderecoIPController =
      TextEditingController(text: "https://simuladoapp.com.br");
  int _tipoProva = 1;

  String _decodificarTexto(String? texto) {
    if (texto == null || texto.isEmpty) return '';

    // Decodificar caracteres HTML/UTF-8 comuns
    String textoDecodificado = texto
        .replaceAll('&amp;', '&')
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .replaceAll('&quot;', '"')
        .replaceAll('&#39;', "'")
        .replaceAll('&aacute;', 'á')
        .replaceAll('&Aacute;', 'Á')
        .replaceAll('&agrave;', 'à')
        .replaceAll('&Agrave;', 'À')
        .replaceAll('&acirc;', 'â')
        .replaceAll('&Acirc;', 'Â')
        .replaceAll('&atilde;', 'ã')
        .replaceAll('&Atilde;', 'Ã')
        .replaceAll('&eacute;', 'é')
        .replaceAll('&Eacute;', 'É')
        .replaceAll('&ecirc;', 'ê')
        .replaceAll('&Ecirc;', 'Ê')
        .replaceAll('&iacute;', 'í')
        .replaceAll('&Iacute;', 'Í')
        .replaceAll('&oacute;', 'ó')
        .replaceAll('&Oacute;', 'Ó')
        .replaceAll('&ocirc;', 'ô')
        .replaceAll('&Ocirc;', 'Ô')
        .replaceAll('&otilde;', 'õ')
        .replaceAll('&Otilde;', 'Õ')
        .replaceAll('&uacute;', 'ú')
        .replaceAll('&Uacute;', 'Ú')
        .replaceAll('&ccedil;', 'ç')
        .replaceAll('&Ccedil;', 'Ç')
        .replaceAll('&ntilde;', 'ñ')
        .replaceAll('&Ntilde;', 'Ñ');

    // Tentar decodificar UTF-8 se necessário
    try {
      // Se o texto contém sequências como "Ã§Ã£o"
      if (textoDecodificado.contains('Ã')) {
        List<int> bytes = latin1.encode(textoDecodificado);
        textoDecodificado = utf8.decode(bytes, allowMalformed: true);
      }
    } catch (e) {
      // Se falhar, manter o texto original
      if (kDebugMode) {
        print('Erro ao decodificar UTF-8: $e');
      }
    }

    return textoDecodificado.trim();
  }

  @override
  void initState() {
    super.initState();
    _inicializarDados();
  }

  // Inicializar dados
  Future<void> _inicializarDados() async {
    // Carregar dados básicos primeiro
    String nomeOriginal =
        widget.aluno['nome'] ?? widget.aluno['name'] ?? 'Aluno';
    String tituloOriginal = widget.simulado['titulo'] ?? 'Simulado';

    _nomeAluno = _decodificarTexto(nomeOriginal);
    _tituloSimulado = _decodificarTexto(tituloOriginal);

    _logger.info('Nome do aluno decodificado: $_nomeAluno');
    _logger.info('Título do simulado decodificado: $_tituloSimulado');

    // Carregar detalhes do simulado se disponível
    await _carregarDadosSimulado();
  }

  // Carregar dados do simulado do Django
  Future<void> _carregarDadosSimulado() async {
    setState(() {
      _carregandoSimulado = true;
      _mensagemErro = null;
    });

    try {
      if (widget.simuladoId > 0) {
        _logger.info('Carregando detalhes do simulado ${widget.simuladoId}...');

        // Buscar detalhes completos do simulado
        final detalhes =
            await _apiService.getSimuladoDetalhes(widget.simuladoId);

        if (detalhes != null && mounted) {
          setState(() {
            _numeroQuestoes =
                detalhes['numero_questoes'] ?? detalhes['total_questoes'];
            // Converter para double - o Django retorna um inteiro
            _pontuacaoTotal = (detalhes['pontuacao_total'] ?? 10).toDouble();

            String tituloApi = detalhes['titulo'] ?? _tituloSimulado;
            _tituloSimulado = _decodificarTexto(tituloApi);

            _carregandoSimulado = false;
          });

          _logger.info('Simulado carregado: $_tituloSimulado');
          _logger.info('Número de questões: $_numeroQuestoes');
          _logger.info('Pontuação total: $_pontuacaoTotal');
        } else {
          // Fallback - tentar buscar simulado básico
          _logger.warning(
              'Detalhes não encontrados, tentando buscar simulado básico...');
          final response = await _apiService
              .authorizedRequest('/api/simulados/${widget.simuladoId}/');

          if (response.statusCode == 200) {
            final simuladoData = jsonDecode(response.body);
            setState(() {
              _numeroQuestoes = simuladoData['questoes']?.length ?? 10;
              _pontuacaoTotal =
                  (simuladoData['pontuacao_total'] ?? 10).toDouble();

              String tituloFallback = simuladoData['titulo'] ?? _tituloSimulado;
              _tituloSimulado = _decodificarTexto(tituloFallback);

              _carregandoSimulado = false;
            });
            _logger.info(
                'Simulado carregado via fallback: $_numeroQuestoes questões');
          } else {
            throw Exception('Não foi possível carregar os dados do simulado');
          }
        }
      } else {
        // Sem simulado selecionado - usar valores padrão
        setState(() {
          _numeroQuestoes = 10;
          _pontuacaoTotal = 10.0;
          _carregandoSimulado = false;
        });
        _logger.warning('Nenhum simulado selecionado, usando valores padrão');
      }
    } catch (e) {
      setState(() {
        _mensagemErro = 'Erro ao carregar simulado: $e';
        _numeroQuestoes = 10; // Fallback
        _pontuacaoTotal = 10.0; // Fallback
        _carregandoSimulado = false;
      });
      _logger.severe('Erro ao carregar simulado: $e');
    }
  }

  Future<void> _capturarImagem() async {
    try {
      final XFile? imagem = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 100,
        preferredCameraDevice: CameraDevice.rear,
        maxWidth: 1600,
        maxHeight: 1200,
      );

      if (imagem != null) {
        setState(() {
          _imagemSelecionada = File(imagem.path);
          _mensagemErro = null;
          _temImagensProcessadas = false;
        });
      }
    } catch (e) {
      setState(() {
        _mensagemErro = "Erro ao capturar imagem: $e";
      });
    }
  }

  Future<void> _selecionarDaGaleria() async {
    try {
      final XFile? imagem = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 100,
        maxWidth: 1600,
        maxHeight: 1200,
      );

      if (imagem != null) {
        setState(() {
          _imagemSelecionada = File(imagem.path);
          _mensagemErro = null;
          _temImagensProcessadas = false;
        });
      }
    } catch (e) {
      setState(() {
        _mensagemErro = "Erro ao selecionar imagem: $e";
      });
    }
  }

  // Função para obter o gabarito da API baseado no tipo de prova
  Future<Map<String, String>?> _obterGabarito() async {
    try {
      if (widget.simuladoId <= 0) {
        return _getGabaritoLocal();
      }

      final gabarito = await _apiService.getGabarito(
        widget.simuladoId,
        tipo: _tipoProva.toString(),
      );

      if (gabarito != null) {
        _logger.info('Gabarito obtido da API: $gabarito');
        return gabarito;
      } else {
        _logger.warning('Falha ao obter gabarito da API, usando local');
        return _getGabaritoLocal();
      }
    } catch (e) {
      _logger.severe('Erro ao obter gabarito: $e');
      return _getGabaritoLocal();
    }
  }

  // Gabarito local usando _numeroQuestoes
  Map<String, String> _getGabaritoLocal() {
    int numQuestoes = _numeroQuestoes ?? 10;
    Map<String, String> gabarito = {};

    switch (_tipoProva) {
      case 1:
        final respostas = ['D', 'D', 'D', 'C', 'C', 'B', 'D', 'C', 'D', 'D'];
        for (int i = 0; i < numQuestoes && i < respostas.length; i++) {
          gabarito[(i + 1).toString()] = respostas[i];
        }
        break;
      case 2:
        final respostas = ['C', 'C', 'C', 'B', 'B', 'A', 'C', 'B', 'C', 'C'];
        for (int i = 0; i < numQuestoes && i < respostas.length; i++) {
          gabarito[(i + 1).toString()] = respostas[i];
        }
        break;
      case 3:
        final respostas = ['B', 'B', 'B', 'A', 'A', 'E', 'B', 'A', 'B', 'B'];
        for (int i = 0; i < numQuestoes && i < respostas.length; i++) {
          gabarito[(i + 1).toString()] = respostas[i];
        }
        break;
      case 4:
        final respostas = ['A', 'A', 'A', 'E', 'E', 'D', 'A', 'E', 'A', 'A'];
        for (int i = 0; i < numQuestoes && i < respostas.length; i++) {
          gabarito[(i + 1).toString()] = respostas[i];
        }
        break;
      case 5:
        final respostas = ['E', 'E', 'E', 'D', 'D', 'C', 'E', 'D', 'E', 'E'];
        for (int i = 0; i < numQuestoes && i < respostas.length; i++) {
          gabarito[(i + 1).toString()] = respostas[i];
        }
        break;
      default:
        for (int i = 1; i <= numQuestoes; i++) {
          gabarito[i.toString()] = 'A';
        }
    }

    return gabarito;
  }

  int _determinarNumColunas(int numQuestoes) {
    if (numQuestoes <= 23) {
      return 1;
    } else if (numQuestoes <= 45) {
      return 2;
    } else {
      return 3;
    }
  }

  Future<void> _logout() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('access_token');
      await prefs.remove('refresh_token');
      await prefs.remove('user_name');
      await prefs.remove('user_email');

      if (!mounted) return;

      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const LoginScreen()),
        (route) => false,
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro ao fazer logout: $e'),
          backgroundColor: AppColors.dangerColor,
        ),
      );
    }
  }

  // Enviar imagem para processamento
  Future<void> _enviarImagem() async {
    if (_imagemSelecionada == null) {
      setState(() {
        _mensagemErro = "Por favor, selecione uma imagem primeiro.";
      });
      return;
    }

    // Verificar se número de questões foi carregado
    if (_numeroQuestoes == null) {
      setState(() {
        _mensagemErro =
            "Número de questões não definido. Tente recarregar o simulado.";
      });
      return;
    }

    setState(() {
      _enviando = true;
      _mensagemErro = null;
      _temImagensProcessadas = false;
    });

    try {
      final imgBytes = await _imagemSelecionada!.readAsBytes();
      _logger.info('Enviando imagem: ${_imagemSelecionada!.path}');
      _logger.info('Tamanho da imagem: ${imgBytes.length} bytes');
      _logger.info('Número de questões do simulado: $_numeroQuestoes');

      final uri =
          Uri.parse('https://cartao-resposta.onrender.com/processar_cartao');
      final request = http.MultipartRequest('POST', uri);

      request.files.add(await http.MultipartFile.fromPath(
        'file',
        _imagemSelecionada!.path,
      ));

      // Usar _numeroQuestoes em vez de controller
      request.fields['num_questoes'] = _numeroQuestoes.toString();
      int numColunas = _determinarNumColunas(_numeroQuestoes!);
      request.fields['num_colunas'] = numColunas.toString();
      request.fields['threshold'] = '150';
      request.fields['retornar_imagens'] = 'true';

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      _logger.info('Resposta do servidor: ${response.statusCode}');

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        setState(() {
          _enviando = false;

          _temImagensProcessadas =
              responseData.containsKey('imagem_processada_base64') &&
                  responseData['imagem_processada_base64'] != null;

          if (_temImagensProcessadas) {
            try {
              _imagemOriginalProcessada =
                  base64Decode(responseData['imagem_processada_base64']);
            } catch (e) {
              _temImagensProcessadas = false;
              _logger.warning('Erro ao decodificar imagens: $e');
            }
          }
        });

        if (responseData.containsKey('respostas') &&
            responseData['respostas'] != null) {
          Map<String, String> respostasAluno = {};
          if (responseData['respostas'] is Map) {
            responseData['respostas'].forEach((key, value) {
              respostasAluno[key.toString()] =
                  value != null ? value.toString() : 'Não detectada';
            });
          } else if (responseData['respostas'] is List) {
            for (int i = 0; i < responseData['respostas'].length; i++) {
              final resposta = responseData['respostas'][i];
              respostasAluno[(i + 1).toString()] =
                  resposta != null ? resposta.toString() : 'Não detectada';
            }
          }

          final gabarito = await _obterGabarito();

          if (gabarito == null) {
            setState(() {
              _mensagemErro =
                  "Erro ao obter o gabarito. Verifique sua conexão.";
              _enviando = false;
            });
            return;
          }

          // Usar pontuação total do Django
          double pontuacaoTotal = _pontuacaoTotal ?? 10.0;
          int numQuestoes = gabarito.length;
          double valorPorQuestao = pontuacaoTotal / numQuestoes;
          double notaFinal = 0;

          respostasAluno.forEach((questao, resposta) {
            if (resposta == gabarito[questao]) {
              notaFinal += valorPorQuestao;
            }
          });

          // Usar _nomeAluno em vez de acessar widget.aluno diretamente
          String nomeAluno = _nomeAluno.isNotEmpty ? _nomeAluno : 'Aluno';

          if (_imagemOriginalProcessada != null) {
            Navigator.push(
              // ignore: use_build_context_synchronously
              context,
              MaterialPageRoute(
                builder: (context) => CartaoRespostaPreviewScreen(
                  imagemProcessada: _imagemOriginalProcessada!,
                  respostasAluno: respostasAluno,
                  gabarito: gabarito,
                  nomeAluno: nomeAluno,
                  notaFinal: notaFinal,
                  tipoProva: _tipoProva,
                  pontuacaoTotal: pontuacaoTotal,
                  alunoId: widget.alunoId,
                  simuladoId: widget.simuladoId,
                  turmaId: widget.turmaId,
                  nomeTurma: widget.turma?['nome'],
                  nomeSimulado: _tituloSimulado,
                ),
              ),
            );
          } else {
            Navigator.push(
              // ignore: use_build_context_synchronously
              context,
              MaterialPageRoute(
                builder: (context) => CartaoRespostaPreviewScreen(
                  imagemProcessada: imgBytes,
                  respostasAluno: respostasAluno,
                  gabarito: gabarito,
                  nomeAluno: nomeAluno,
                  notaFinal: notaFinal,
                  tipoProva: _tipoProva,
                  pontuacaoTotal: pontuacaoTotal,
                  alunoId: widget.alunoId,
                  simuladoId: widget.simuladoId,
                  turmaId: widget.turmaId,
                  nomeTurma: widget.turma?['nome'],
                  nomeSimulado: _tituloSimulado,
                ),
              ),
            );
          }
        }
      } else {
        setState(() {
          _mensagemErro =
              "Erro no servidor: ${response.statusCode} - ${response.body}";
          _enviando = false;
        });
      }
    } catch (e) {
      setState(() {
        _mensagemErro = "Erro ao enviar a imagem: $e";
        _enviando = false;
      });
    }
  }

  // ignore: unused_element
  Future<void> _atualizarIndicadorCreditos() async {
    if (mounted) {
      setState(() {
        // Força o rebuild do FutureBuilder
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgDark,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: AppColors.bgSurface,
        foregroundColor: AppColors.textLight,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primaryColor, AppColors.secondaryColor],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.display_settings,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Text(
              _carregandoSimulado ? 'Carregando...' : 'SimuladoApp',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 20,
                color: AppColors.textLight,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Recarregar Simulado',
            onPressed: _carregarDadosSimulado,
            color: AppColors.textMuted,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sair',
            onPressed: _logout,
            color: AppColors.textMuted,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            height: 1,
            color: AppColors.borderColor,
          ),
        ),
      ),
      body: _carregandoSimulado
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(
                    color: AppColors.primaryColor,
                    backgroundColor: AppColors.borderColor,
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Carregando dados do simulado...',
                    style: TextStyle(color: AppColors.textMuted),
                  ),
                ],
              ),
            )
          : ListView(
              padding: const EdgeInsets.all(12.0),
              children: [
                const SizedBox(height: 12),

                // Card com informações do simulado
                Card(
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: const BorderSide(
                        color: AppColors.borderColor, width: 1),
                  ),
                  color: Colors.transparent,
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      gradient: const LinearGradient(
                        colors: [
                          AppColors.secondaryColor,
                          AppColors.primaryColor
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Header com ícone e nome do simulado
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(
                                    color: Colors.white.withOpacity(0.3),
                                    width: 1,
                                  ),
                                ),
                                child: const Icon(
                                  Icons.quiz,
                                  color: AppColors.textLight,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: SelectableText(
                                  _decodificarTexto(_tituloSimulado),
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textLight,
                                  ),
                                  maxLines: 2,
                                ),
                              ),
                            ],
                          ),
                          // Adicione aqui o resto do conteúdo do card do simulado

                          const SizedBox(height: 12),

                          // Nome do aluno completo
                          SelectableText(
                            _decodificarTexto(_nomeAluno),
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                            maxLines: 1,
                          ),

                          const SizedBox(height: 16),

                          // Apenas 2 cards: Questões e Pontuação
                          Row(
                            children: [
                              // Card de Questões
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: AppColors.bgSurface.withOpacity(0.5),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                        color: AppColors.borderColor),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.3),
                                        blurRadius: 4,
                                        offset: const Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    children: [
                                      const Icon(
                                        Icons.help_outline,
                                        color: AppColors.primaryColor,
                                        size: 24,
                                      ),
                                      const SizedBox(height: 8),
                                      const Text(
                                        'Questões',
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: AppColors.textMuted,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        '${_numeroQuestoes ?? "..."}',
                                        style: const TextStyle(
                                          fontSize: 22,
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.textLight,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),

                              const SizedBox(width: 16),

                              // Card de Pontuação
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: AppColors.bgSurface.withOpacity(0.5),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                        color: AppColors.borderColor),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.3),
                                        blurRadius: 4,
                                        offset: const Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    children: [
                                      const Icon(
                                        Icons.grade,
                                        color: AppColors.warningColor,
                                        size: 24,
                                      ),
                                      const SizedBox(height: 8),
                                      const Text(
                                        'Pontuação',
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: AppColors.textMuted,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        _pontuacaoTotal?.toStringAsFixed(1) ??
                                            "...",
                                        style: const TextStyle(
                                          fontSize: 22,
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.textLight,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // Card de configuração do tipo de prova
                Card(
                  elevation: 3,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: const BorderSide(
                        color: AppColors.borderColor, width: 1),
                  ),
                  color: AppColors.bgSurface.withOpacity(0.5),
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [
                                    AppColors.primaryColor,
                                    AppColors.secondaryColor
                                  ],
                                ),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Icon(
                                Icons.quiz_outlined,
                                color: Colors.white,
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            const Text(
                              'Tipo de Prova',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryColor,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: List.generate(5, (index) {
                            final tipo = index + 1;
                            return Expanded(
                              child: Padding(
                                padding: EdgeInsets.only(
                                  left: index == 0 ? 0 : 4,
                                  right: index == 4 ? 0 : 4,
                                ),
                                child: Container(
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(4),
                                    boxShadow: _tipoProva == tipo
                                        ? [
                                            BoxShadow(
                                              color: AppColors.primaryColor
                                                  .withOpacity(0.3),
                                              blurRadius: 8,
                                              offset: const Offset(0, 4),
                                            ),
                                          ]
                                        : null,
                                  ),
                                  child: ChoiceChip(
                                    label: Text(
                                      '$tipo',
                                      style: TextStyle(
                                        color: _tipoProva == tipo
                                            ? Colors.white
                                            : AppColors.textLight,
                                        fontWeight: FontWeight.w600,
                                        fontSize: 14, // Diminuído de 16 para 14
                                      ),
                                    ),
                                    selected: _tipoProva == tipo,
                                    onSelected: (selected) {
                                      if (selected) {
                                        setState(() {
                                          _tipoProva = tipo;
                                        });
                                      }
                                    },
                                    backgroundColor: AppColors.bgDark,
                                    selectedColor: AppColors.primaryColor,
                                    elevation: 2,
                                    pressElevation: 4,
                                    side: BorderSide(
                                      color: _tipoProva == tipo
                                          ? AppColors.primaryColor
                                          : AppColors.borderColor,
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // Área da imagem
                Card(
                  color: AppColors.bgSurface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: const BorderSide(
                        color: AppColors.borderColor, width: 1),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      height: 200,
                      decoration: BoxDecoration(
                        color: AppColors.bgDark,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: _imagemSelecionada != null
                          ? Image.file(
                              _imagemSelecionada!,
                              fit: BoxFit.contain,
                            )
                          : const Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.camera_alt_outlined,
                                    size: 48,
                                    color: AppColors.textMuted,
                                  ),
                                  SizedBox(height: 8),
                                  Text(
                                    'Nenhuma imagem selecionada',
                                    style:
                                        TextStyle(color: AppColors.textMuted),
                                  ),
                                ],
                              ),
                            ),
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // Botões de captura
                Row(
                  children: [
                    Expanded(
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: _capturarImagem,
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [
                                  AppColors.primaryColor,
                                  AppColors.secondaryColor
                                ],
                                begin: Alignment.centerLeft,
                                end: Alignment.centerRight,
                              ),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.camera_alt,
                                    size: 20, color: Colors.white),
                                SizedBox(width: 8),
                                Text(
                                  'Câmera',
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
                    const SizedBox(width: 8),
                    Expanded(
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: _selecionarDaGaleria,
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: AppColors.bgSurface,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                  color: AppColors.borderColor, width: 2),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.photo_library,
                                    size: 20, color: AppColors.textLight),
                                SizedBox(width: 8),
                                Text(
                                  'Galeria',
                                  style: TextStyle(
                                    color: AppColors.textLight,
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

                const SizedBox(height: 12),

                // Botão de processar
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: _imagemSelecionada == null || _enviando
                          ? null
                          : _enviarImagem,
                      borderRadius: BorderRadius.circular(4),
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: _imagemSelecionada == null || _enviando
                              ? null
                              : const LinearGradient(
                                  colors: [
                                    AppColors.successColor,
                                    AppColors.primaryColor
                                  ],
                                  begin: Alignment.centerLeft,
                                  end: Alignment.centerRight,
                                ),
                          color: _imagemSelecionada == null || _enviando
                              ? AppColors.borderColor
                              : null,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        alignment: Alignment.center,
                        child: _enviando
                            ? const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  ),
                                  SizedBox(width: 12),
                                  Text(
                                    'Processando...',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              )
                            : const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.play_arrow,
                                      size: 24, color: Colors.white),
                                  SizedBox(width: 8),
                                  Text(
                                    'Processar Cartão Resposta',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // Exibição de erro
                if (_mensagemErro != null)
                  Card(
                    color: AppColors.dangerColor.withOpacity(0.1),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: const BorderSide(
                          color: AppColors.dangerColor, width: 1),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(
                                Icons.error_outline,
                                color: AppColors.dangerColor,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              const Text(
                                'Erro',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.dangerColor,
                                ),
                              ),
                              const Spacer(),
                              TextButton(
                                onPressed: () {
                                  showDialog(
                                    context: context,
                                    builder: (context) => AlertDialog(
                                      backgroundColor: AppColors.bgSurface,
                                      title: const Text(
                                        'Detalhes do Erro',
                                        style: TextStyle(
                                            color: AppColors.textLight),
                                      ),
                                      content: SingleChildScrollView(
                                        child: Text(
                                          _mensagemErro!,
                                          style: const TextStyle(
                                              color: AppColors.textMuted),
                                        ),
                                      ),
                                      actions: [
                                        TextButton(
                                          onPressed: () =>
                                              Navigator.pop(context),
                                          child: const Text(
                                            'Fechar',
                                            style: TextStyle(
                                                color: AppColors.primaryColor),
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                                child: const Text(
                                  'Ver detalhes',
                                  style:
                                      TextStyle(color: AppColors.dangerColor),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _mensagemErro!,
                            style: const TextStyle(
                              color: AppColors.dangerColor,
                              fontSize: 14,
                            ),
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                          ),
                          if (_mensagemErro!.contains('simulado'))
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  onTap: _carregarDadosSimulado,
                                  borderRadius: BorderRadius.circular(4),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 12, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: AppColors.dangerColor
                                          .withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(4),
                                      border: Border.all(
                                          color: AppColors.dangerColor),
                                    ),
                                    child: const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.refresh,
                                            size: 16,
                                            color: AppColors.dangerColor),
                                        SizedBox(width: 4),
                                        Text(
                                          'Recarregar Simulado',
                                          style: TextStyle(
                                              color: AppColors.dangerColor),
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
                  ),
                const SizedBox(height: 30), // Espaço extra para rolagem
              ],
            ),
    );
  }

  @override
  void dispose() {
    _enderecoIPController.dispose();
    super.dispose();
  }
}

class ImagensProcessadasScreen extends StatelessWidget {
  final Uint8List imagemOriginal;
  final Uint8List imagemBinaria;

  const ImagensProcessadasScreen({
    super.key,
    required this.imagemOriginal,
    required this.imagemBinaria,
  });

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AppColors.bgDark,
        appBar: AppBar(
          elevation: 0,
          backgroundColor: AppColors.bgSurface,
          foregroundColor: AppColors.textLight,
          title: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primaryColor, AppColors.secondaryColor],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.image_outlined,
                  color: Colors.white,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Imagens Processadas',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: AppColors.textLight,
                ),
              ),
            ],
          ),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(49),
            child: Column(
              children: [
                const TabBar(
                  indicatorColor: AppColors.primaryColor,
                  labelColor: AppColors.textLight,
                  unselectedLabelColor: AppColors.textMuted,
                  tabs: [
                    Tab(
                      text: 'Original',
                      icon: Icon(Icons.image_outlined),
                    ),
                    Tab(
                      text: 'Processada',
                      icon: Icon(Icons.filter_b_and_w_outlined),
                    ),
                  ],
                ),
                Container(
                  height: 1,
                  color: AppColors.borderColor,
                ),
              ],
            ),
          ),
        ),
        body: TabBarView(
          children: [
            // Tab da imagem original
            Container(
              color: AppColors.bgDark,
              child: Center(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Card(
                          color: AppColors.bgSurface,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: const BorderSide(
                                color: AppColors.borderColor, width: 1),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        gradient: const LinearGradient(
                                          colors: [
                                            AppColors.primaryColor,
                                            AppColors.secondaryColor
                                          ],
                                        ),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: const Icon(
                                        Icons.image_outlined,
                                        color: Colors.white,
                                        size: 20,
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    const Text(
                                      'Imagem Original com Marcações',
                                      style: TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                        color: AppColors.primaryColor,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Esta é a imagem capturada com as marcações de detecção das respostas.',
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: AppColors.textMuted,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: AppColors.borderColor, width: 1),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.3),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: InteractiveViewer(
                            minScale: 0.5,
                            maxScale: 4.0,
                            boundaryMargin: const EdgeInsets.all(20.0),
                            child: Image.memory(
                              imagemOriginal,
                              fit: BoxFit.contain,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.primaryColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: AppColors.primaryColor.withOpacity(0.3)),
                        ),
                        child: const Row(
                          children: [
                            Icon(
                              Icons.touch_app_outlined,
                              color: AppColors.primaryColor,
                              size: 20,
                            ),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Use gestos de pinça para ampliar e arrastar para navegar',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: AppColors.primaryColor,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // Tab da imagem processada (binarizada)
            Container(
              color: AppColors.bgDark,
              child: Center(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Card(
                          color: AppColors.bgSurface,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: const BorderSide(
                                color: AppColors.borderColor, width: 1),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: AppColors.textMuted,
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: const Icon(
                                        Icons.filter_b_and_w_outlined,
                                        color: Colors.white,
                                        size: 20,
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    const Text(
                                      'Imagem Binarizada',
                                      style: TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                        color: AppColors.textMuted,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Esta é a versão processada em preto e branco usada pelo algoritmo de detecção.',
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: AppColors.textMuted,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: AppColors.borderColor, width: 1),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.3),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: InteractiveViewer(
                            minScale: 0.5,
                            maxScale: 4.0,
                            boundaryMargin: const EdgeInsets.all(20.0),
                            child: Image.memory(
                              imagemBinaria,
                              fit: BoxFit.contain,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.textMuted.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: AppColors.textMuted.withOpacity(0.3)),
                        ),
                        child: const Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              color: AppColors.textMuted,
                              size: 20,
                            ),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Imagem convertida para facilitar a detecção automática das marcações',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textMuted,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        floatingActionButton: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () {
              Navigator.pop(context);
            },
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primaryColor, AppColors.secondaryColor],
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primaryColor.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.arrow_back, color: Colors.white),
                  SizedBox(width: 8),
                  Text(
                    'Voltar',
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
        floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      ),
    );
  }
}
