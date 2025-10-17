#questions/views.py
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.encoding import force_str
from .models import Questao, Simulado, QuestaoSimulado, VersaoGabarito
from .forms import QuestaoForm, SimuladoForm, QuestaoFilterForm
from django.db.models import Max
from django.db import transaction
from django.db import models
from .templatetags import custom_filters
import json
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML
import tempfile
from django.conf import settings
import os
import logging
from django.shortcuts import render
import traceback
from classes.models import Class
from django.core.cache import cache
import concurrent.futures
from PyPDF2 import PdfMerger
import time
import io
from django.utils import timezone
from .pdf_performance_logger import PerformanceTimer, time_function, perf_logger, log_file_size
import base64
import time
import zipfile
from django.http import Http404
import socket
import html
from django.db import models

logger = logging.getLogger(__name__)

def pagina_de_vendas(request):
    """Página inicial visível a todos"""
    return render(request, 'questions/pagina_de_vendas.html')

@login_required
def dashboard(request):
    """View para o dashboard principal do professor."""
    total_questoes = Questao.objects.filter(professor=request.user).count()
    total_simulados = Simulado.objects.filter(professor=request.user).count()
    ultimas_questoes = Questao.objects.filter(professor=request.user).order_by('-data_criacao')[:5]
    ultimos_simulados = Simulado.objects.filter(professor=request.user).order_by('-data_criacao')[:5]

    context = {
        'total_questoes': total_questoes,
        'total_simulados': total_simulados,
        'ultimas_questoes': ultimas_questoes,
        'ultimos_simulados': ultimos_simulados
    }
    return render(request, 'questions/questions_dashboard.html', context)

def normalizar_busca(texto):
    """
    Normaliza o texto de busca convertendo para HTML entities.
    Usa html.escape() do Python que é mais completo e confiável.
    """
    if not texto:
        return texto

    # O html.escape() converte automaticamente:
    # & -> &amp;
    # < -> &lt;
    # > -> &gt;
    # " -> &quot;
    # ' -> &#x27;
    texto_escapado = html.escape(texto, quote=True)

    # Mapa adicional para acentos e caracteres especiais do português
    # que o html.escape() não pega
    mapa_acentos = {
        'á': '&aacute;', 'à': '&agrave;', 'â': '&acirc;', 'ã': '&atilde;', 'ä': '&auml;',
        'é': '&eacute;', 'è': '&egrave;', 'ê': '&ecirc;', 'ë': '&euml;',
        'í': '&iacute;', 'ì': '&igrave;', 'î': '&icirc;', 'ï': '&iuml;',
        'ó': '&oacute;', 'ò': '&ograve;', 'ô': '&ocirc;', 'õ': '&otilde;', 'ö': '&ouml;',
        'ú': '&uacute;', 'ù': '&ugrave;', 'û': '&ucirc;', 'ü': '&uuml;',
        'ç': '&ccedil;', 'ñ': '&ntilde;',
        'Á': '&Aacute;', 'À': '&Agrave;', 'Â': '&Acirc;', 'Ã': '&Atilde;', 'Ä': '&Auml;',
        'É': '&Eacute;', 'È': '&Egrave;', 'Ê': '&Ecirc;', 'Ë': '&Euml;',
        'Í': '&Iacute;', 'Ì': '&Igrave;', 'Î': '&Icirc;', 'Ï': '&Iuml;',
        'Ó': '&Oacute;', 'Ò': '&Ograve;', 'Ô': '&Ocirc;', 'Õ': '&Otilde;', 'Ö': '&Ouml;',
        'Ú': '&Uacute;', 'Ù': '&Ugrave;', 'Û': '&Ucirc;', 'Ü': '&Uuml;',
        'Ç': '&Ccedil;', 'Ñ': '&Ntilde;',
        # Caracteres matemáticos e símbolos comuns
        '°': '&deg;', '±': '&plusmn;', '×': '&times;', '÷': '&divide;',
        '¹': '&sup1;', '²': '&sup2;', '³': '&sup3;',
        '½': '&frac12;', '¼': '&frac14;', '¾': '&frac34;',
        # Símbolos de moeda
        '¢': '&cent;', '£': '&pound;', '¥': '&yen;', '€': '&euro;',
        # Pontuação especial
        '–': '&ndash;', '—': '&mdash;',
        ''': '&lsquo;', ''': '&rsquo;', '"': '&ldquo;', '"': '&rdquo;',
        '«': '&laquo;', '»': '&raquo;',
        '…': '&hellip;',
        # Símbolos científicos
        'µ': '&micro;', '∞': '&infin;', '≈': '&asymp;', '≠': '&ne;',
        '≤': '&le;', '≥': '&ge;',
        # Outros símbolos úteis
        '§': '&sect;', '¶': '&para;', '©': '&copy;', '®': '&reg;',
        '™': '&trade;', '•': '&bull;',
    }

    for char, entity in mapa_acentos.items():
        texto_escapado = texto_escapado.replace(char, entity)

    return texto_escapado


def questao_list(request):
    """View otimizada com busca em HTML entities"""
    form = QuestaoFilterForm(request.GET)
    questoes = Questao.objects.filter(
        models.Q(professor=request.user) | models.Q(professor__isnull=True)
    )

    if form.is_valid():
        if form.cleaned_data.get('busca'):
            query = form.cleaned_data['busca'].strip()

            # Converter para HTML entities
            query_html = normalizar_busca(query)

            # Lista de campos para buscar
            campos = [
                'enunciado', 'alternativa_a', 'alternativa_b',
                'alternativa_c', 'alternativa_d', 'alternativa_e'
            ]

            # Construir Q objects dinamicamente
            q_objects = models.Q()
            for campo in campos:
                q_objects |= models.Q(**{f'{campo}__icontains': query})
                q_objects |= models.Q(**{f'{campo}__icontains': query_html})

            # Adicionar campos sem conversão HTML
            q_objects |= models.Q(disciplina__icontains=query)
            q_objects |= models.Q(conteudo__icontains=query)

            questoes = questoes.filter(q_objects)

        if form.cleaned_data.get('disciplina'):
            questoes = questoes.filter(disciplina__icontains=form.cleaned_data['disciplina'])

        if form.cleaned_data.get('conteudo'):
            questoes = questoes.filter(conteudo__icontains=form.cleaned_data['conteudo'])

        if form.cleaned_data.get('nivel_dificuldade'):
            questoes = questoes.filter(nivel_dificuldade=form.cleaned_data['nivel_dificuldade'])

    # Ordenação
    questoes = questoes.extra(
        select={'is_own': f"CASE WHEN professor_id = {request.user.id} THEN 0 ELSE 1 END"}
    ).order_by('is_own', '-data_criacao')

    # Paginação
    paginator = Paginator(questoes, 10)
    page = request.GET.get('page')
    questoes = paginator.get_page(page)

    # Carregar simulados
    arquivados_path = os.path.join(settings.BASE_DIR, 'arquivados.json')
    arquivado_ids = []
    if os.path.exists(arquivados_path):
        with open(arquivados_path, 'r', encoding='utf-8') as f:
            try:
                arquivado_ids = json.load(f)
            except json.JSONDecodeError:
                pass

    simulados = Simulado.objects.filter(professor=request.user).exclude(id__in=arquivado_ids)

    context = {
        'questoes': questoes,
        'form': form,
        'simulados': simulados,
    }
    return render(request, 'questions/questao_list.html', context)


# ============================================
# BONUS: Função para limpar o banco de dados
# ============================================

def decodificar_html_entities_no_banco():
    """
    Função utilitária para converter HTML entities de volta para caracteres normais.
    Execute uma vez se quiser limpar seus dados existentes.

    ATENÇÃO: Execute isso em um ambiente de desenvolvimento primeiro!
    """
    from questions.models import Questao

    questoes = Questao.objects.all()
    total = questoes.count()

    print(f"Processando {total} questões...")

    for i, questao in enumerate(questoes, 1):
        campos_atualizados = []

        # Lista de campos para decodificar
        campos = [
            'enunciado', 'alternativa_a', 'alternativa_b',
            'alternativa_c', 'alternativa_d', 'alternativa_e'
        ]

        for campo in campos:
            valor_original = getattr(questao, campo, None)
            if valor_original:
                # html.unescape() decodifica TODAS as HTML entities
                valor_decodificado = html.unescape(valor_original)
                if valor_decodificado != valor_original:
                    setattr(questao, campo, valor_decodificado)
                    campos_atualizados.append(campo)

        if campos_atualizados:
            questao.save()
            print(f"[{i}/{total}] Questão {questao.id} atualizada: {', '.join(campos_atualizados)}")

        if i % 100 == 0:
            print(f"Progresso: {i}/{total}")

    print("✅ Conversão concluída!")

