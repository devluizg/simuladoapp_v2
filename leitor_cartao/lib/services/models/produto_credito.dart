class ProdutoCredito {
  final String id;
  final String nome;
  final int creditos;
  final String? preco;
  final String? descricao;

  ProdutoCredito({
    required this.id,
    required this.nome,
    required this.creditos,
    this.preco,
    this.descricao,
  });

  factory ProdutoCredito.fromJson(Map<String, dynamic> json) {
    return ProdutoCredito(
      id: json['id'],
      nome: json['nome'],
      creditos: json['creditos'],
      preco: json['preco'],
      descricao: json['descricao'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nome': nome,
      'creditos': creditos,
      'preco': preco,
      'descricao': descricao,
    };
  }

  @override
  String toString() {
    return 'ProdutoCredito(id: $id, nome: $nome, creditos: $creditos, preco: $preco)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ProdutoCredito && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
