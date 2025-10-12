import pandas as pd
from io import BytesIO
import PyPDF2
import re
import unicodedata
import logging

# Configurar logging para debug
logger = logging.getLogger(__name__)

def normalize_name(name):
    """
    Normaliza um nome removendo caracteres indesejados e formatando adequadamente.
    """
    if not name or not isinstance(name, str):
        return None

    # Remover caracteres numéricos e especiais no início e fim
    name = re.sub(r'^[\d\W]+|[\d\W]+$', '', name.strip())

    # Remover múltiplos espaços
    name = re.sub(r'\s+', ' ', name)

    # Capitalizar cada palavra (formato de nome próprio)
    name = ' '.join(word.capitalize() for word in name.split())

    # Verificar comprimento mínimo após limpeza
    if len(name) < 3:
        return None

    # Normalizar acentos e caracteres especiais
    try:
        # Preservar acentos para ordem alfabética correta
        name = unicodedata.normalize('NFC', name)
    except:
        pass  # Se falhar a normalização, mantém o nome original

    return name

def extract_students_from_pdf(pdf_file):
    """
    Extrai nomes de alunos de um arquivo PDF usando regras melhoradas de extração.
    Retorna a lista ordenada alfabeticamente por nome.

    Args:
        pdf_file: Arquivo PDF carregado

    Returns:
        Lista de dicionários com dados dos alunos (nome e email) em ordem alfabética
    """
    students = []
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Diferentes padrões para capturar nomes de alunos
        patterns = [
            # Padrão 1: Número seguido de nome (comum em listas de chamada)
            r'(?:^|\n)(?:\d+\.?\s+)([A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]+(?:\s+[A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]*){0,5})',

            # Padrão 2: Nome seguido de matrícula ou número
            r'([A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]+(?:\s+[A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]*){1,5})\s*(?:[\d-]+|$)',

            # Padrão 3: Nome seguido de tabulação ou múltiplos espaços e depois informações adicionais
            r'([A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]+(?:\s+[A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]*){1,5})(?:\t|\s{2,})',

            # Padrão 4: Linha iniciando por nome
            r'(?:^|\n)([A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]+(?:\s+[A-ZÀ-ÚÇ][A-ZÀ-ÚÇa-zà-úç\s]*){1,5})(?:$|\n|\t)',
        ]

        text_with_line_breaks = ""

        # Extrair o texto de todas as páginas
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_with_line_breaks += page_text + "\n"

        # Aplicar cada padrão ao texto completo
        potential_names = set()

        for pattern in patterns:
            matches = re.finditer(pattern, text_with_line_breaks)
            for match in matches:
                raw_name = match.group(1).strip()
                if raw_name:
                    # Diversos filtros para eliminar linhas que não são nomes
                    if (len(raw_name) > 3 and
                        " " in raw_name and  # Nome deve ter pelo menos duas palavras
                        not re.search(r'(?:ALUNO|NOME|MATRICUL|LISTA|PROFESSOR|TURMA|ESCOLA|CURSO|DISCIPLINA|TOTAL)$', raw_name, re.IGNORECASE) and
                        not re.match(r'^\d+$', raw_name)):  # Não deve ser apenas números

                        # Verificar se o texto possui pelo menos uma letra
                        if any(c.isalpha() for c in raw_name):
                            potential_names.add(raw_name)

        # Lista negra de palavras que geralmente não fazem parte de nomes
        blacklist = [
            "total", "alunos", "pagina", "página", "classe", "escola", "turma",
            "matricula", "matrícula", "ensino", "fundamental", "médio", "medio",
            "professor", "professora", "coordenador", "diretor", "disciplina"
        ]

        # Processar nomes potenciais
        normalized_names = []
        for name in potential_names:
            # Verificar se o nome não contém palavras da lista negra
            if not any(word.lower() in name.lower() for word in blacklist):
                # Normalizar e adicionar à lista se válido
                normalized_name = normalize_name(name)
                if normalized_name and len(normalized_name.split()) >= 2:  # Garantir pelo menos nome e sobrenome
                    normalized_names.append(normalized_name)

        # Remover duplicatas e ordenar alfabeticamente (ignorando case)
        normalized_names = sorted(set(normalized_names), key=lambda x: x.lower())

        # Criar a lista final de estudantes em ordem alfabética
        for name in normalized_names:
            students.append({
                'name': name,
                'email': None  # PDF normalmente não terá email
            })

        logger.info(f"Extração PDF: Encontrados {len(students)} alunos ordenados alfabeticamente")

    except Exception as e:
        logger.error(f"Erro ao extrair alunos do PDF: {str(e)}")

    return students

