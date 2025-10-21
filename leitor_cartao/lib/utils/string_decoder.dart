// lib/utils/string_decoder.dart

class StringDecoder {
  /// Decodifica caracteres especiais UTF-8 em strings
  static String decode(String? text) {
    if (text == null || text.isEmpty) {
      return '';
    }

    // Corrigir problemas comuns de codificação de caracteres em português
    return text
        // Caracteres com acentos
        .replaceAll('Ã£', 'ã')
        .replaceAll('Ã§', 'ç')
        .replaceAll('Ã©', 'é')
        .replaceAll('Ãª', 'ê')
        .replaceAll('Ã³', 'ó')
        .replaceAll('Ã¡', 'á')
        .replaceAll('Ã¢', 'â')
        .replaceAll('Ã\u0081', 'Á')
        .replaceAll('Ãµ', 'õ')
        .replaceAll('Ã´', 'ô')
        .replaceAll('Ãº', 'ú')
        .replaceAll('Ã­', 'í')
        .replaceAll('Ã‡', 'Ç')

        // Símbolos específicos
        .replaceAll('Â°', '°')
        .replaceAll('Âª', 'ª')
        .replaceAll('Âº', 'º')

        // Caso específico para "1ª"
        .replaceAll('1Âª', '1ª');
  }
}