@login_required
def questao_create(request):
    """View para criar uma nova questão."""
    if request.method == 'POST':
        form = QuestaoForm(request.POST, request.FILES)
        if form.is_valid():
            questao = form.save(commit=False)
            questao.professor = request.user

            if 'imagem' in request.FILES:
                imagem = request.FILES['imagem']
                if imagem.size > 5 * 1024 * 1024:  # 5MB
                    messages.error(request, 'A imagem deve ter no máximo 5MB.')
                    return render(request, 'questions/questao_form.html', {'form': form})

            try:
                questao.save()
                messages.success(request, 'Questão criada com sucesso!')
                return redirect('questions:questao_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = QuestaoForm()

    return render(request, 'questions/questao_form.html', {'form': form})

@login_required
@require_POST
@csrf_exempt
def adicionar_questao_simulado(request):
    try:
        data = json.loads(request.body)
        questao_id = data.get('questao_id')
        simulado_id = data.get('simulado_id')

        if not questao_id or not simulado_id:
            return JsonResponse({'success': False, 'error': 'IDs de questão e simulado são necessários.'}, status=400)

        # ✅ MODIFICADO: Buscar questão pública OU do usuário
        try:
            questao = Questao.objects.filter(
                models.Q(professor=request.user) | models.Q(professor__isnull=True)
            ).get(id=questao_id)
        except Questao.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Questão não encontrada ou sem permissão.'}, status=404)

        simulado = Simulado.objects.get(id=simulado_id, professor=request.user)

        # Verifica se a questão já está no simulado
        if QuestaoSimulado.objects.filter(simulado=simulado, questao=questao).exists():
            return JsonResponse({'success': False, 'error': 'Esta questão já está no simulado.'})

        with transaction.atomic():
            # Encontra a próxima ordem disponível
            max_ordem = QuestaoSimulado.objects.filter(simulado=simulado).aggregate(Max('ordem'))['ordem__max'] or 0
            proxima_ordem = max_ordem + 1

            # Cria a nova relação QuestaoSimulado
            QuestaoSimulado.objects.create(
                simulado=simulado,
                questao=questao,
                ordem=proxima_ordem
            )

        return JsonResponse({'success': True})

    except Simulado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Simulado não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def questao_update(request, pk):
    """View para atualizar uma questão existente."""
    questao = get_object_or_404(Questao, pk=pk)

    # ✅ CORRIGIDO: Proibir edição de questões públicas (exceto para staff)
    if questao.professor is None:  # Questão pública
        if not request.user.is_staff:
            messages.error(request, 'Questões públicas não podem ser editadas por usuários normais.')
            return redirect('questions:questao_list')
    elif questao.professor != request.user and not request.user.is_staff:  # Questão de outro usuário
        messages.error(request, 'Você não tem permissão para editar esta questão.')
        return redirect('questions:questao_list')

    if request.method == 'POST':
        form = QuestaoForm(request.POST, request.FILES, instance=questao)
        if form.is_valid():
            if 'imagem' in request.FILES:
                imagem = request.FILES['imagem']
                if imagem.size > 5 * 1024 * 1024:  # 5MB
                    messages.error(request, 'A imagem deve ter no máximo 5MB.')
                    return render(request, 'questions/questao_form.html', {'form': form, 'questao': questao})

            form.save()
            messages.success(request, 'Questão atualizada com sucesso!')
            return redirect('questions:questao_list')
    else:
        form = QuestaoForm(instance=questao)

    return render(request, 'questions/questao_form.html', {
        'form': form,
        'questao': questao
    })

@login_required
def questao_delete(request, pk):
    """View para excluir uma questão contornando o problema da tabela inexistente."""
    questao = get_object_or_404(Questao, pk=pk)

    # ✅ CORRIGIDO: Permitir exclusão de questões próprias OU questões públicas OU se for staff
    if questao.professor and questao.professor != request.user and not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para excluir esta questão.')
        return redirect('questions:questao_list')

    if request.method == 'POST':
        try:
            # Remover manualmente a imagem se existir
            if questao.imagem and hasattr(questao.imagem, 'path') and os.path.isfile(questao.imagem.path):
                os.remove(questao.imagem.path)

            # Excluir manualmente as relações primeiro
            from django.db import connection
            with connection.cursor() as cursor:
                # Remover primeiro as questões do simulado
                cursor.execute("DELETE FROM questions_questaosimulado WHERE questao_id = %s", [questao.id])
                # Agora remover a questão diretamente
                cursor.execute("DELETE FROM questions_questao WHERE id = %s", [questao.id])

            messages.success(request, 'Questão excluída com sucesso!')
            return redirect('questions:questao_list')
        except Exception as e:
            messages.error(request, f'Erro ao excluir questão: {str(e)}')
            return redirect('questions:questao_list')

    return render(request, 'questions/questao_confirm_delete.html', {
        'questao': questao
    })

@login_required
def simulado_list(request):
    """View para listar simulados."""
    import json
    import os
    from django.conf import settings

    # Caminho para o arquivo de simulados arquivados
    arquivados_path = os.path.join(settings.BASE_DIR, 'arquivados.json')

    arquivado_ids = []
    if os.path.exists(arquivados_path):
        with open(arquivados_path, 'r') as f:
            try:
                arquivado_ids = json.load(f)
            except json.JSONDecodeError:
                pass

    # Obter simulados do professor e excluir os arquivados
    simulados = Simulado.objects.filter(professor=request.user).exclude(id__in=arquivado_ids).order_by('-data_criacao')

    return render(request, 'questions/simulado_list.html', {
        'simulados': simulados
    })

@login_required
def archived_simulado_list(request):
    """View para listar simulados arquivados."""
    import json
    import os
    from django.conf import settings

    arquivados_path = os.path.join(settings.BASE_DIR, 'arquivados.json')
    arquivado_ids = []
    if os.path.exists(arquivados_path):
        with open(arquivados_path, 'r') as f:
            try:
                arquivado_ids = json.load(f)
            except json.JSONDecodeError:
                pass

    simulados = Simulado.objects.filter(professor=request.user, id__in=arquivado_ids).order_by('-data_criacao')

    return render(request, 'questions/archived_simulado_list.html', {
        'simulados': simulados
    })

@login_required
def simulado_create(request):
    if request.method == 'POST':
        form = SimuladoForm(request.POST, user=request.user)
        if form.is_valid():
            simulado = form.save(commit=False)
            simulado.professor = request.user
            simulado.save()

            # Salvar as turmas selecionadas
            turmas = form.cleaned_data['turmas']
            simulado.classes.set(turmas)

            messages.success(request, 'Simulado criado com sucesso!')
            return redirect('questions:simulado_edit', pk=simulado.pk)
    else:
        form = SimuladoForm(user=request.user)

    context = {
        'form': form,
        'titulo': 'Novo Simulado'
    }
    return render(request, 'questions/simulado_form.html', context)


@login_required
def simulado_edit(request, pk):
    """View para editar um simulado existente."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    questoes_selecionadas = simulado.questoes.all().order_by('questaosimulado__ordem')

    # ✅ MODIFICADO: Incluir questões públicas + questões do usuário
    questoes_disponiveis = Questao.objects.filter(
        models.Q(professor=request.user) | models.Q(professor__isnull=True)
    ).exclude(
        id__in=questoes_selecionadas.values_list('id', flat=True)
    ).extra(
        select={'is_own': f"CASE WHEN professor_id = {request.user.id} THEN 0 ELSE 1 END"}
    ).order_by('is_own', 'disciplina', 'conteudo')

    if request.method == 'POST':
        form = SimuladoForm(request.POST, instance=simulado, user=request.user)
        if form.is_valid():
            simulado = form.save()

            # Atualizar as turmas selecionadas
            if 'turmas' in form.cleaned_data:
                turmas = form.cleaned_data['turmas']
                simulado.classes.set(turmas)

            messages.success(request, 'Simulado atualizado com sucesso!')
            return redirect('questions:simulado_list')
    else:
        form = SimuladoForm(instance=simulado, user=request.user)

    context = {
        'form': form,
        'simulado': simulado,
        'questoes_selecionadas': questoes_selecionadas,
        'questoes_disponiveis': questoes_disponiveis
    }

    return render(request, 'questions/simulado_edit.html', context)


@login_required
@require_POST
def simulado_delete(request, pk):
    """View para excluir um simulado."""
    try:
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)
        simulado.delete()

        return JsonResponse({
            'success': True,
            'message': 'Simulado excluído com sucesso!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def simulado_detail(request, pk):
    """View simplificada para exibir detalhes de um simulado."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # Buscar questões ordenadas
    questoes = simulado.questoes.all().order_by('questaosimulado__ordem')

    # Buscar histórico de gabaritos apenas para exibição
    historico_gabaritos = simulado.get_historico_gabaritos()
    total_versoes = simulado.get_total_versoes_gabarito()

    # ✅ CORREÇÃO PRINCIPAL - Usar versão OFICIAL ao invés da última gerada
    versoes = []
    gabaritos_processados = []
    versao_oficial = None

    # Obter a versão oficial do gabarito
    if simulado.versao_gabarito_oficial:
        versao_oficial = simulado.versao_gabarito_oficial
        print(f"DEBUG - Exibindo versão oficial: {versao_oficial.get_versao_curta()}")
    elif historico_gabaritos.exists():
        # Fallback: se não há oficial, usar a mais recente
        versao_oficial = historico_gabaritos.first()
        print(f"DEBUG - Sem versão oficial, usando mais recente: {versao_oficial.get_versao_curta()}")

    if versao_oficial and versao_oficial.gabaritos_gerados:
        try:
            # Processar os gabaritos da versão OFICIAL
            for versao_data in versao_oficial.gabaritos_gerados[:5]:
                if isinstance(versao_data, dict) and 'gabarito' in versao_data:
                    versoes.append(versao_data)

            # Obter todas as questões do gabarito oficial
            todas_questoes = set()
            for versao in versao_oficial.gabaritos_gerados:
                if isinstance(versao, dict) and 'gabarito' in versao:
                    todas_questoes.update(versao['gabarito'].keys())

            # Converter para lista e ordenar
            todas_questoes = sorted(list(todas_questoes), key=lambda x: int(x))

            # Para cada questão, obter as respostas em cada versão
            for questao_idx in todas_questoes:
                row = {'questao_idx': int(questao_idx)}

                # Para cada versão
                for i, versao_data in enumerate(versao_oficial.gabaritos_gerados[:5]):
                    if isinstance(versao_data, dict) and 'gabarito' in versao_data:
                        gabarito = versao_data['gabarito']
                        if questao_idx in gabarito:
                            questao_data = gabarito[questao_idx]
                            if isinstance(questao_data, dict):
                                resposta = questao_data.get('tipo1', '-')
                            else:
                                resposta = str(questao_data)
                        else:
                            resposta = '-'
                    else:
                        resposta = '-'

                    row[f'versao_{i+1}'] = resposta

                # Preencher versões restantes com '-' se necessário
                for i in range(len(versao_oficial.gabaritos_gerados), 5):
                    row[f'versao_{i+1}'] = '-'

                gabaritos_processados.append(row)

            # Ordenar gabaritos processados pelo número da questão
            gabaritos_processados.sort(key=lambda x: x['questao_idx'])

        except Exception as e:
            logger.error(f"Erro ao processar gabaritos oficiais do simulado {pk}: {str(e)}")
            messages.error(request, f"Erro ao processar gabaritos: {str(e)}")
            versoes = []
            gabaritos_processados = []

    if settings.DEBUG:
        logger.debug(f"Gabaritos processados (versão oficial): {gabaritos_processados}")

    return render(request, 'questions/simulado_detail.html', {
        'simulado': simulado,
        'questoes': questoes,
        'versoes': versoes,
        'gabaritos_processados': gabaritos_processados,
        'versao_oficial': versao_oficial,  # ✅ Mudança: passa versão oficial
        'historico_gabaritos': historico_gabaritos,
        'total_versoes': total_versoes,
    })

logger = logging.getLogger(__name__)

@login_required
@require_POST
def update_questoes_ordem(request, pk):
    logger.info(f"Atualizando ordem do simulado {pk} para usuário {request.user.username}")
    try:
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)
        data = json.loads(request.body)
        questoes = data.get('questoes', [])

        # Remover valores None e converter para inteiros
        questoes = [int(q) for q in questoes if q is not None]
        logger.debug(f"Questões recebidas após limpeza: {questoes}")

        if not questoes:
            logger.warning("Tentativa de salvar simulado sem questões")
            return JsonResponse({
                'status': 'error',
                'message': 'O simulado deve ter pelo menos uma questão'
            }, status=400)

        if len(questoes) > 45:
            logger.warning(f"Tentativa de salvar simulado com {len(questoes)} questões (máximo: 45)")
            return JsonResponse({
                'status': 'error',
                'message': 'O simulado não pode ter mais que 45 questões'
            }, status=400)

        if len(questoes) != len(set(questoes)):
            logger.warning("Detectadas questões duplicadas na lista")
            return JsonResponse({
                'status': 'error',
                'message': 'Existem questões duplicadas na lista'
            }, status=400)

        questoes_validas = set(Questao.objects.filter(
            models.Q(professor=request.user) | models.Q(professor__isnull=True),
            id__in=questoes
        ).values_list('id', flat=True))

        questoes_invalidas = set(questoes) - questoes_validas

        if questoes_invalidas:
            logger.warning(f"Questões inválidas detectadas: {questoes_invalidas}")
            return JsonResponse({
                'status': 'error',
                'message': f'Algumas questões selecionadas são inválidas: {", ".join(map(str, questoes_invalidas))}'
            }, status=400)

        # Verificar se houve mudança real na ordem antes de atualizar
        questoes_atuais = list(QuestaoSimulado.objects.filter(simulado=simulado).order_by('ordem').values_list('questao_id', flat=True))

        # Se a ordem é exatamente a mesma, não faz nada
        if questoes_atuais == questoes:
            logger.info(f"Ordem do simulado {pk} não foi alterada")
            return JsonResponse({
                'status': 'success',
                'message': 'Nenhuma alteração necessária'
            })

        logger.info(f"Ordem alterada no simulado {pk}: {questoes_atuais} -> {questoes}")

        with transaction.atomic():
            logger.debug("Iniciando transação atômica para atualizar questões do simulado")

            # CORRIGIDO: Limpar cache ANTES de fazer as alterações
            simulado.limpar_todo_cache()
            logger.info(f"Cache limpo para simulado {pk} devido à reordenação")

            # Deletar todas as questões existentes
            QuestaoSimulado.objects.filter(simulado=simulado).delete()

            # Recriar as questões na nova ordem
            for ordem, questao_id in enumerate(questoes, 1):
                QuestaoSimulado.objects.create(
                    simulado=simulado,
                    questao_id=questao_id,
                    ordem=ordem
                )

            # Atualizar timestamp do simulado
            simulado.ultima_modificacao = timezone.now()
            simulado.save(update_fields=['ultima_modificacao'])

        logger.info(f"Simulado {pk} atualizado com sucesso")
        return JsonResponse({
            'status': 'success',
            'message': 'Simulado atualizado com sucesso!'
        })

    except Exception as e:
        logger.error(f"Erro ao atualizar simulado {pk}: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao atualizar simulado: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
@login_required
def confirm_regenerate(request, pk):
    """View para confirmar nova geração de PDF quando já existem versões"""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # Buscar informações das versões existentes
    versoes_existentes = simulado.versoes_gabarito.all()[:5]  # Últimas 5
    total_versoes = simulado.get_total_versoes_gabarito()

    context = {
        'simulado': simulado,
        'versoes_existentes': versoes_existentes,
        'total_versoes': total_versoes,
        'mensagem_extra': 'Este simulado já possui versões geradas anteriormente.'
    }

    return render(request, 'questions/confirm_regenerate.html', context)

@login_required
def gerar_pdf(request, pk):
    """View para gerar PDF - SEMPRE com novo embaralhamento a cada download."""
    import zipfile
    from .pdf_performance_logger import PerformanceTimer, perf_logger, start_operation_timer, end_operation_timer
    import socket

    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # VERIFICAR SE JÁ EXISTEM VERSÕES E SE NÃO É GERAÇÃO FORÇADA
    versoes_existentes = simulado.get_total_versoes_gabarito()
    force_regenerate = request.GET.get('force', 'false').lower() == 'true'

    if versoes_existentes > 0 and not force_regenerate:
        print(f"DEBUG - Simulado {pk} já tem {versoes_existentes} versões, redirecionando para confirmação")
        return redirect('questions:confirm_regenerate', pk=pk)

    # Detectar ambiente PythonAnywhere
    IS_PYTHONANYWHERE = 'pythonanywhere' in os.environ.get('HOSTNAME', '')

    if IS_PYTHONANYWHERE:
        socket.setdefaulttimeout(300)
        import logging
        logging.getLogger('weasyprint').setLevel(logging.ERROR)

    operation_id = f"pdf_gen_{pk}_{int(time.time())}"
    start_operation_timer(operation_id, f"Geração completa de PDF único para simulado {pk}")

    try:
        with PerformanceTimer("gerar_pdf_completo", user=request.user.username, simulado_id=pk):
            print(f"DEBUG - SEMPRE gerando NOVO embaralhamento para simulado {pk}")

            # SEMPRE limpar qualquer cache existente
            simulado.limpar_todo_cache()

            # Motivo sempre é novo embaralhamento
            motivo_str = "Novo embaralhamento sempre"
            perf_logger.info(f"Simulado {pk} - {motivo_str.lower()}, gerando nova versão")

            # Buscar questões apenas uma vez
            with PerformanceTimer("carregar_questoes", simulado_id=pk):
                questoes = list(simulado.questoes.all().order_by('questaosimulado__ordem'))
                perf_logger.info(f"Carregadas {len(questoes)} questões para simulado {pk}")

            if len(questoes) > 45:
                perf_logger.warning(f"Simulado {pk} excede o limite de 45 questões: tem {len(questoes)}")
                messages.error(request, 'O simulado não pode ter mais que 45 questões')
                end_operation_timer(operation_id, success=False, reason="too_many_questions")
                return redirect('questions:simulado_edit', pk=simulado.pk)

            # Criar diretório temporário para os arquivos
            with tempfile.TemporaryDirectory() as tmpdirname:
                perf_logger.debug(f"Diretório temporário criado: {tmpdirname}")

                # 🆕 CRIAR VERSÃO ANTES DO LOOP PARA TER O CÓDIGO DISPONÍVEL
                nova_versao = VersaoGabarito.objects.create(
                    simulado=simulado,
                    gabaritos_gerados=[],  # Será preenchido depois
                    usuario_geracao=request.user,
                    total_questoes=len(questoes)
                )
                versao_codigo = nova_versao.get_versao_curta()
                perf_logger.info(f"Nova versão criada: {versao_codigo}")

                htmls_versoes = []
                embaralhamentos = [None] * 5
                cartoes_resposta = [None] * 5

                # Processamento sequencial
                with PerformanceTimer("processamento_sequencial", simulado_id=pk):
                    perf_logger.info(f"Iniciando processamento sequencial de 5 versões para simulado {pk}")

                    # Gerar HTML de cada versão em loop
                    for versao in range(1, 6):
                        try:
                            # 🆕 PASSAR CÓDIGO DA VERSÃO
                            html_versao, embaralhamento = _gerar_versao_simulado(
                                simulado, questoes, tmpdirname, versao, versao_codigo
                            )
                            htmls_versoes.append(html_versao)
                            embaralhamentos[versao-1] = embaralhamento
                            perf_logger.debug(f"Versão {versao} HTML gerado com sucesso")
                        except Exception as exc:
                            # 🆕 LIMPAR VERSÃO SE FALHAR
                            nova_versao.delete()
                            perf_logger.error(f"Erro ao gerar HTML da versão {versao}: {str(exc)}")
                            perf_logger.error(traceback.format_exc())
                            messages.error(request, f"Erro ao gerar versão {versao}: {str(exc)}")
                            end_operation_timer(operation_id, success=False, reason="version_generation_failed", version=versao)
                            return redirect('questions:simulado_edit', pk=simulado.pk)

                # Gerar PDF único com todas as versões
                with PerformanceTimer("gerar_pdf_unico", simulado_id=pk):
                    pdf_unico_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_todas_versoes.pdf')
                    _combinar_pdfs_versoes(htmls_versoes, pdf_unico_path, simulado, versao_codigo)
                    perf_logger.info(f"PDF único gerado com sucesso: {pdf_unico_path}")

                # Gerar cartões resposta COM O CÓDIGO DA VERSÃO
                with PerformanceTimer("gerar_cartoes_resposta", simulado_id=pk):
                    for versao in range(1, 6):
                        try:
                            # 🆕 PASSAR CÓDIGO DA VERSÃO
                            cartao_path = _gerar_cartao_resposta(
                                tmpdirname, versao, versao, len(questoes), versao_codigo
                            )
                            cartoes_resposta[versao-1] = cartao_path
                        except Exception as exc:
                            nova_versao.delete()
                            perf_logger.error(f"Erro ao gerar cartão resposta {versao}: {str(exc)}")
                            messages.error(request, f"Erro ao gerar cartão resposta {versao}: {str(exc)}")
                            end_operation_timer(operation_id, success=False, reason="answer_card_generation_failed", version=versao)
                            return redirect('questions:simulado_edit', pk=simulado.pk)

                # Verificar se todos os arquivos foram gerados
                if None in cartoes_resposta:
                    nova_versao.delete()
                    perf_logger.error(f"Cartões resposta incompletos para simulado {pk}")
                    messages.error(request, "Falha ao gerar alguns cartões resposta.")
                    end_operation_timer(operation_id, success=False, reason="incomplete_answer_cards")
                    return redirect('questions:simulado_edit', pk=simulado.pk)

                # Combinar cartões resposta
                with PerformanceTimer("combinar_cartoes", simulado_id=pk):
                    cartoes_pdf_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_cartoes_resposta.pdf')
                    _combinar_pdfs_simples(cartoes_resposta, cartoes_pdf_path)

                # Atualizar versão com os embaralhamentos gerados
                with PerformanceTimer("salvar_gabaritos", simulado_id=pk):
                    nova_versao.gabaritos_gerados = embaralhamentos
                    nova_versao.save()

                    simulado.versao_gabarito_oficial = nova_versao
                    simulado.save()
                    print(f"DEBUG - Nova versão definida como oficial: {nova_versao.get_versao_curta()}")

                    perf_logger.info(f"Nova versão de gabarito salva para simulado {pk}: {nova_versao.get_versao_curta()}")

                # Criar o arquivo ZIP
                with PerformanceTimer("criar_zip", simulado_id=pk):
                    versao_nome = nova_versao.get_versao_curta()
                    zip_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_materiais_{versao_nome}.zip')

                    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(pdf_unico_path, os.path.basename(pdf_unico_path))
                        zipf.write(cartoes_pdf_path, os.path.basename(cartoes_pdf_path))

                        # Arquivo README
                        readme_path = os.path.join(tmpdirname, 'README.txt')
                        with open(readme_path, 'w', encoding='utf-8') as readme:
                            readme.write(f"""SIMULADO: {simulado.titulo}
VERSÃO DO GABARITO: {versao_nome}
CÓDIGO DE RASTREIO: {versao_codigo}
GERADO EM: {nova_versao.data_geracao.strftime('%d/%m/%Y às %H:%M')}

Este pacote contém um único arquivo PDF com as 5 versões embaralhadas sequencialmente.

IMPORTANTE: CADA DOWNLOAD GERA UM NOVO EMBARALHAMENTO COMPLETO!
Não existe cache - sempre são geradas novas ordens das questões.

O código de rastreio ({versao_codigo}) está impresso:
- No rodapé direito de todos os 5 cartões resposta
- Pode ser usado para identificar qual arquivo PDF foi distribuído

CONTEÚDO:
- simulado_{simulado.pk}_todas_versoes.pdf: PDF único com 5 versões embaralhadas
- simulado_{simulado.pk}_cartoes_resposta.pdf: Cartões de resposta (com código {versao_codigo})

VERSÃO: {versao_nome}
""")
                        zipf.write(readme_path, 'README.txt')

                # Ler o ZIP e retornar
                with PerformanceTimer("ler_zip_final", simulado_id=pk):
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()

                    zip_size = len(zip_content) / 1024.0
                    perf_logger.info(f"ZIP gerado com PDF único: {zip_size:.2f} KB")

                # Finalizar logs
                perf_logger.info(f"Finalizada geração de PDF ÚNICO para simulado {pk}")
                end_operation_timer(operation_id, success=True, action="generated_single_pdf", size_kb=zip_size)

                # DECIDIR O RETORNO BASEADO SE É NOVA GERAÇÃO
                if force_regenerate:
                    # É nova geração - adicionar mensagem de sucesso
                    messages.success(request, f'PDF gerado com sucesso! Código de rastreio: {versao_nome}')

                    # 🆕 CRIAR NOME DE ARQUIVO BASEADO NO TÍTULO DO SIMULADO
                    import re
                    titulo_limpo = re.sub(r'[^\w\s-]', '', simulado.titulo)  # Remove caracteres especiais
                    titulo_limpo = re.sub(r'[-\s]+', '_', titulo_limpo)  # Substitui espaços por underscore
                    titulo_limpo = titulo_limpo[:50]  # Limitar a 50 caracteres

                    # Retornar o arquivo
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{titulo_limpo}_{versao_nome}.zip"'
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'

                    # Adicionar JavaScript para redirecionamento após download
                    response['X-Redirect-After-Download'] = reverse('questions:simulado_list')

                    return response
                else:
                    # Primeira geração - download normal
                    # 🆕 CRIAR NOME DE ARQUIVO BASEADO NO TÍTULO DO SIMULADO
                    import re
                    titulo_limpo = re.sub(r'[^\w\s-]', '', simulado.titulo)
                    titulo_limpo = re.sub(r'[-\s]+', '_', titulo_limpo)
                    titulo_limpo = titulo_limpo[:50]

                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{titulo_limpo}_{versao_nome}.zip"'
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response

    except Exception as e:
        perf_logger.error(f"Erro geral ao gerar PDF para simulado {pk}: {str(e)}")
        perf_logger.error(traceback.format_exc())
        end_operation_timer(operation_id, success=False, reason="general_error", error=str(e))
        messages.error(request, f"Erro ao gerar os arquivos: {str(e)}")
        return redirect('questions:simulado_edit', pk=simulado.pk)

@time_function
def _combinar_pdfs_simples(pdfs_list, output_path):
    """Combina vários PDFs em sequência em um único arquivo, com logs."""
    with PerformanceTimer("combinar_pdfs_simples",
                         extra_data={'num_pdfs': len(pdfs_list)}):
        from PyPDF2 import PdfWriter, PdfReader

        writer = PdfWriter()
        total_pages = 0

        for i, pdf_path in enumerate(pdfs_list):
            with PerformanceTimer(f"processar_pdf_{i+1}",
                                 extra_data={'arquivo': os.path.basename(pdf_path)}):
                reader = PdfReader(pdf_path)
                num_pages = len(reader.pages)
                total_pages += num_pages

                for page in reader.pages:
                    writer.add_page(page)

                perf_logger.debug(f"PDF {i+1}: {num_pages} páginas processadas")

        perf_logger.debug(f"Escrevendo PDF combinado com {total_pages} páginas: {output_path}")
        with open(output_path, 'wb') as f:
            writer.write(f)

        log_file_size(output_path, "PDFs Combinados")
        return output_path

@time_function
def _combinar_pdfs_versoes(htmls_versoes, output_path, simulado, codigo_geracao=None):
    """
    Gera PDF separado para cada TIPO com numeração reiniciada.
    ✅ Adiciona código da versão na última página usando PyPDF2.
    """
    with PerformanceTimer("combinar_htmls_em_pdf_unico",
                        extra_data={'num_tipos': len(htmls_versoes), 'saida': os.path.basename(output_path)}):

        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        from PyPDF2 import PdfWriter, PdfReader
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        import tempfile
        import warnings
        import logging
        import io

        # Detectar ambiente
        IS_PYTHONANYWHERE = 'pythonanywhere' in os.environ.get('HOSTNAME', '')

        # Configurar fonte
        font_config = FontConfiguration()

        # Reduzir logging
        if IS_PYTHONANYWHERE:
            logging.getLogger('weasyprint').setLevel(logging.ERROR)
            warnings.filterwarnings("ignore", category=UserWarning)

        writer = PdfWriter()
        total_paginas_adicionadas = 0
        total_paginas_brancas = 0

        # 🔥 FUNÇÃO HELPER: Adicionar texto em uma página PDF
        def adicionar_codigo_versao_em_pagina(page, tipo_idx, num_pagina, codigo):
            """Adiciona código da versão no rodapé direito de uma página PDF."""
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)

            # Tornar o canvas transparente
            can.setFillAlpha(0)
            can.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            can.setFillAlpha(1)

            # Rodapé esquerdo (já existe no PDF do WeasyPrint, não adicionar)
            # Apenas adicionar rodapé direito
            can.setFont("Courier", 8)
            can.setFillColorRGB(0.4, 0.4, 0.4)
            texto_codigo = f"ID: {codigo}"
            largura_texto = can.stringWidth(texto_codigo, "Courier", 8)
            can.drawString(
                A4[0] - largura_texto - (1.5 * 10 * mm),
                0.5 * 10 * mm,
                texto_codigo
            )

            can.save()
            packet.seek(0)

            # Mesclar com a página original
            overlay_pdf = PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])
            return page

        # 🆕 PROCESSAR CADA TIPO SEPARADAMENTE
        for tipo_idx, html_tipo in enumerate(htmls_versoes, 1):
            perf_logger.info(f"Processando Tipo {tipo_idx}/{len(htmls_versoes)}")

            # CSS APENAS com rodapé esquerdo
            css_tipo = CSS(string=f'''
                @page {{
                    size: A4;
                    margin: 1cm 1cm 1.5cm 1cm;

                    @bottom-left {{
                        content: "Tipo {tipo_idx} - Página " counter(page);
                        font-family: Arial, Helvetica, sans-serif;
                        font-size: 9px;
                        color: #666;
                    }}
                }}

                body, * {{
                    font-family: Arial, Helvetica, sans-serif !important;
                }}
            ''')

            # GERAR PDF TEMPORÁRIO DESTE TIPO
            with tempfile.NamedTemporaryFile(suffix=f'_tipo{tipo_idx}.pdf', delete=False) as tmp_pdf:
                tmp_pdf_path = tmp_pdf.name

                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")

                        html = HTML(string=html_tipo, base_url=settings.BASE_DIR)
                        html.write_pdf(
                            tmp_pdf_path,
                            font_config=font_config,
                            stylesheets=[css_tipo],
                            optimize_size=('fonts',)
                        )

                    # LER O PDF GERADO
                    reader = PdfReader(tmp_pdf_path)
                    num_paginas = len(reader.pages)

                    perf_logger.info(f"Tipo {tipo_idx}: {num_paginas} páginas geradas")

                    # 🔥 ADICIONAR PÁGINAS COM CÓDIGO APENAS NA ÚLTIMA
                    for i, page in enumerate(reader.pages):
                        num_pagina_atual = i + 1

                        # Se for a ÚLTIMA página, adicionar código
                        if num_pagina_atual == num_paginas:
                            page = adicionar_codigo_versao_em_pagina(
                                page, tipo_idx, num_pagina_atual, codigo_geracao
                            )
                            perf_logger.debug(f"Código adicionado na página {num_pagina_atual} do Tipo {tipo_idx}")

                        writer.add_page(page)
                        total_paginas_adicionadas += 1

                    # SE NÚMERO ÍMPAR, ADICIONAR PÁGINA EM BRANCO COM CÓDIGO
                    if num_paginas % 2 == 1:
                        perf_logger.info(f"Tipo {tipo_idx} tem {num_paginas} páginas (ímpar), adicionando página em branco")

                        # Criar página em branco com rodapés
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=A4)

                        # Fundo branco
                        can.setFillColorRGB(1, 1, 1)
                        can.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

                        # Rodapé esquerdo
                        can.setFont("Helvetica", 9)
                        can.setFillColorRGB(0.4, 0.4, 0.4)
                        can.drawString(
                            1 * 10 * mm,
                            0.5 * 10 * mm,
                            f"Tipo {tipo_idx} - Página {num_paginas + 1}"
                        )

                        # Rodapé direito
                        can.setFont("Courier", 8)
                        texto_codigo = f"ID: {codigo_geracao}"
                        largura_texto = can.stringWidth(texto_codigo, "Courier", 8)
                        can.drawString(
                            A4[0] - largura_texto - (1.5 * 10 * mm),
                            0.5 * 10 * mm,
                            texto_codigo
                        )

                        can.showPage()
                        can.save()
                        packet.seek(0)

                        blank_reader = PdfReader(packet)
                        writer.add_page(blank_reader.pages[0])
                        total_paginas_brancas += 1
                        total_paginas_adicionadas += 1

                        perf_logger.debug(f"Página em branco adicionada APÓS Tipo {tipo_idx}")

                finally:
                    if os.path.exists(tmp_pdf_path):
                        os.unlink(tmp_pdf_path)

        # SALVAR PDF FINAL
        with open(output_path, 'wb') as f:
            writer.write(f)

        perf_logger.info(f"PDF final: {total_paginas_adicionadas} páginas ({total_paginas_brancas} em branco)")
        log_file_size(output_path, "PDF Único com 5 Tipos")

        return output_path

