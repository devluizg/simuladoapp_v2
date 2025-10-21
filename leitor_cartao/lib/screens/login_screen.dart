import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'selection_screen.dart';

// Enum para ambientes
enum Environment { development, production }

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _customUrlController = TextEditingController();

  bool _isLoading = false;
  bool _isPasswordVisible = false;
  bool _useCustomUrl = false;
  String _errorMessage = '';
  String _successMessage = '';
  final ApiService _apiService = ApiService();
  Environment _selectedEnvironment = Environment.production;

  // Cores do tema
  static const Color primaryDark = Color(0xFF1E203A);
  static const Color secondaryDark = Color(0xFF121425);
  static const Color accentBlue = Color(0xFF4A9EFF);
  static const Color cardColor = Color(0xFF2A2D4A);
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB8BCCF);
  static const Color errorColor = Color(0xFFFF6B6B);
  static const Color successColor = Color(0xFF4CAF50);

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    await _loadEnvironment();
    await _loadCustomUrl();
    _updateApiUrl();
    // NÃO verificar conexão automaticamente no initState
    // Apenas verificar quando o usuário clicar em "Testar Conexão"
  }

  Future<void> _loadEnvironment() async {
    final prefs = await SharedPreferences.getInstance();
    final env = prefs.getString('environment') ?? 'production';
    final useCustom = prefs.getBool('use_custom_url') ?? false;

    setState(() {
      _selectedEnvironment = env == 'development'
          ? Environment.development
          : Environment.production;
      _useCustomUrl = useCustom;
    });
  }

  Future<void> _loadCustomUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final customUrl = prefs.getString('custom_url') ?? '';
    _customUrlController.text = customUrl;
  }

  Future<void> _saveEnvironment(Environment env) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('environment', env.name);
  }

  Future<void> _saveCustomUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('custom_url', url);
    await prefs.setBool('use_custom_url', _useCustomUrl);
  }

  void _updateApiUrl() {
    String url;

    if (_useCustomUrl && _customUrlController.text.isNotEmpty) {
      url = _customUrlController.text.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'http://$url';
      }
      debugPrint('App usando URL customizada: $url');
    } else if (_selectedEnvironment == Environment.development) {
      // Para Android Emulator, use 10.0.2.2
      // Para iOS Simulator, use localhost
      // Para dispositivo físico, use o IP da sua máquina (ex: 192.168.1.100)
      url = 'http://10.0.2.2:8000';
      debugPrint('App em modo desenvolvimento: $url');
    } else {
      url = 'https://simuladoapp.com.br';
      debugPrint('App em modo produção: $url');
    }

    _apiService.setBaseUrl(url);
  }

  Future<void> _checkConnection() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
      _successMessage = '';
    });

    try {
      bool isConnected = await _apiService.testConnection();

      if (!mounted) return;

      setState(() {
        _isLoading = false;
        if (isConnected) {
          _successMessage = 'Conectado ao servidor com sucesso!';
          _errorMessage = '';
        } else {
          _errorMessage =
              'Não foi possível conectar ao servidor. Verifique a URL e sua conexão.';
          _successMessage = '';
        }
      });

      // Limpar mensagem de sucesso após 3 segundos
      if (isConnected) {
        Future.delayed(const Duration(seconds: 3), () {
          if (mounted) {
            setState(() {
              _successMessage = '';
            });
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Erro ao testar conexão: $e';
        });
      }
    }
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = '';
      _successMessage = '';
    });

    try {
      final success = await _apiService.login(
        _usernameController.text.trim(),
        _passwordController.text,
      );

      if (success) {
        if (!mounted) return;

        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const SelectionScreen()),
        );
      } else {
        setState(() {
          _errorMessage = 'Credenciais inválidas ou assinatura inativa.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage =
            'Erro de conexão. Verifique a URL do servidor e tente novamente.';
      });
      debugPrint('Exception during login: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showConfigDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: cardColor,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              title: const Text(
                'Configurações de Servidor',
                style: TextStyle(color: textPrimary),
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Seletor de Ambiente
                    Row(
                      children: [
                        Text(
                          'Produção',
                          style: TextStyle(
                            color:
                                _selectedEnvironment == Environment.production
                                    ? textPrimary
                                    : textSecondary,
                            fontWeight:
                                _selectedEnvironment == Environment.production
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                          ),
                        ),
                        Switch(
                          value:
                              _selectedEnvironment == Environment.development,
                          onChanged: (value) {
                            setDialogState(() {
                              setState(() {
                                _selectedEnvironment = value
                                    ? Environment.development
                                    : Environment.production;
                                _useCustomUrl = false;
                              });
                            });
                          },
                          activeTrackColor: accentBlue.withOpacity(0.5),
                          activeColor: accentBlue,
                        ),
                        Text(
                          'Desenvolvimento',
                          style: TextStyle(
                            color:
                                _selectedEnvironment == Environment.development
                                    ? textPrimary
                                    : textSecondary,
                            fontWeight:
                                _selectedEnvironment == Environment.development
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),
                    const Divider(color: textSecondary),
                    const SizedBox(height: 20),

                    // URL Customizada
                    Row(
                      children: [
                        Checkbox(
                          value: _useCustomUrl,
                          onChanged: (value) {
                            setDialogState(() {
                              setState(() {
                                _useCustomUrl = value ?? false;
                              });
                            });
                          },
                          activeColor: accentBlue,
                        ),
                        const Expanded(
                          child: Text(
                            'Usar URL personalizada',
                            style: TextStyle(color: textPrimary),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 10),

                    if (_useCustomUrl)
                      TextField(
                        controller: _customUrlController,
                        style: const TextStyle(color: textPrimary),
                        decoration: InputDecoration(
                          hintText: 'Ex: 192.168.1.100:8000',
                          hintStyle:
                              TextStyle(color: textSecondary.withOpacity(0.7)),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide(
                                color: textSecondary.withOpacity(0.3)),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: accentBlue),
                          ),
                          filled: true,
                          fillColor: primaryDark.withOpacity(0.6),
                        ),
                      ),

                    const SizedBox(height: 20),

                    // Informações de ajuda
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: primaryDark.withOpacity(0.6),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Dicas de configuração:',
                            style: TextStyle(
                              color: accentBlue,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '• Android Emulator: 10.0.2.2:8000\n'
                            '• iOS Simulator: localhost:8000\n'
                            '• Dispositivo físico: IP_DA_MAQUINA:8000\n'
                            '• Exemplo: 192.168.1.100:8000',
                            style: TextStyle(
                              color: textSecondary,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                  child: const Text(
                    'Cancelar',
                    style: TextStyle(color: textSecondary),
                  ),
                ),
                ElevatedButton(
                  onPressed: () async {
                    await _saveEnvironment(_selectedEnvironment);
                    await _saveCustomUrl(_customUrlController.text.trim());
                    _updateApiUrl();
                    Navigator.of(context).pop();
                    // Testar conexão após salvar
                    await _checkConnection();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: accentBlue,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Salvar e Testar'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [secondaryDark, primaryDark],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Logo e título
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 40),
                      child: Column(
                        children: [
                          Container(
                            width: 120,
                            height: 120,
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [
                                  accentBlue.withOpacity(0.8),
                                  accentBlue.withOpacity(0.4),
                                ],
                              ),
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: accentBlue.withOpacity(0.3),
                                  blurRadius: 20,
                                  offset: const Offset(0, 10),
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.quiz_outlined,
                              size: 60,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 30),
                          const Text(
                            'SimuladoApp',
                            style: TextStyle(
                              fontSize: 36,
                              fontWeight: FontWeight.bold,
                              color: textPrimary,
                              letterSpacing: 2,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Faça login para continuar',
                            style: TextStyle(
                              fontSize: 16,
                              color: textSecondary,
                              fontWeight: FontWeight.w300,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),

                    // Card de login
                    Container(
                      padding: const EdgeInsets.all(28),
                      decoration: BoxDecoration(
                        color: cardColor.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: accentBlue.withOpacity(0.2),
                          width: 1,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.2),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          // Campo de usuário
                          TextFormField(
                            controller: _usernameController,
                            keyboardType: TextInputType.emailAddress,
                            style: const TextStyle(
                                color: textPrimary, fontSize: 16),
                            decoration: InputDecoration(
                              labelText: 'Email',
                              hintText: 'Digite seu Email',
                              labelStyle: const TextStyle(
                                  color: textSecondary, fontSize: 14),
                              hintStyle: TextStyle(
                                  color: textSecondary.withOpacity(0.7)),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide(
                                    color: textSecondary.withOpacity(0.3)),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide(
                                    color: textSecondary.withOpacity(0.3)),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: const BorderSide(
                                    color: accentBlue, width: 2),
                              ),
                              filled: true,
                              fillColor: primaryDark.withOpacity(0.6),
                              prefixIcon: const Icon(Icons.person_outline,
                                  color: textSecondary),
                              contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 20, vertical: 16),
                            ),
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Por favor, insira seu Email';
                              }
                              return null;
                            },
                          ),

                          const SizedBox(height: 20),

                          // Campo de senha
                          TextFormField(
                            controller: _passwordController,
                            obscureText: !_isPasswordVisible,
                            style: const TextStyle(
                                color: textPrimary, fontSize: 16),
                            decoration: InputDecoration(
                              labelText: 'Senha',
                              hintText: 'Digite sua senha',
                              labelStyle: const TextStyle(
                                  color: textSecondary, fontSize: 14),
                              hintStyle: TextStyle(
                                  color: textSecondary.withOpacity(0.7)),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide(
                                    color: textSecondary.withOpacity(0.3)),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide(
                                    color: textSecondary.withOpacity(0.3)),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: const BorderSide(
                                    color: accentBlue, width: 2),
                              ),
                              filled: true,
                              fillColor: primaryDark.withOpacity(0.6),
                              prefixIcon: const Icon(Icons.lock_outline,
                                  color: textSecondary),
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _isPasswordVisible
                                      ? Icons.visibility
                                      : Icons.visibility_off,
                                  color: textSecondary,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _isPasswordVisible = !_isPasswordVisible;
                                  });
                                },
                              ),
                              contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 20, vertical: 16),
                            ),
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Por favor, insira sua senha';
                              }
                              return null;
                            },
                          ),

                          const SizedBox(height: 24),

                          // Mensagem de sucesso
                          if (_successMessage.isNotEmpty)
                            Container(
                              margin: const EdgeInsets.only(bottom: 20),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: successColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                    color: successColor.withOpacity(0.3)),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.check_circle_outline,
                                      color: successColor, size: 22),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(
                                      _successMessage,
                                      style: const TextStyle(
                                        color: successColor,
                                        fontSize: 14,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),

                          // Mensagem de erro
                          if (_errorMessage.isNotEmpty)
                            Container(
                              margin: const EdgeInsets.only(bottom: 20),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: errorColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                    color: errorColor.withOpacity(0.3)),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.error_outline,
                                      color: errorColor, size: 22),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(
                                      _errorMessage,
                                      style: const TextStyle(
                                        color: errorColor,
                                        fontSize: 14,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),

                          // Botão de login
                          SizedBox(
                            width: double.infinity,
                            height: 56,
                            child: ElevatedButton(
                              onPressed: _isLoading ? null : _login,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: accentBlue,
                                foregroundColor: Colors.white,
                                disabledBackgroundColor:
                                    accentBlue.withOpacity(0.6),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                elevation: 0,
                              ),
                              child: _isLoading
                                  ? const SizedBox(
                                      width: 24,
                                      height: 24,
                                      child: CircularProgressIndicator(
                                        color: Colors.white,
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.login, size: 22),
                                        SizedBox(width: 12),
                                        Text(
                                          'Entrar',
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            letterSpacing: 0.5,
                                          ),
                                        ),
                                      ],
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Botão de configurações
                    OutlinedButton.icon(
                      onPressed: _showConfigDialog,
                      icon: const Icon(Icons.settings, size: 20),
                      label: const Text('Configurar Servidor'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: accentBlue,
                        side: BorderSide(color: accentBlue.withOpacity(0.5)),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Texto de rodapé
                    Text(
                      'Desenvolvido para SimuladoApp',
                      style: TextStyle(
                        color: textSecondary.withOpacity(0.6),
                        fontSize: 12,
                        fontWeight: FontWeight.w300,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _customUrlController.dispose();
    super.dispose();
  }
}
