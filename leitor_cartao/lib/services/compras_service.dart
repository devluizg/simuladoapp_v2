import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'models/produto_credito.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:developer' as developer;

class ComprasService {
  static const String baseUrl = 'https://simuladoapp.com.br/api/';

  // IDs dos produtos que serão cadastrados no Google Play Console
  static const List<String> produtoIds = [
    'starter_300_creditos',
    'professor_ativo_800_creditos',
    'escola_pequena_2000_creditos',
    'escola_profissional_5000_creditos',
  ];

  final InAppPurchase _inAppPurchase = InAppPurchase.instance;
  late StreamSubscription<List<PurchaseDetails>> _subscription;

  List<ProductDetails> _produtos = [];
  List<ProdutoCredito> _produtosCredito = [];

  // Callbacks para notificar a UI
  Function(int creditos)? onCompraSucesso;
  Function(String erro)? onCompraErro;
  Function(String status)? onCompraStatus;

  // Getters
  List<ProductDetails> get produtos => _produtos;
  List<ProdutoCredito> get produtosCredito => _produtosCredito;

  ComprasService() {
    _inicializarCompras();
  }

  Future<void> _inicializarCompras() async {
    final bool isAvailable = await _inAppPurchase.isAvailable();
    if (!isAvailable) {
      _log('❌ InAppPurchase não disponível na inicialização');
      throw Exception('Loja não disponível');
    }

    _subscription = _inAppPurchase.purchaseStream.listen(
      _onPurchaseUpdated,
      onError: (error) {
        _log('Erro no stream de compras: $error');
        onCompraErro?.call('Erro no stream de compras: $error');
      },
    );
  }

  // MÉTODO PRINCIPAL DE DIAGNÓSTICO
  Future<void> debugInAppPurchase() async {
    _log('🔍 ===== DIAGNÓSTICO COMPLETO =====');
    _log('📱 Platform: ${Platform.operatingSystem}');
    _log('🔑 Is Debug: $kDebugMode');
    _log('📦 Package Name: ${await _getPackageName()}');
    _log('🏗️ Build Mode: ${kDebugMode ? "DEBUG" : "RELEASE"}');

    final bool isAvailable = await _inAppPurchase.isAvailable();
    _log('✅ InAppPurchase disponível: $isAvailable');

    if (!isAvailable) {
      _log('❌ MOTIVOS POSSÍVEIS PARA INDISPONIBILIDADE:');
      _log('   1. App não está na Google Play Store');
      _log('   2. Conta não é tester licenciado');
      _log('   3. Produtos não estão configurados no Play Console');
      _log('   4. Região não suportada');
      _log('   5. Versão do app não foi publicada');
      return;
    }

    await carregarProdutos();
  }