def extract_students_from_excel(excel_file):
    """
    Extrai nomes de alunos de um arquivo Excel com melhor detecção de colunas.
    Retorna a lista ordenada alfabeticamente por nome.

    Args:
        excel_file: Arquivo Excel carregado

    Returns:
        Lista de dicionários com dados dos alunos (nome e email) em ordem alfabética
    """
    students_data = []
    try:
        # Tentar diferentes engines para garantir compatibilidade
        try:
            df = pd.read_excel(excel_file, engine='openpyxl')
        except:
            try:
                df = pd.read_excel(excel_file, engine='xlrd')
            except:
                df = pd.read_excel(excel_file)

        # Remover linhas completamente vazias
        df.dropna(how='all', inplace=True)

        # Função para detectar probabilidade de uma coluna conter nomes
        def is_name_column(col_values):
            """Determina se uma coluna provavelmente contém nomes"""
            # Converter valores para string e eliminar NaN
            values = [str(v).strip() for v in col_values if pd.notna(v) and str(v).strip()]
            if not values:
                return 0

            # Pontuação para determinar se é uma coluna de nomes
            score = 0

            # Verificar proporção de valores que seguem padrão de nome
            name_pattern = re.compile(r'^[A-ZÀ-ÚÇ][a-zà-úç]+(?: [A-ZÀ-ÚÇ][a-zà-úç]+)+$')
            name_matches = sum(1 for v in values if name_pattern.match(v))
            name_ratio = name_matches / len(values) if values else 0

            # Palavras-chave comuns em cabeçalhos de nome
            name_keywords = ['nome', 'aluno', 'estudante', 'discente']

            # Verificar cabeçalho
            if col_values.name:
                header_name = str(col_values.name).lower()
                if any(keyword in header_name for keyword in name_keywords):
                    score += 5

            # Pontuação baseada na proporção de valores que parecem nomes
            score += name_ratio * 10

            # Pontuação para valores com múltiplas palavras (nomes geralmente têm)
            multi_word_ratio = sum(1 for v in values if ' ' in v) / len(values) if values else 0
            score += multi_word_ratio * 3

            # Pontuação para valores capitalizados (nomes geralmente são)
            capital_ratio = sum(1 for v in values if v and v[0].isupper()) / len(values) if values else 0
            score += capital_ratio * 2

            return score

        # Detectar coluna de nome
        name_column = None
        email_column = None

        # Calcular pontuação para cada coluna
        column_scores = [(col, is_name_column(df[col])) for col in df.columns]

        # Ordenar colunas por pontuação
        column_scores.sort(key=lambda x: x[1], reverse=True)

        # A coluna com maior pontuação é provavelmente a de nomes
        if column_scores and column_scores[0][1] > 3:  # Threshold mínimo
            name_column = column_scores[0][0]

        # Procurar coluna de email
        for col in df.columns:
            col_lower = str(col).lower()
            if 'email' in col_lower or 'e-mail' in col_lower:
                email_column = col
                break
            else:
                # Verificar se a coluna contém padrões de email
                if df[col].dtype == object:  # Apenas colunas de texto
                    values = [str(v).strip() for v in df[col] if pd.notna(v) and str(v).strip()]
                    if values and any('@' in v for v in values):
                        email_column = col
                        break

        # Se não encontrou nome_column, usar a primeira coluna de texto como fallback
        if name_column is None:
            for col in df.columns:
                if df[col].dtype == object:  # Verificar se é coluna de texto
                    potential_values = [str(v).strip() for v in df[col] if pd.notna(v) and str(v).strip()]
                    if potential_values and any(' ' in v for v in potential_values):  # Verificar se há valores com espaços (possíveis nomes)
                        name_column = col
                        break

        if name_column is None:
            raise ValueError("Não foi possível identificar a coluna com nomes de alunos")

        # Dicionário temporário para armazenar dados (nome -> dados)
        # Isso facilita a remoção de duplicatas
        students_dict = {}

        # Processar linhas
        for _, row in df.iterrows():
            raw_name = str(row[name_column]).strip() if pd.notna(row[name_column]) else ""

            # Pular linhas com cabeçalhos ou valores inválidos
            if (raw_name.lower() in ['nome', 'aluno', 'estudante', 'discente', 'nan', ''] or
                len(raw_name) < 3 or
                raw_name.isdigit()):
                continue

            # Normalizar o nome
            normalized_name = normalize_name(raw_name)
            if not normalized_name:
                continue

            # Processar email se disponível
            email = None
            if email_column and pd.notna(row[email_column]):
                email_value = str(row[email_column]).strip()
                if '@' in email_value and '.' in email_value:  # Validação simples de email
                    email = email_value

            # Armazenar no dicionário, evitando duplicatas
            # Se houver duplicata, manterá a primeira ocorrência
            if normalized_name.lower() not in {name.lower() for name in students_dict.keys()}:
                students_dict[normalized_name] = {
                    'name': normalized_name,
                    'email': email
                }

        # Ordenar alfabeticamente por nome (case-insensitive)
        # Primeiro, converter o dicionário para lista de tuplas (nome, dados)
        students_items = list(students_dict.items())
        # Depois, ordenar por nome em minúsculas
        students_items.sort(key=lambda x: x[0].lower())
        # Finalmente, extrair apenas os dados para a lista final
        students_data = [item[1] for item in students_items]

        logger.info(f"Extração Excel: Encontrados {len(students_data)} alunos ordenados alfabeticamente (coluna={name_column})")

    except Exception as e:
        logger.error(f"Erro ao extrair alunos do Excel: {str(e)}")
        raise ValueError(f"Erro ao processar arquivo Excel: {str(e)}")

    return students_data

def get_next_student_id(user):
    """Determina o próximo ID disponível para um novo aluno."""
    from classes.models import Student
    last_student = Student.objects.filter(user=user).order_by('-student_id').first()
    return (int(last_student.student_id) + 1) if last_student and last_student.student_id else 1