@time_function
def _gerar_versao_simulado(simulado, questoes, tmpdirname, tipo, codigo_geracao=None):
    """Gera apenas o HTML de um tipo do simulado (SEM definir @page aqui)."""
    with PerformanceTimer(f"gerar_html_tipo_{tipo}",
                         simulado_id=simulado.pk,
                         extra_data={'num_questoes': len(questoes)}):

        print(f"DEBUG - Gerando HTML tipo {tipo} para simulado {simulado.pk}")

        IS_PYTHONANYWHERE = 'pythonanywhere' in os.environ.get('HOSTNAME', '')

        # SEMPRE embaralhar as questões
        with PerformanceTimer("embaralhar_questoes", simulado_id=simulado.pk,
                            extra_data={'tipo': tipo}):
            questoes_shuffled = list(custom_filters.shuffle(questoes))

            ordem_atual = {
                'questoes': [q.id for q in questoes_shuffled],
                'gabarito': {}
            }

            for ordem, questao in enumerate(questoes_shuffled, 1):
                resp_original = questao.resposta_correta
                ordem_atual['gabarito'][ordem] = {
                    'tipo1': resp_original,
                    'tipo2': resp_original,
                    'tipo3': resp_original,
                    'tipo4': resp_original,
                    'tipo5': resp_original
                }

        # Pré-processar imagens
        with PerformanceTimer("pre_processar_imagens", simulado_id=simulado.pk,
                            extra_data={'tipo': tipo}):
            from PIL import Image
            import io
            import base64

            imagens_count = 0
            LARGURA_MAXIMA_COLUNA = 280
            ALTURA_MAXIMA = 400

            for q in questoes_shuffled:
                if q.imagem and hasattr(q.imagem, 'path') and os.path.exists(q.imagem.path):
                    imagens_count += 1

                    try:
                        with Image.open(q.imagem.path) as img:
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')

                            largura_original, altura_original = img.size

                            fator_largura = LARGURA_MAXIMA_COLUNA / largura_original
                            fator_altura = ALTURA_MAXIMA / altura_original
                            fator_redimensionamento = min(fator_largura, fator_altura, 1.0)

                            if fator_redimensionamento < 1.0:
                                nova_largura = int(largura_original * fator_redimensionamento)
                                nova_altura = int(altura_original * fator_redimensionamento)

                                img_redimensionada = img.resize(
                                    (nova_largura, nova_altura),
                                    Image.Resampling.LANCZOS
                                )

                                buffer = io.BytesIO()
                                img_redimensionada.save(
                                    buffer,
                                    format='JPEG',
                                    quality=90,
                                    optimize=True
                                )

                                q.imagem_redimensionada_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                                q.imagem_tamanho = f"{nova_largura}x{nova_altura}"
                            else:
                                buffer = io.BytesIO()
                                img.save(buffer, format='JPEG', quality=90, optimize=True)
                                q.imagem_redimensionada_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                                q.imagem_tamanho = f"{largura_original}x{altura_original}"

                            q.imagem_path = q.imagem.path

                    except Exception as e:
                        perf_logger.warning(f"Erro ao processar imagem da questão {q.id}: {str(e)}")
                        q.imagem_path = q.imagem.path if os.path.exists(q.imagem.path) else None

            perf_logger.debug(f"Tipo {tipo}: {imagens_count} imagens processadas")

        # 🆕 RENDERIZAR HTML SEM @page (será adicionado na combinação)
        with PerformanceTimer("renderizar_html", simulado_id=simulado.pk,
                            extra_data={'tipo': tipo}):
            html_string = render_to_string('questions/simulado_pdf.html', {
                'simulado': simulado,
                'questoes': questoes_shuffled,
                'tipo': tipo,
                'codigo_geracao': codigo_geracao,
                'MEDIA_ROOT': settings.MEDIA_ROOT,
                'is_pythonanywhere': IS_PYTHONANYWHERE,
            })

            # Otimização
            import re
            html_string = re.sub(r'<!--.*?-->', '', html_string, flags=re.DOTALL)
            html_string = re.sub(r'\s{2,}', ' ', html_string)

            perf_logger.debug(f"HTML para tipo {tipo} gerado: {len(html_string)/1024:.2f} KB")

        return html_string, ordem_atual