  Future<void> carregarProdutos() async {
    try {
      _log('🔍 Iniciando carregamento de produtos...');
      _log('📱 Package Name: ${await _getPackageName()}');
      _log('🔑 Build Mode: ${kDebugMode ? "DEBUG" : "RELEASE"}');

      // ✅ Verificar conectividade primeiro
      final connectivityResult = await Connectivity().checkConnectivity();
      if (connectivityResult == ConnectivityResult.none) {
        _log('❌ Sem conexão com a internet');
        throw Exception(
            'Sem conexão com a internet. Verifique sua conexão e tente novamente.');
      }
      _log('✅ Conectividade OK: $connectivityResult');

      // Verificar se InAppPurchase está disponível
      final bool isAvailable = await _inAppPurchase.isAvailable();
      if (!isAvailable) {
        _log('❌ InAppPurchase não disponível');
        _log('❌ POSSÍVEIS CAUSAS:');
        _log('   - App não está na Google Play Store');
        _log('   - Conta não é tester licenciado');
        _log('   - Produtos não estão ativos no Play Console');
        _log('   - Versão não foi publicada');
        throw Exception('Loja não disponível');
      }
      _log('✅ InAppPurchase disponível');

      // Log dos IDs que estamos buscando
      _log('🔍 Buscando produtos com IDs: $produtoIds');

      // Buscar produtos do Google Play
      final ProductDetailsResponse response =
          await _inAppPurchase.queryProductDetails(
        produtoIds.toSet(),
      );

      _log('📦 Resposta da consulta recebida');
      _log('❌ Produtos não encontrados: ${response.notFoundIDs}');
      _log('✅ Produtos encontrados: ${response.productDetails.length}');

      // Log mais detalhado dos produtos não encontrados
      if (response.notFoundIDs.isNotEmpty) {
        _log('🚨 PRODUTOS NÃO ENCONTRADOS:');
        for (final id in response.notFoundIDs) {
          _log('   ❌ $id - VERIFICAR SE ESTÁ ATIVO NO PLAY CONSOLE');
        }
        _log('🔧 AÇÕES NECESSÁRIAS:');
        _log('   1. Verificar se produtos estão com status "Ativo"');
        _log('   2. Verificar se IDs estão corretos');
        _log('   3. Aguardar até 2 horas após criação');
        _log('   4. Verificar se app foi publicado');
      }

      // Log detalhado dos produtos encontrados
      for (final product in response.productDetails) {
        _log('📱 Produto encontrado: ${product.id}');
        _log('   📝 Título: ${product.title}');
        _log('   💰 Preço: ${product.price}');
        _log('   📄 Descrição: ${product.description}');
        _log('   🏷️ Preço formatado: ${product.rawPrice}');
      }

      if (response.error != null) {
        _log('❌ Erro na resposta: ${response.error?.message}');
        _log('❌ Código do erro: ${response.error?.code}');
        _log('❌ Detalhes do erro: ${response.error?.details}');
        throw Exception(
            'Erro ao carregar produtos: ${response.error?.message}');
      }

      _produtos = response.productDetails;
      _log('✅ ${_produtos.length} produtos carregados com sucesso');

      // Mapear para produtos de crédito com informações locais
      _produtosCredito = _produtos.map((product) {
        final produtoCredito = _mapearProdutoCredito(product);
        _log(
            '🎯 Mapeado: ${produtoCredito.nome} - ${produtoCredito.creditos} créditos - ${produtoCredito.preco}');
        return produtoCredito;
      }).toList();

      _log(
          '🎉 Carregamento concluído! ${_produtosCredito.length} produtos de crédito disponíveis');

      // Log final de resumo
      _log('📊 RESUMO FINAL:');
      _log('   📱 Produtos disponíveis: ${_produtosCredito.length}');
      _log('   ❌ Produtos não encontrados: ${response.notFoundIDs.length}');
      _log('   ✅ Sistema funcionando: ${_produtosCredito.isNotEmpty}');
    } catch (e) {
      _log('💥 ERRO COMPLETO ao carregar produtos: $e');
      _log('💥 Stack trace: ${StackTrace.current}');
      rethrow;
    }
  }

  ProdutoCredito _mapearProdutoCredito(ProductDetails product) {
    // Mapear IDs dos produtos para informações locais
    switch (product.id) {
      case 'starter_300_creditos':
        return ProdutoCredito(
          id: product.id,
          nome: 'Starter',
          creditos: 300,
          preco: product.price,
          descricao: '300 correções incluídas',
        );
      case 'professor_ativo_800_creditos':
        return ProdutoCredito(
          id: product.id,
          nome: 'Professor Ativo',
          creditos: 800,
          preco: product.price,
          descricao: '800 correções incluídas',
        );
      case 'escola_pequena_2000_creditos':
        return ProdutoCredito(
          id: product.id,
          nome: 'Escola Pequena',
          creditos: 2000,
          preco: product.price,
          descricao: '2000 correções incluídas',
        );
      case 'escola_profissional_5000_creditos':
        return ProdutoCredito(
          id: product.id,
          nome: 'Escola Profissional',
          creditos: 5000,
          preco: product.price,
          descricao: '5000 correções incluídas',
        );
      default:
        return ProdutoCredito(
          id: product.id,
          nome: product.title,
          creditos: 0,
          preco: product.price,
          descricao: product.description,
        );
    }
  }

  Future<void> comprarProduto(ProductDetails produto) async {
    try {
      _log('🛒 Iniciando compra do produto: ${produto.id}');
      onCompraStatus?.call('Iniciando compra...');

      final PurchaseParam purchaseParam = PurchaseParam(
        productDetails: produto,
      );

      _log('🛒 Executando buyConsumable...');
      await _inAppPurchase.buyConsumable(purchaseParam: purchaseParam);
      _log('🛒 buyConsumable executado com sucesso');
    } catch (e) {
      _log('💥 Erro ao iniciar compra: $e');
      onCompraErro?.call('Erro ao iniciar compra: $e');
      rethrow;
    }
  }

  void _onPurchaseUpdated(List<PurchaseDetails> purchaseDetailsList) {
    _log(
        '🔄 Recebida atualização de compras: ${purchaseDetailsList.length} itens');
    for (final PurchaseDetails purchaseDetails in purchaseDetailsList) {
      _log(
          '🔄 Processando compra: ${purchaseDetails.productID} - Status: ${purchaseDetails.status}');
      _handlePurchase(purchaseDetails);
    }
  }

