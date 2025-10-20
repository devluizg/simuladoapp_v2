// ignore_for_file: unused_local_variable

import 'package:flutter/material.dart';
import 'package:leitor_cartao/screens/login_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../main.dart';
import 'dart:developer' as developer;
import 'package:leitor_cartao/services/models/class_model.dart';
import 'package:leitor_cartao/services/models/student_model.dart';
import 'package:leitor_cartao/services/models/simulado_model.dart';

class SelectionScreen extends StatefulWidget {
  const SelectionScreen({super.key});

  @override
  State<SelectionScreen> createState() => _SelectionScreenState();
}

class _SelectionScreenState extends State<SelectionScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  String _errorMessage = '';
  String userName = 'Usuário';

  List<ClassModel> _turmas = [];
  List<SimuladoModel> _simulados = [];
  List<StudentModel> _alunos = [];

  int? _turmaId;
  int? _simuladoId;
  int? _alunoId;

  // Paleta de cores do site Django
  static const Color primaryColor = Color(0xFF00A4D9); // Ciano vibrante
  static const Color secondaryColor = Color(0xFF434891); // Índigo profundo
  static const Color bgDark = Color(0xFF121425); // Fundo ultra escuro
  static const Color bgSurface = Color(0xFF1D203A); // Superfícies
  static const Color borderColor = Color(0xFF31355B); // Bordas sutis
  static const Color textLight = Color(0xFFE0E6F1); // Texto claro
  static const Color textMuted = Color(0xFF8C96C3); // Texto secundário