@time_function
def _gerar_cartao_resposta(tmpdirname, caderno, tipo, num_questoes, versao_codigo=None):
    """Versão otimizada da função de geração de cartão resposta com código de rastreio."""
    with PerformanceTimer(f"gerar_cartao_resposta_tipo{tipo}",
                         extra_data={'num_questoes': num_questoes, 'caderno': caderno}):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm

        nome_arquivo = os.path.join(tmpdirname, f'Cartao_Resposta_{caderno}_Tipo{tipo}.pdf')
        perf_logger.debug(f"Gerando cartão resposta: {nome_arquivo}")

        c = canvas.Canvas(nome_arquivo, pagesize=A4)
        c.setTitle(f"Cartão Resposta - Tipo {tipo}")
        c.setAuthor("Sistema de Correção")
        c.setSubject("Cartão Resposta")
        c.setPageCompression(1)
        largura, altura = A4

        # Determina o número de colunas
        num_colunas = 1 if num_questoes <= 23 else 2

        # Distribuição das questões entre as colunas
        questoes_por_coluna = []
        if num_colunas == 1:
            questoes_por_coluna = [num_questoes]
        else:
            if num_questoes % 2 == 0:
                questoes_por_coluna = [num_questoes // 2, num_questoes // 2]
            else:
                questoes_por_coluna = [(num_questoes // 2) + 1, num_questoes // 2]

        # Dimensões básicas
        margem_superior = 50 * mm
        margem_lateral = 30 * mm
        espaco_entre_colunas = 15 * mm
        alternativas = ['A', 'B', 'C', 'D', 'E']
        diametro_circulo = 4 * mm
        espaco_entre_circulos = 6 * mm
        espaco_entre_questoes = 8 * mm
        margem_interna = 3 * mm
        largura_bolhas = (5 * espaco_entre_circulos)
        largura_indice = 8 * mm
        largura_necessaria = largura_bolhas + (2 * margem_interna)

        largura_total_necessaria = (largura_necessaria * num_colunas) + (espaco_entre_colunas * (num_colunas - 1)) + (largura_indice * num_colunas)
        margem_lateral = (largura - largura_total_necessaria) / 2

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(margem_lateral - 20 * mm, altura - 20 * mm, f"CARTÃO RESPOSTA - TIPO {tipo}")

        questoes_processadas = 0

        for coluna in range(num_colunas):
            x_inicial_indice = margem_lateral + (coluna * (largura_necessaria + espaco_entre_colunas + largura_indice))
            x_inicial_retangulo = x_inicial_indice + largura_indice
            largura_bolhas_total = (len(alternativas) - 1) * espaco_entre_circulos
            x_inicial_bolhas = x_inicial_retangulo + ((largura_necessaria - largura_bolhas_total) / 2)

            questoes_nesta_coluna = questoes_por_coluna[coluna]
            altura_necessaria = (questoes_nesta_coluna * espaco_entre_questoes) + (2 * margem_interna)

            c.setLineWidth(0.7 * mm)
            c.rect(x_inicial_retangulo,
                  altura - margem_superior - altura_necessaria,
                  largura_necessaria,
                  altura_necessaria)

            # Cabeçalho das alternativas
            for i, alt in enumerate(alternativas):
                x = x_inicial_bolhas + (i * espaco_entre_circulos)
                y = altura - margem_superior + 5 * mm
                c.setFont("Helvetica", 10)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x - 1 * mm, y, alt)

            for q in range(questoes_nesta_coluna):
                numero_questao = questoes_processadas + q + 1
                y = altura - margem_superior - ((q + 1) * espaco_entre_questoes)

                # Número da questão FORA do retângulo
                c.setFont("Helvetica", 10)
                c.setFillColorRGB(0, 0, 0)
                if numero_questao < 10:
                    c.drawString(x_inicial_indice, y - 1 * mm, f"0{numero_questao}")
                else:
                    c.drawString(x_inicial_indice, y - 1 * mm, f"{numero_questao}")

                # Bolhas das alternativas
                for i in range(5):
                    x = x_inicial_bolhas + (i * espaco_entre_circulos)
                    c.circle(x, y, diametro_circulo / 2, stroke=1, fill=0)

            questoes_processadas += questoes_nesta_coluna

        # 🆕 ADICIONAR CÓDIGO DE RASTREIO NO RODAPÉ (CANTO INFERIOR DIREITO)
        if versao_codigo:
            c.setFont("Courier", 7)  # Fonte monoespaçada pequena
            c.setFillColorRGB(0.4, 0.4, 0.4)  # Cinza médio
            codigo_text = f"ID: {versao_codigo}"
            # Posicionar no canto inferior direito
            c.drawRightString(largura - 15 * mm, 5 * mm, codigo_text)

        # Instruções no rodapé (CANTO INFERIOR ESQUERDO)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0, 0, 0)  # Preto
        c.drawString(margem_lateral, 15 * mm, f"Total de questões: {num_questoes}")
        c.drawString(margem_lateral, 10 * mm, "Preencha completamente os círculos com caneta preta ou azul")

        c.save()
        log_file_size(nome_arquivo, f"Cartão Resposta Tipo {tipo}")

        if versao_codigo:
            perf_logger.debug(f"Cartão resposta {tipo} gerado com código de rastreio: {versao_codigo}")

        return nome_arquivo

@login_required
def simulado_form(request, pk=None):
    """View para criar ou editar um simulado."""
    # Limpa todas as mensagens existentes no início da view
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Isso consome/remove todas as mensagens

    # Inicializa o simulado como None (para criação)
    simulado = None

    # Se um pk foi fornecido, tenta buscar o simulado existente
    if pk:
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    if request.method == 'POST':
        # Passa o parâmetro user para o formulário
        form = SimuladoForm(request.POST, instance=simulado, user=request.user)
        if form.is_valid():
            simulado = form.save(commit=False)
            # Sempre define o professor como o usuário atual antes de salvar
            simulado.professor = request.user

            # Capturar pontuação total (campo simples)
            pontuacao_total = request.POST.get('pontuacao_total', 5)
            try:
                simulado.pontuacao_total = int(pontuacao_total)
                if simulado.pontuacao_total <= 0:
                    simulado.pontuacao_total = 5
            except (ValueError, TypeError):
                simulado.pontuacao_total = 5
                messages.warning(request, 'Valor de pontuação inválido. Usando valor padrão: 5')

            simulado.save()

            # Salvar as turmas selecionadas
            turmas = form.cleaned_data['turmas']
            simulado.classes.set(turmas)

            messages.success(request, 'Alterações salvas com sucesso!')
            return redirect('questions:simulado_edit', pk=simulado.pk)
    else:
        # Passa o parâmetro user para o formulário
        form = SimuladoForm(instance=simulado, user=request.user)

    context = {
        'form': form,
        'simulado': simulado,
        'titulo': 'Editar Simulado' if pk else 'Novo Simulado'
    }
    return render(request, 'questions/simulado_form.html', context)

@login_required
def simulado_gabaritos_historico(request, pk):
    """View para exibir o histórico de gabaritos de um simulado."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # Buscar todas as versões de gabarito (histórico)
    versoes = simulado.get_historico_gabaritos()

    # ✅ LÓGICA CORRIGIDA - Só define oficial se NÃO EXISTIR nenhuma
    # NÃO sobrescreve escolhas manuais do usuário
    if versoes.exists() and not simulado.versao_gabarito_oficial:
        versao_mais_recente = versoes.first()  # Primeira = mais recente (order by -data_geracao)
        simulado.versao_gabarito_oficial = versao_mais_recente
        simulado.save()
        print(f"DEBUG - Primeira versão oficial definida: {versao_mais_recente.get_versao_curta()}")
    elif versoes.exists() and simulado.versao_gabarito_oficial:
        # Verificar se a versão oficial ainda existe no histórico
        if not versoes.filter(versao_id=simulado.versao_gabarito_oficial.versao_id).exists():
            # Só redefine se a versão oficial atual foi deletada
            versao_mais_recente = versoes.first()
            simulado.versao_gabarito_oficial = versao_mais_recente
            simulado.save()
            print(f"DEBUG - Versão oficial inexistente substituída: {versao_mais_recente.get_versao_curta()}")
        else:
            print(f"DEBUG - Mantendo versão oficial escolhida: {simulado.versao_gabarito_oficial.get_versao_curta()}")

    # Paginação
    paginator = Paginator(versoes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estatísticas simplificadas
    total_versoes = simulado.get_total_versoes_gabarito()
    ultima_versao = versoes.first() if versoes.exists() else None

    # Informações adicionais
    total_questoes = simulado.questoes.count()
    tem_questoes = total_questoes > 0

    context = {
        'simulado': simulado,
        'page_obj': page_obj,
        'total_versoes': total_versoes,
        'ultima_versao': ultima_versao,
        'total_questoes': total_questoes,
        'tem_questoes': tem_questoes,
        'versao_oficial': simulado.versao_gabarito_oficial,
        'questoes_alteradas': False,
        'aviso_novo_sistema': True,
    }

    return render(request, 'questions/simulado_gabaritos_historico.html', context)

@login_required
def visualizar_gabarito_versao(request, pk, versao_id):
    """View para visualizar uma versão específica do gabarito."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)
    versao = get_object_or_404(VersaoGabarito, simulado=simulado, versao_id=versao_id)

    # Processar os gabaritos para exibição
    gabaritos_processados = []
    versoes_data = []

    if versao.gabaritos_gerados:
        try:
            # Processar os dados de gabarito para facilitar uso no template
            for versao_data in versao.gabaritos_gerados:
                versoes_data.append({'gabarito': versao_data.get('gabarito', {})})

            # Obter todas as chaves de questões da primeira versão
            if versao.gabaritos_gerados:
                primeira_versao = versao.gabaritos_gerados[0]
                questao_indices = list(primeira_versao.get('gabarito', {}).keys())

                # Ordenar questões numericamente
                questao_indices.sort(key=lambda x: int(x))

                # Para cada questão, obter as respostas em cada versão
                for questao_idx in questao_indices:
                    row = {'questao_idx': int(questao_idx)}

                    # Obter resposta para cada versão
                    for i in range(len(versoes_data)):
                        if i < len(versao.gabaritos_gerados):
                            gabarito = versao.gabaritos_gerados[i].get('gabarito', {})
                            questao_data = gabarito.get(questao_idx, {})

                            if isinstance(questao_data, dict):
                                resposta = questao_data.get('tipo1', '-')
                            else:
                                resposta = str(questao_data) if questao_data else '-'

                            row[f'versao_{i+1}'] = resposta
                        else:
                            row[f'versao_{i+1}'] = '-'

                    # Preencher versões restantes se necessário
                    for i in range(len(versao.gabaritos_gerados), 5):
                        row[f'versao_{i+1}'] = '-'

                    gabaritos_processados.append(row)

        except Exception as e:
            logger.error(f"Erro ao processar gabaritos da versão {versao_id}: {str(e)}")
            messages.error(request, f"Erro ao processar gabaritos: {str(e)}")
            versoes_data = []
            gabaritos_processados = []

    # Verificar se há resultados vinculados
    tem_resultados = versao.tem_resultados_vinculados()

    # Verificar se é a versão mais recente
    ultima_versao = simulado.get_historico_gabaritos().first()
    is_mais_recente = ultima_versao and ultima_versao.versao_id == versao.versao_id

    # Estatísticas da versão
    total_versoes_simulado = simulado.get_total_versoes_gabarito()
    posicao_versao = list(simulado.get_historico_gabaritos().values_list('versao_id', flat=True)).index(versao.versao_id) + 1

    context = {
        'simulado': simulado,
        'versao': versao,
        'versoes': versoes_data,
        'gabaritos_processados': gabaritos_processados,
        'tem_resultados': tem_resultados,
        'is_mais_recente': is_mais_recente,
        'total_versoes_simulado': total_versoes_simulado,
        'posicao_versao': posicao_versao,
        'aviso_historico': True,  # Indica que é apenas histórico
    }

    return render(request, 'questions/visualizar_gabarito_versao.html', context)

@login_required
def comparar_versoes_gabarito(request, pk):
    """View para comparar duas versões de gabarito do histórico."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # Obter as versões para comparação dos parâmetros GET
    versao1_id = request.GET.get('versao1')
    versao2_id = request.GET.get('versao2')

    # Buscar todas as versões disponíveis para seleção
    versoes_disponiveis = simulado.get_historico_gabaritos()

    # Contexto base
    context = {
        'simulado': simulado,
        'versoes_disponiveis': versoes_disponiveis,
        'total_versoes': simulado.get_total_versoes_gabarito(),
        'aviso_historico': True,  # Indica que é apenas histórico
    }

    # Se ambas as versões foram selecionadas, fazer a comparação
    if versao1_id and versao2_id:
        try:
            # Converter strings para UUID se necessário
            if isinstance(versao1_id, str):
                versao1_id = uuid.UUID(versao1_id)
            if isinstance(versao2_id, str):
                versao2_id = uuid.UUID(versao2_id)

            # Buscar as versões no histórico
            versao1 = simulado.versoes_gabarito.get(versao_id=versao1_id)
            versao2 = simulado.versoes_gabarito.get(versao_id=versao2_id)

            # Verificar se as versões são diferentes
            if versao1.versao_id == versao2.versao_id:
                messages.warning(request, 'Você selecionou a mesma versão para comparação.')
                return render(request, 'questions/comparar_versoes_gabarito.html', context)

            # Comparar as versões
            diferencas = _comparar_gabaritos(versao1, versao2)

            # Adicionar informações das versões
            versao1_info = {
                'versao': versao1,
                'versao_curta': versao1.get_versao_curta(),
                'data_geracao': versao1.data_geracao,
                'total_questoes': versao1.total_questoes,
                'tem_resultados': versao1.tem_resultados_vinculados(),
                'observacoes': versao1.observacoes or 'Nenhuma observação'
            }

            versao2_info = {
                'versao': versao2,
                'versao_curta': versao2.get_versao_curta(),
                'data_geracao': versao2.data_geracao,
                'total_questoes': versao2.total_questoes,
                'tem_resultados': versao2.tem_resultados_vinculados(),
                'observacoes': versao2.observacoes or 'Nenhuma observação'
            }

            # Gerar resumo da comparação
            resumo_comparacao = {
                'total_diferencas': diferencas['total_diferencas'],
                'questoes_diferentes': len(diferencas['questoes_diferentes']),
                'questoes_adicionadas': len(diferencas['questoes_adicionadas']),
                'questoes_removidas': len(diferencas['questoes_removidas']),
                'percentual_diferenca': 0
            }

            # Calcular percentual de diferença
            if versao1.total_questoes > 0:
                total_comparacoes = max(versao1.total_questoes, versao2.total_questoes)
                resumo_comparacao['percentual_diferenca'] = round(
                    (diferencas['total_diferencas'] / total_comparacoes) * 100, 2
                )

            context.update({
                'versao1_info': versao1_info,
                'versao2_info': versao2_info,
                'diferencas': diferencas,
                'resumo_comparacao': resumo_comparacao,
                'versao1_selecionada': str(versao1_id),
                'versao2_selecionada': str(versao2_id),
                'comparacao_realizada': True,
            })

            # Log da comparação
            logger.info(f"Comparação realizada entre versões {versao1.get_versao_curta()} e {versao2.get_versao_curta()} do simulado {pk}")

        except VersaoGabarito.DoesNotExist:
            messages.error(request, 'Uma das versões selecionadas não foi encontrada no histórico.')
            logger.warning(f"Tentativa de comparar versão inexistente no simulado {pk}")
        except ValueError as e:
            messages.error(request, 'ID de versão inválido fornecido.')
            logger.warning(f"ID de versão inválido na comparação do simulado {pk}: {str(e)}")
        except Exception as e:
            messages.error(request, f'Erro ao comparar versões: {str(e)}')
            logger.error(f"Erro na comparação de versões do simulado {pk}: {str(e)}")

    elif versao1_id or versao2_id:
        # Se apenas uma versão foi selecionada
        messages.info(request, 'Selecione duas versões diferentes para comparar.')

    return render(request, 'questions/comparar_versoes_gabarito.html', context)

@login_required
@require_POST
def definir_gabarito_oficial(request, pk):
    """Debug version - retorna informações detalhadas"""
    debug_info = []

    try:
        debug_info.append(f"🔍 Simulado ID: {pk}")
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)
        debug_info.append(f"🔍 Simulado encontrado: {simulado.titulo}")

        versao_id = request.POST.get('versao_id')
        debug_info.append(f"🔍 versao_id recebido: {versao_id}")
        debug_info.append(f"🔍 POST data: {dict(request.POST)}")

        if not versao_id:
            debug_info.append("❌ versao_id não fornecido")
            return JsonResponse({
                'success': False,
                'error': 'ID da versão não fornecido',
                'debug': debug_info
            })

        # Resto da lógica...
        versao_uuid = uuid.UUID(versao_id)
        versao = simulado.versoes_gabarito.get(versao_id=versao_uuid)
        debug_info.append(f"🔍 Versão encontrada: {versao.get_versao_curta()}")

        versao_anterior = simulado.versao_gabarito_oficial
        debug_info.append(f"🔍 Versão anterior: {versao_anterior.get_versao_curta() if versao_anterior else 'Nenhuma'}")

        simulado.versao_gabarito_oficial = versao
        simulado.save(update_fields=['versao_gabarito_oficial'])
        debug_info.append(f"✅ Simulado salvo!")

        # Verificar se salvou
        simulado.refresh_from_db()
        debug_info.append(f"🔍 Verificação: {simulado.versao_gabarito_oficial.get_versao_curta()}")

        return JsonResponse({
            'success': True,
            'message': f'Versão {versao.get_versao_curta()} definida como oficial!',
            'debug': debug_info,
            'versao_info': {
                'id': str(versao.versao_id),
                'versao_curta': versao.get_versao_curta(),
                'data_geracao': versao.data_geracao.strftime('%d/%m/%Y às %H:%M'),
            }
        })

    except Exception as e:
        debug_info.append(f"❌ ERRO: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'debug': debug_info
        })

@login_required
@require_POST
@csrf_exempt
def excluir_versao_gabarito(request, pk, versao_id):
    """
    View AJAX para excluir uma versão do histórico de gabaritos.
    ATENÇÃO: Não afeta a geração futura de PDFs.
    """
    try:
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

        # Converter string para UUID se necessário
        if isinstance(versao_id, str):
            versao_id = uuid.UUID(versao_id)

        versao = get_object_or_404(VersaoGabarito, simulado=simulado, versao_id=versao_id)

        # Verificar se não há resultados vinculados
        if versao.tem_resultados_vinculados():
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir uma versão que possui resultados de alunos vinculados'
            })

        # Verificar se não é a única versão restante
        total_versoes = simulado.get_total_versoes_gabarito()
        if total_versoes <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir a única versão restante no histórico'
            })

        # Verificar se não é uma versão muito recente (últimas 24h)
        from django.utils import timezone
        limite_tempo = timezone.now() - timezone.timedelta(hours=24)

        if versao.data_geracao > limite_tempo:
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir versões criadas nas últimas 24 horas'
            })

        versao_curta = versao.get_versao_curta()
        data_geracao = versao.data_geracao.strftime('%d/%m/%Y às %H:%M')

        # Excluir a versão
        versao.delete()

        return JsonResponse({
            'success': True,
            'message': f'Versão {versao_curta} (gerada em {data_geracao}) excluída do histórico com sucesso',
            'aviso': 'A exclusão do histórico não afeta gerações futuras de PDF.',
            'versoes_restantes': simulado.get_total_versoes_gabarito()
        })

    except VersaoGabarito.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Versão não encontrada no histórico'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'ID de versão inválido'})
    except Exception as e:
        logger.error(f"Erro ao excluir versão do histórico: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})

# FUNÇÃO AUXILIAR: Comparar Gabaritos
def _comparar_gabaritos(versao1, versao2):
    """Compara duas versões de gabarito e retorna as diferenças."""
    diferencas = {
        'questoes_diferentes': [],
        'questoes_adicionadas': [],
        'questoes_removidas': [],
        'total_diferencas': 0
    }

    if not versao1.gabaritos_gerados or not versao2.gabaritos_gerados:
        return diferencas

    # Comparar primeira versão de cada gabarito (pode ser expandido para comparar todas)
    gab1 = versao1.gabaritos_gerados[0].get('gabarito', {}) if versao1.gabaritos_gerados else {}
    gab2 = versao2.gabaritos_gerados[0].get('gabarito', {}) if versao2.gabaritos_gerados else {}

    # Questões em comum
    questoes_comuns = set(gab1.keys()) & set(gab2.keys())

    # Questões diferentes
    for questao in questoes_comuns:
        resp1 = gab1[questao].get('tipo1', '') if isinstance(gab1[questao], dict) else gab1[questao]
        resp2 = gab2[questao].get('tipo1', '') if isinstance(gab2[questao], dict) else gab2[questao]

        if resp1 != resp2:
            diferencas['questoes_diferentes'].append({
                'questao': questao,
                'resposta_v1': resp1,
                'resposta_v2': resp2
            })

    # Questões adicionadas (presentes em v2 mas não em v1)
    questoes_adicionadas = set(gab2.keys()) - set(gab1.keys())
    for questao in questoes_adicionadas:
        resp2 = gab2[questao].get('tipo1', '') if isinstance(gab2[questao], dict) else gab2[questao]
        diferencas['questoes_adicionadas'].append({
            'questao': questao,
            'resposta': resp2
        })

    # Questões removidas (presentes em v1 mas não em v2)
    questoes_removidas = set(gab1.keys()) - set(gab2.keys())
    for questao in questoes_removidas:
        resp1 = gab1[questao].get('tipo1', '') if isinstance(gab1[questao], dict) else gab1[questao]
        diferencas['questoes_removidas'].append({
            'questao': questao,
            'resposta': resp1
        })

    diferencas['total_diferencas'] = (
        len(diferencas['questoes_diferentes']) +
        len(diferencas['questoes_adicionadas']) +
        len(diferencas['questoes_removidas'])
    )

    return diferencas

@login_required
def progresso_pdf(request, pk):
    """View que exibe a página de progresso do PDF."""
    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

    # NOVA LÓGICA - Verificar se já existem versões ANTES de mostrar a página
    versoes_existentes = simulado.get_total_versoes_gabarito()
    force_regenerate = request.GET.get('force', 'false').lower() == 'true'

    # Se já existem versões E não é geração forçada, redirecionar para confirmação
    if versoes_existentes > 0 and not force_regenerate:
        print(f"DEBUG - Simulado {pk} já tem {versoes_existentes} versões, redirecionando para confirmação")
        return redirect('questions:confirm_regenerate', pk=pk)

    # Se chegou até aqui, pode mostrar a página de progresso
    # Inicializar o progresso na sessão
    request.session[f'progress_{pk}'] = {
        'step': 0,
        'message': 'Iniciando...',
        'percent': 0,
        'completed': False,
        'error': None
    }

    context = {
        'simulado': simulado,
        'pk': pk
    }

    return render(request, 'questions/progresso_pdf.html', context)

@login_required
def status_progresso(request, pk):
    """View AJAX que retorna o status atual do progresso."""
    progress_key = f'progress_{pk}'
    progress = request.session.get(progress_key, {
        'step': 0,
        'message': 'Aguardando...',
        'percent': 0,
        'completed': False,
        'error': None
    })

    return JsonResponse(progress)

@login_required
def gerar_pdf_com_progresso(request, pk):
    """View que gera PDF único atualizando o progresso na sessão."""
    import time  # MOVER IMPORT PARA O TOPO
    import threading

    simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)
    progress_key = f'progress_{pk}'

    def update_progress(step, message, percent):
        """Função helper para atualizar progresso."""
        request.session[progress_key] = {
            'step': step,
            'message': message,
            'percent': percent,
            'completed': False,
            'error': None
        }
        request.session.save()

    def complete_progress(success=True, error=None, download_url=None):
        """Função helper para finalizar progresso."""
        request.session[progress_key] = {
            'step': 100,
            'message': 'Concluído!' if success else f'Erro: {error}',
            'percent': 100,
            'completed': True,
            'error': error,
            'download_url': download_url
        }
        request.session.save()

    try:
        # Passo 1: Carregando questões (5% - muito rápido)
        update_progress(1, 'Carregando questões do simulado...', 5)
        time.sleep(0.3)

        questoes = list(simulado.questoes.all().order_by('questaosimulado__ordem'))

        if len(questoes) > 45:
            complete_progress(False, 'O simulado não pode ter mais que 45 questões')
            return JsonResponse({'status': 'error'})

        if not questoes:
            complete_progress(False, 'Simulado não possui questões')
            return JsonResponse({'status': 'error'})

        # Passo 2: Preparando ambiente (8% - rápido)
        update_progress(2, 'Preparando ambiente de geração...', 8)
        time.sleep(0.3)

        # Limpar cache
        simulado.limpar_todo_cache()

        # Detectar ambiente
        IS_PYTHONANYWHERE = 'pythonanywhere' in os.environ.get('HOSTNAME', '')
        if IS_PYTHONANYWHERE:
            socket.setdefaulttimeout(300)

        # Passo 3: Gerando HTMLs das versões (8% a 15% - rápido)
        update_progress(3, 'Gerando HTMLs das 5 versões embaralhadas...', 8)

        with tempfile.TemporaryDirectory() as tmpdirname:
            htmls_versoes = []
            embaralhamentos = [None] * 5
            cartoes_resposta = [None] * 5

            # 🆕 Criar versão ANTES do loop para ter o código disponível
            nova_versao = VersaoGabarito.objects.create(
                simulado=simulado,
                gabaritos_gerados=[],  # Será preenchido depois
                usuario_geracao=request.user,
                total_questoes=len(questoes)
            )
            versao_codigo = nova_versao.get_versao_curta()  # Ex: "55569AFD"

            # Gerar HTML de cada versão sequencialmente
            for versao in range(1, 6):
                percent = 8 + (versao * 1.4)
                update_progress(3, f'Gerando HTML da versão {versao} de 5...', int(percent))

                try:
                    # 🆕 PASSAR O CÓDIGO DA VERSÃO
                    html_versao, embaralhamento = _gerar_versao_simulado(
                        simulado, questoes, tmpdirname, versao, versao_codigo
                    )
                    htmls_versoes.append(html_versao)
                    embaralhamentos[versao-1] = embaralhamento
                except Exception as e:
                    nova_versao.delete()  # Limpar se falhar
                    complete_progress(False, f'Erro ao gerar HTML da versão {versao}: {str(e)}')
                    return JsonResponse({'status': 'error'})

            # Passo 4: ETAPA MAIS LENTA - Gerando PDF único (15% a 85% - MUY LENTO)
            update_progress(4, 'Combinando versões em PDF único... (Esta etapa demora mais)', 15)

            # Sub-etapas durante a geração do PDF único para dar feedback
            pdf_thread_running = True
            def update_pdf_progress():
                """Thread para simular progresso durante geração do PDF"""
                start_time = time.time()  # AGORA time ESTÁ IMPORTADO CORRETAMENTE
                while pdf_thread_running:
                    elapsed = time.time() - start_time
                    # Progressão mais lenta e realista: 15% -> 85% em ~3 minutos
                    if elapsed < 30:  # Primeiros 30s: 15% -> 25%
                        progress = 15 + (elapsed / 30) * 10
                    elif elapsed < 120:  # 30s-2min: 25% -> 70%
                        progress = 25 + ((elapsed - 30) / 90) * 45
                    elif elapsed < 180:  # 2min-3min: 70% -> 85%
                        progress = 70 + ((elapsed - 120) / 60) * 15
                    else:  # Após 3min: manter 85%
                        progress = 85

                    if progress <= 85:  # Não passar de 85% nesta thread
                        update_progress(4, 'Combinando versões em PDF único... (Esta etapa demora mais)', int(progress))

                    time.sleep(2)  # Atualizar a cada 2 segundos

            # Iniciar thread de progresso
            progress_thread = threading.Thread(target=update_pdf_progress)
            progress_thread.daemon = True
            progress_thread.start()

            try:
                pdf_unico_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_todas_versoes.pdf')
                _combinar_pdfs_versoes(htmls_versoes, pdf_unico_path, simulado, versao_codigo)
            except Exception as e:
                pdf_thread_running = False
                complete_progress(False, f'Erro ao gerar PDF único: {str(e)}')
                return JsonResponse({'status': 'error'})
            finally:
                pdf_thread_running = False
                progress_thread.join(timeout=1)

            # PDF gerado com sucesso
            update_progress(4, 'PDF único gerado com sucesso!', 85)
            time.sleep(0.5)

            # Passo 5: Gerando cartões resposta (88% - rápido)
            update_progress(5, 'Gerando cartões de resposta...', 88)
            time.sleep(0.5)

            for versao in range(1, 6):
                try:
                    # 🆕 PASSAR O CÓDIGO DA VERSÃO
                    cartao_path = _gerar_cartao_resposta(
                        tmpdirname, versao, versao, len(questoes), versao_codigo
                    )
                    cartoes_resposta[versao-1] = cartao_path
                except Exception as e:
                    nova_versao.delete()
                    complete_progress(False, f'Erro ao gerar cartão resposta {versao}: {str(e)}')
                    return JsonResponse({'status': 'error'})

            # Passo 6: Combinando cartões (92% - rápido)
            update_progress(6, 'Combinando cartões de resposta...', 92)
            time.sleep(0.3)

            cartoes_pdf_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_cartoes_resposta.pdf')
            _combinar_pdfs_simples(cartoes_resposta, cartoes_pdf_path)

            # Passo 7: Salvando gabaritos (95% - rápido)
            update_progress(7, 'Salvando gabaritos...', 95)
            time.sleep(0.3)

            nova_versao.gabaritos_gerados = embaralhamentos
            nova_versao.save()

            simulado.versao_gabarito_oficial = nova_versao
            simulado.save()

            # Passo 8: Criando arquivo final (98% - rápido)
            update_progress(8, 'Criando arquivo ZIP...', 98)
            time.sleep(0.3)

            versao_nome = nova_versao.get_versao_curta()
            zip_path = os.path.join(tmpdirname, f'simulado_{simulado.pk}_materiais_{versao_nome}.zip')

            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(pdf_unico_path, os.path.basename(pdf_unico_path))
                zipf.write(cartoes_pdf_path, os.path.basename(cartoes_pdf_path))

                # README
                readme_path = os.path.join(tmpdirname, 'README.txt')
                with open(readme_path, 'w', encoding='utf-8') as readme:
                    readme.write(f"""SIMULADO: {simulado.titulo}
VERSÃO: {versao_nome}
GERADO EM: {nova_versao.data_geracao.strftime('%d/%m/%Y às %H:%M')}

Este pacote contém um único PDF com as 5 versões embaralhadas sequencialmente.

CONTEÚDO:
- simulado_{simulado.pk}_todas_versoes.pdf: PDF único com 5 versões
- simulado_{simulado.pk}_cartoes_resposta.pdf: Cartões de resposta
""")
                zipf.write(readme_path, 'README.txt')

            # Passo 9: Finalizando (99% - rápido)
            update_progress(9, 'Finalizando...', 99)
            time.sleep(0.3)

            # Ler arquivo e preparar download
            with open(zip_path, 'rb') as f:
                zip_content = f.read()

            # 🆕 CRIAR NOME DE ARQUIVO BASEADO NO TÍTULO DO SIMULADO
            import re
            titulo_limpo = re.sub(r'[^\w\s-]', '', simulado.titulo)  # Remove caracteres especiais
            titulo_limpo = re.sub(r'[-\s]+', '_', titulo_limpo)  # Substitui espaços por underscore
            titulo_limpo = titulo_limpo[:50]  # Limitar a 50 caracteres

            # Salvar arquivo temporariamente para download
            temp_file_key = f'temp_file_{pk}_{int(time.time())}'
            request.session[temp_file_key] = {
                'content': base64.b64encode(zip_content).decode('utf-8'),
                'filename': f'{titulo_limpo}_{versao_nome}.zip'  # 🆕 MODIFICADO AQUI
            }

            download_url = reverse('questions:download_temp_file', kwargs={'key': temp_file_key})
            complete_progress(True, None, download_url)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        complete_progress(False, str(e))
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def download_temp_file(request, key):
    """Download de arquivo temporário da sessão."""
    file_data = request.session.get(key)
    if not file_data:
        raise Http404("Arquivo não encontrado")

    content = base64.b64decode(file_data['content'])
    filename = file_data['filename']

    # Limpar da sessão
    del request.session[key]

    response = HttpResponse(content, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response