  Future<void> _handlePurchase(PurchaseDetails purchaseDetails) async {
    _log(
        '🔄 Handling purchase: ${purchaseDetails.productID} - ${purchaseDetails.status}');

    if (purchaseDetails.status == PurchaseStatus.purchased) {
      _log('✅ Compra bem-sucedida: ${purchaseDetails.productID}');
      onCompraStatus?.call('Processando compra...');
      await _processarCompraSucesso(purchaseDetails);
    } else if (purchaseDetails.status == PurchaseStatus.error) {
      final errorMessage = 'Erro na compra: ${purchaseDetails.error?.message}';
      _log('❌ $errorMessage');
      onCompraErro?.call(errorMessage);
    } else if (purchaseDetails.status == PurchaseStatus.canceled) {
      const cancelMessage = 'Compra cancelada pelo usuário';
      _log('⏹️ $cancelMessage');
      onCompraStatus?.call(cancelMessage);
    } else if (purchaseDetails.status == PurchaseStatus.pending) {
      const pendingMessage = 'Compra pendente';
      _log('⏳ $pendingMessage');
      onCompraStatus?.call(pendingMessage);
    }

    if (purchaseDetails.pendingCompletePurchase) {
      _log('🔄 Completando compra...');
      await _inAppPurchase.completePurchase(purchaseDetails);
      _log('✅ Compra completada');
    }
  }

  Future<void> _processarCompraSucesso(PurchaseDetails purchaseDetails) async {
    try {
      _log('🎉 Processando compra bem-sucedida: ${purchaseDetails.productID}');

      // Encontrar o produto comprado
      final produto = _produtosCredito.firstWhere(
        (p) => p.id == purchaseDetails.productID,
        orElse: () => ProdutoCredito(
          id: purchaseDetails.productID,
          nome: 'Produto Desconhecido',
          creditos: 0,
        ),
      );

      _log(
          '🎯 Produto encontrado: ${produto.nome} - ${produto.creditos} créditos');

      // Enviar para o backend para validação
      await _validarCompraNoBackend(purchaseDetails, produto);
    } catch (e) {
      _log('💥 Erro ao processar compra: $e');
      onCompraErro?.call('Erro ao processar compra: $e');
      rethrow;
    }
  }

  Future<void> _validarCompraNoBackend(
      PurchaseDetails purchaseDetails, ProdutoCredito produto) async {
    try {
      _log('🔍 Validando compra no backend...');

      final token = await _getAuthToken();
      if (token.isEmpty) {
        throw Exception('Token de autenticação não encontrado');
      }

      final response = await http.post(
        Uri.parse('$baseUrl/comprar_creditos/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'produto_id': produto.id,
          'creditos': produto.creditos,
          'purchase_token':
              purchaseDetails.verificationData.serverVerificationData,
          'transaction_id': purchaseDetails.purchaseID,
          'plataforma': Platform.isAndroid ? 'android' : 'ios',
        }),
      );

      _log('📡 Resposta do backend: ${response.statusCode}');
      _log('📡 Corpo da resposta: ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        _log('✅ Compra validada com sucesso: ${responseData['message']}');
        _notificarCompraSucesso(produto.creditos);
      } else {
        throw Exception('Erro ao validar compra: ${response.body}');
      }
    } catch (e) {
      _log('💥 Erro ao validar compra no backend: $e');
      onCompraErro?.call('Erro ao validar compra no backend: $e');
      rethrow;
    }
  }

  Future<String> _getAuthToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token') ?? '';
      _log('🔑 Token obtido: ${token.isNotEmpty ? "✅ Presente" : "❌ Ausente"}');
      return token;
    } catch (e) {
      _log('💥 Erro ao obter token: $e');
      return '';
    }
  }

  Future<String> _getPackageName() async {
    try {
      final PackageInfo packageInfo = await PackageInfo.fromPlatform();
      return packageInfo.packageName;
    } catch (e) {
      return 'Erro ao obter package name';
    }
  }

  void _notificarCompraSucesso(int creditos) {
    _log('🎉 Compra finalizada com sucesso! $creditos créditos adicionados.');
    onCompraSucesso?.call(creditos);
  }

  void _log(String message) {
    developer.log(message, name: '🛒 ComprasService');
    if (kDebugMode) {
      print('🛒 ComprasService: $message');
    }
  }

  void dispose() {
    _subscription.cancel();
  }
}