// Sucesso
  static const Color dangerColor = Color(0xFFE94B6A); // Erro
  static const Color warningColor = Color(0xFFF2A93B); // Aviso

  @override
  void initState() {
    super.initState();
    _iniciarApp();
  }

  Future<void> _iniciarApp() async {
    await _carregarNomeUsuario();
    await _verificarConexao();
  }

  Future<void> _verificarConexao() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final token = await _apiService.getAccessToken();
      if (token == null) {
        developer.log('Token de autenticação ausente');
        setState(() {
          _errorMessage = 'Sessão expirada. Por favor, faça login novamente.';
          _isLoading = false;
        });
        return;
      }

      bool conectado = await _apiService.testConnection();
      if (conectado) {
        developer.log('Conexão com a API estabelecida com sucesso');
        await _carregarTurmas();
      } else {
        setState(() {
          _errorMessage =
              'Não foi possível conectar ao servidor. Verifique se o servidor está rodando.';
          _isLoading = false;
        });
      }
    } catch (e) {
      developer.log('Erro ao verificar conexão: $e');
      setState(() {
        _errorMessage = 'Erro ao verificar conexão com o servidor: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _carregarNomeUsuario() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final nome = prefs.getString('user_name');
      if (nome != null && mounted) {
        setState(() {
          userName = nome;
        });
      } else {
        final userInfo = await _apiService.getUserInfo();
        if (userInfo != null && mounted) {
          setState(() {
            userName = userInfo['name'] ?? 'Usuário';
          });
        }
      }
    } catch (e) {
      developer.log('Erro ao carregar nome do usuário: $e');
    }
  }

  Future<void> _carregarTurmas() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      developer.log('Solicitando turmas da API...');
      final turmas = await _apiService.getClasses();
      developer.log('Turmas recebidas: ${turmas.length}');

      if (mounted) {
        setState(() {
          _turmas = turmas;
          _isLoading = false;

          if (turmas.isEmpty) {
            _errorMessage =
                'Nenhuma turma encontrada. Verifique se existem turmas cadastradas no sistema.';
          }
        });
      }
    } catch (e) {
      developer.log('Erro ao carregar turmas: $e');
      if (mounted) {
        if (e.toString().contains('401')) {
          try {
            bool tokenRenovado = await _apiService.refreshToken();
            if (tokenRenovado) {
              return _carregarTurmas();
            } else {
              _logout();
              return;
            }
          } catch (_) {
            _logout();
            return;
          }
        }

        setState(() {
          _errorMessage = 'Erro ao carregar turmas: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _carregarSimulados(int turmaId) async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
      _simulados = [];
      _simuladoId = null;
    });

    try {
      developer.log('Solicitando simulados para a turma ID: $turmaId');
      final simulados = await _apiService.getSimuladosByClass(turmaId);
      developer.log('Simulados recebidos: ${simulados.length}');

      if (mounted) {
        setState(() {
          _simulados = simulados;
          _isLoading = false;

          if (simulados.isEmpty) {
            _errorMessage = 'Nenhum simulado encontrado para esta turma.';
          }
        });
      }
    } catch (e) {
      developer.log('Erro ao carregar simulados: $e');
      if (mounted) {
        if (e.toString().contains('401')) {
          try {
            bool tokenRenovado = await _apiService.refreshToken();
            if (tokenRenovado) {
              return _carregarSimulados(turmaId);
            }
          } catch (_) {}
        }

        setState(() {
          _errorMessage = 'Erro ao carregar simulados: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _carregarAlunos(int turmaId) async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
      _alunos = [];
      _alunoId = null;
    });

    try {
      developer.log('Solicitando alunos para a turma ID: $turmaId');
      final alunos = await _apiService.getStudentsByClass(turmaId);
      developer.log('Alunos recebidos: ${alunos.length}');

      if (mounted) {
        setState(() {
          _alunos = alunos;
          _isLoading = false;

          if (alunos.isEmpty) {
            _errorMessage = 'Nenhum aluno encontrado para esta turma.';
          }
        });
      }
    } catch (e) {
      developer.log('Erro ao carregar alunos: $e');
      if (mounted) {
        if (e.toString().contains('401')) {
          try {
            bool tokenRenovado = await _apiService.refreshToken();
            if (tokenRenovado) {
              return _carregarAlunos(turmaId);
            }
          } catch (_) {}
        }

        setState(() {
          _errorMessage = 'Erro ao carregar alunos: $e';
          _isLoading = false;
        });
      }
    }
  }

  void _onTurmaChanged(int? value) {
    if (value != null && value != _turmaId) {
      setState(() {
        _turmaId = value;
        _simuladoId = null;
        _alunoId = null;
        _simulados = [];
        _alunos = [];
      });
      developer.log('Turma selecionada: $value');
      _carregarSimulados(value);
      _carregarAlunos(value);
    }
  }

  void _onSimuladoChanged(int? value) {
    setState(() {
      _simuladoId = value;
    });
    developer.log('Simulado selecionado: $value');
  }

  void _onAlunoChanged(int? value) {
    setState(() {
      _alunoId = value;
    });
    developer.log('Aluno selecionado: $value');
  }

  void _continuarParaLeitor() {
    if (_turmaId == null || _simuladoId == null || _alunoId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Row(
            children: [
              Icon(Icons.warning, color: Colors.white),
              SizedBox(width: 8),
              Text('Por favor, selecione todos os campos'),
            ],
          ),
          backgroundColor: warningColor,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      );
      return;
    }

    final alunoSelecionado = _alunos.firstWhere(
      (aluno) => aluno.id == _alunoId,
      orElse: () => StudentModel(
        id: _alunoId!,
        name: 'Desconhecido',
        email: '',
        studentId: '',
        classes: [],
      ),
    );

    final simuladoSelecionado = _simulados.firstWhere(
      (simulado) => simulado.id == _simuladoId,
      orElse: () => SimuladoModel(
        id: _simuladoId!,
        titulo: 'Desconhecido',
        descricao: '',
        questoes: [],
        dataCriacao: DateTime.now(),
        ultimaModificacao: DateTime.now(),
        classes: [_turmaId!],
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      ),
    );

    final turmaSelecionada = _turmas.firstWhere(
      (turma) => turma.id == _turmaId,
      orElse: () => ClassModel(
        id: _turmaId!,
        name: 'Turma Desconhecida',
        description: '',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      ),
    );

    developer.log(
        'Navegando para TelaInicial com: Turma=$_turmaId (${turmaSelecionada.name}), Simulado=$_simuladoId (${simuladoSelecionado.titulo}), Aluno=$_alunoId (${alunoSelecionado.name})');

    final alunoMap = {
      'id': alunoSelecionado.id,
      'nome': alunoSelecionado.name,
    };

    final simuladoMap = {
      'id': simuladoSelecionado.id,
      'titulo': simuladoSelecionado.titulo,
    };

    final turmaMap = {
      'id': turmaSelecionada.id,
      'nome': turmaSelecionada.name,
    };

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TelaInicial(
          turmaId: _turmaId!,
          simuladoId: _simuladoId!,
          alunoId: _alunoId!,
          aluno: alunoMap,
          simulado: simuladoMap,
          turma: turmaMap,
        ),
      ),
    );
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
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error, color: Colors.white),
                const SizedBox(width: 8),
                Text('Erro ao fazer logout: $e'),
              ],
            ),
            backgroundColor: dangerColor,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        );
      }
    }
  }

  Future<void> _recarregarDados() async {
    _resetSelections();
    await _verificarConexao();
  }

  void _resetSelections() {
    setState(() {
      _turmaId = null;
      _simuladoId = null;
      _alunoId = null;
      _simulados = [];
      _alunos = [];
    });
  }

  @override
  Widget build(BuildContext context) {
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
                Icons.display_settings,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'SimuladoApp',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 20,
                color: textLight,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Recarregar',
            onPressed: _recarregarDados,
            color: textMuted,
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Sair',
            onPressed: _logout,
            color: textMuted,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            height: 1,
            color: borderColor,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 48,
                    height: 48,
                    child: CircularProgressIndicator(
                      strokeWidth: 3,
                      valueColor: AlwaysStoppedAnimation<Color>(primaryColor),
                      backgroundColor: borderColor,
                    ),
                  ),
                  SizedBox(height: 24),
                  Text(
                    'Carregando dados...',
                    style: TextStyle(
                      fontSize: 16,
                      color: textMuted,
                    ),
                  ),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: _recarregarDados,
              color: primaryColor,
              backgroundColor: bgSurface,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Header com boas-vindas
                      Container(
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
                                        'Bem-vindo(a),',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 14,
                                        ),
                                      ),
                                      Text(
                                        userName,
                                        style: const TextStyle(
                                          color: textLight,
                                          fontSize: 20,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Selecione a turma, simulado e aluno para iniciar a correção',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 24),

                      // Card com formulário de seleção
                      Container(
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
                          crossAxisAlignment: CrossAxisAlignment.start,
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
                                    Icons.settings_outlined,
                                    color: Colors.white,
                                    size: 20,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                const Text(
                                  'Configurações da Correção',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: primaryColor,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 24),

                            // Dropdown Turma
                            _buildDropdown(
                              label: 'Turma',
                              hint: 'Selecione uma turma',
                              value: _turmaId,
                              icon: Icons.group_outlined,
                              items: _turmas.map((turma) {
                                return DropdownMenuItem<int>(
                                  value: turma.id,
                                  child: Text(turma.name,
                                      style: const TextStyle(color: textLight)),
                                );
                              }).toList(),
                              onChanged: _onTurmaChanged,
                            ),

                            const SizedBox(height: 16),

                            // Dropdown Simulado
                            _buildDropdown(
                              label: 'Simulado',
                              hint: _turmaId == null
                                  ? 'Selecione uma turma primeiro'
                                  : 'Selecione um simulado',
                              value: _simuladoId,
                              icon: Icons.quiz_outlined,
                              items: _simulados.map((simulado) {
                                return DropdownMenuItem<int>(
                                  value: simulado.id,
                                  child: Text(simulado.titulo,
                                      style: const TextStyle(color: textLight)),
                                );
                              }).toList(),
                              onChanged: _simulados.isEmpty
                                  ? null
                                  : _onSimuladoChanged,
                              disabledHint: _turmaId == null
                                  ? 'Selecione uma turma primeiro'
                                  : _isLoading
                                      ? 'Carregando simulados...'
                                      : 'Nenhum simulado disponível',
                            ),

                            const SizedBox(height: 16),

                            // Dropdown Aluno
                            _buildDropdown(
                              label: 'Aluno',
                              hint: _turmaId == null
                                  ? 'Selecione uma turma primeiro'
                                  : 'Selecione um aluno',
                              value: _alunoId,
                              icon: Icons.person_outline,
                              items: _alunos.map((aluno) {
                                return DropdownMenuItem<int>(
                                  value: aluno.id,
                                  child: Text(aluno.name,
                                      style: const TextStyle(color: textLight)),
                                );
                              }).toList(),
                              onChanged:
                                  _alunos.isEmpty ? null : _onAlunoChanged,
                              disabledHint: _turmaId == null
                                  ? 'Selecione uma turma primeiro'
                                  : _isLoading
                                      ? 'Carregando alunos...'
                                      : 'Nenhum aluno disponível',
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 16),

                      // Mensagem de erro
                      if (_errorMessage.isNotEmpty)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: dangerColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: dangerColor, width: 1),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(
                                    Icons.error_outline,
                                    color: dangerColor,
                                    size: 20,
                                  ),
                                  SizedBox(width: 8),
                                  Text(
                                    'Erro',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: dangerColor,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _errorMessage,
                                style: const TextStyle(
                                  color: dangerColor,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 12),
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton.icon(
                                  onPressed: _recarregarDados,
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Tentar Novamente'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor:
                                        dangerColor.withOpacity(0.2),
                                    foregroundColor: dangerColor,
                                    side: const BorderSide(color: dangerColor),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                      const SizedBox(height: 24),

                      // Botão continuar
                      SizedBox(
                        height: 56,
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: (_isLoading ||
                                    _turmaId == null ||
                                    _simuladoId == null ||
                                    _alunoId == null)
                                ? null
                                : _continuarParaLeitor,
                            borderRadius: BorderRadius.circular(4),
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: (_isLoading ||
                                        _turmaId == null ||
                                        _simuladoId == null ||
                                        _alunoId == null)
                                    ? null
                                    : const LinearGradient(
                                        colors: [secondaryColor, primaryColor],
                                        begin: Alignment.centerLeft,
                                        end: Alignment.centerRight,
                                      ),
                                color: (_isLoading ||
                                        _turmaId == null ||
                                        _simuladoId == null ||
                                        _alunoId == null)
                                    ? borderColor
                                    : null,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              alignment: Alignment.center,
                              child: _isLoading
                                  ? const SizedBox(
                                      width: 24,
                                      height: 24,
                                      child: CircularProgressIndicator(
                                        color: textLight,
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.camera_alt_outlined,
                                            size: 20, color: Colors.white),
                                        SizedBox(width: 8),
                                        Text(
                                          'Continuar para Leitura',
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                            color: Colors.white,
                                            letterSpacing: 0.5,
                                          ),
                                        ),
                                      ],
                                    ),
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required String hint,
    required int? value,
    required IconData icon,
    required List<DropdownMenuItem<int>> items,
    required void Function(int?)? onChanged,
    String? disabledHint,
  }) {
    return DropdownButtonFormField<int>(
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: textMuted),
        hintText: hint,
        hintStyle: const TextStyle(color: textMuted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: primaryColor, width: 2),
        ),
        filled: true,
        fillColor: bgDark,
        prefixIcon: Icon(icon, color: primaryColor),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      value: value,
      isExpanded: true,
      style: const TextStyle(color: textLight),
      dropdownColor: bgSurface,
      items: items,
      onChanged: onChanged,
      disabledHint: disabledHint != null
          ? Text(disabledHint, style: const TextStyle(color: textMuted))
          : null,
    );
  }
}
