#api/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.models import Resultado, DetalhesResposta
from classes.models import Class, Student
from questions.models import Questao, Simulado, QuestaoSimulado
from .serializers import (
    ClassSerializer, StudentSerializer, QuestaoSerializer,
    SimuladoSerializer, CartaoRespostaSerializer, ResultadoSerializer,
    DetalhesRespostaSerializer, DashboardAlunoSerializer
)
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Sum, F, Q
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

class ClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar e detalhar turmas.
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas as turmas do usuário autenticado"""
        return Class.objects.filter(user=self.request.user).order_by('id')

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Retorna todos os alunos de uma turma específica"""
        turma = self.get_object()
        students = Student.objects.filter(classes=turma)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def simulados(self, request, pk=None):
        """Retorna todos os simulados associados a uma turma específica"""
        import json
        import os
        from django.conf import settings

        turma = self.get_object()
        simulados_qs = Simulado.objects.filter(classes=turma)

        # Filtrar simulados arquivados
        arquivados_path = os.path.join(settings.BASE_DIR, 'arquivados.json')
        arquivado_ids = []
        if os.path.exists(arquivados_path):
            with open(arquivados_path, 'r') as f:
                try:
                    arquivado_ids = json.load(f)
                except json.JSONDecodeError:
                    pass

        if arquivado_ids:
            simulados_qs = simulados_qs.exclude(id__in=arquivado_ids)

        serializer = SimuladoSerializer(simulados_qs, many=True)
        return Response(serializer.data)

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar e detalhar alunos.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas os alunos do usuário autenticado"""
        return Student.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def simulados(self, request, pk=None):
        """Retorna todos os simulados disponíveis para um aluno específico"""
        aluno = self.get_object()
        simulados = Simulado.objects.filter(classes__in=aluno.classes.all()).distinct()
        serializer = SimuladoSerializer(simulados, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resultados(self, request, pk=None):
        """Retorna todos os resultados de simulados de um aluno específico"""
        aluno = self.get_object()
        resultados = Resultado.objects.filter(aluno=aluno)
        serializer = ResultadoSerializer(resultados, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Retorna dados do dashboard de desempenho do aluno"""
        aluno = self.get_object()

        # Estatísticas gerais
        total_simulados = Resultado.objects.filter(aluno=aluno).count()
        media_geral = Resultado.objects.filter(aluno=aluno).aggregate(Avg('pontuacao'))['pontuacao__avg'] or 0

        # Desempenho por disciplina
        desempenho_disciplinas = []
        disciplinas = Questao.objects.values_list('disciplina', flat=True).distinct()

        for disciplina in disciplinas:
            # Calcular média por disciplina
            detalhes = DetalhesResposta.objects.filter(
                resultado__aluno=aluno,
                questao__disciplina=disciplina
            )

            total_questoes = detalhes.count()
            acertos = detalhes.filter(acertou=True).count()

            if total_questoes > 0:
                taxa_acerto = (acertos / total_questoes) * 100
            else:
                taxa_acerto = 0

            desempenho_disciplinas.append({
                'disciplina': disciplina,
                'total_questoes': total_questoes,
                'acertos': acertos,
                'taxa_acerto': taxa_acerto
            })

        # Evolução ao longo do tempo
        resultados_timeline = Resultado.objects.filter(aluno=aluno).order_by('data_correcao').values(
            'simulado__titulo', 'pontuacao', 'data_correcao'
        )

        dashboard_data = {
            'aluno': aluno.name,
            'total_simulados': total_simulados,
            'media_geral': media_geral,
            'desempenho_disciplinas': desempenho_disciplinas,
            'evolucao_timeline': list(resultados_timeline)
        }

        serializer = DashboardAlunoSerializer(data=dashboard_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class QuestaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar e detalhar questões.
    """
    queryset = Questao.objects.all()
    serializer_class = QuestaoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def por_disciplina(self, request):
        """Retorna questões filtradas por disciplina"""
        disciplina = request.query_params.get('disciplina', None)
        if disciplina:
            questoes = Questao.objects.filter(disciplina=disciplina)
            serializer = self.get_serializer(questoes, many=True)
            return Response(serializer.data)
        return Response({'error': 'Parâmetro disciplina é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

class SimuladoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar e detalhar simulados.
    """
    serializer_class = SimuladoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna simulados disponíveis para o usuário, excluindo os arquivados"""
        user = self.request.user

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
                    # O arquivo está vazio ou mal formatado, considera como lista vazia
                    pass

        # Obter simulados associados às turmas do usuário e excluir os arquivados
        queryset = Simulado.objects.filter(classes__user=user).distinct()
        if arquivado_ids:
            queryset = queryset.exclude(id__in=arquivado_ids)

        return queryset

    @action(detail=True, methods=['get'])
    def detalhes(self, request, pk=None):
        """Retorna detalhes completos do simulado incluindo número de questões e pontuação"""
        simulado = self.get_object()

        # Contar questões
        numero_questoes = simulado.questoes.count()

        # Dados básicos do simulado
        dados = {
            'id': simulado.id,
            'titulo': simulado.titulo,
            'descricao': simulado.descricao,
            'pontuacao_total': simulado.pontuacao_total,
            'numero_questoes': numero_questoes,
            'data_criacao': simulado.data_criacao,
            'ultima_modificacao': simulado.ultima_modificacao,
        }

        return Response(dados)

    @action(detail=True, methods=['get'])
    def gabarito(self, request, pk=None):
        """Retorna o gabarito de um simulado específico - CORRIGIDO"""
        simulado = self.get_object()

        # Obter os parâmetros da URL
        versao_param = request.query_params.get('versao', 'versao1')  # versao1, versao2, etc.
        tipo_prova = request.query_params.get('tipo', '1')  # 1, 2, 3, 4, 5

        # Mapear o tipo_prova para o índice correto (1 -> 0, 2 -> 1, etc.)
        versao_index = int(tipo_prova) - 1
        if versao_index < 0 or versao_index > 4:
            versao_index = 0

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"====== SOLICITAÇÃO DE GABARITO (CORRIGIDA) ======")
        logger.info(f"SIMULADO: ID={simulado.id}, TÍTULO={simulado.titulo}")
        logger.info(f"PARÂMETROS: versao={versao_param}, tipo={tipo_prova} -> índice={versao_index}")

        try:
            # CORREÇÃO PRINCIPAL: Usar versao_gabarito_oficial ao invés de gabaritos_gerados
            versao_oficial = simulado.versao_gabarito_oficial

            if versao_oficial and versao_oficial.gabaritos_gerados:
                versoes_disponiveis = versao_oficial.gabaritos_gerados
                logger.info(f"VERSÃO OFICIAL ENCONTRADA: {versao_oficial.get_versao_curta()}")
                logger.info(f"VERSÕES DISPONÍVEIS: {len(versoes_disponiveis)}")

                # Verificar se o índice da versão é válido
                if versao_index < len(versoes_disponiveis):
                    versao_escolhida = versoes_disponiveis[versao_index]
                    logger.info(f"VERSÃO ESCOLHIDA: {versao_index+1} (índice {versao_index})")

                    gabarito_raw = versao_escolhida.get('gabarito', {})

                    # Processar o gabarito para extrair a resposta do tipo correto
                    gabarito = {}
                    for ordem, questao_data in gabarito_raw.items():
                        if isinstance(questao_data, dict):
                            # A resposta está aninhada sob a chave 'tipoX'
                            resposta = questao_data.get(f'tipo{tipo_prova}', questao_data.get('tipo1', ''))
                        else:
                            # Fallback para estruturas mais antigas/simples
                            resposta = str(questao_data)
                        gabarito[ordem] = resposta

                    logger.info(f"GABARITO PROCESSADO (Versão {versao_index+1}, Tipo {tipo_prova}): {gabarito}")
                else:
                    # Se o índice estiver fora do intervalo, usar a primeira versão disponível
                    logger.warning(f"ÍNDICE {versao_index} FORA DO INTERVALO, USANDO VERSÃO 1")
                    versao_escolhida = versoes_disponiveis[0]
                    gabarito_raw = versao_escolhida.get('gabarito', {})

                    gabarito = {}
                    for ordem, questao_data in gabarito_raw.items():
                        if isinstance(questao_data, dict):
                            resposta = questao_data.get('tipo1', '')
                        else:
                            resposta = str(questao_data)
                        gabarito[ordem] = resposta

                    logger.warning(f"GABARITO ALTERNATIVO USADO: {gabarito}")
            else:
                # Se não houver versão oficial ou gabaritos gerados, usar o método antigo
                logger.warning(f"SEM VERSÃO OFICIAL OU GABARITOS GERADOS")
                questoes_simulado = QuestaoSimulado.objects.filter(simulado=simulado).order_by('ordem')
                gabarito = {str(item.ordem): item.questao.resposta_correta for item in questoes_simulado}
                logger.warning(f"USANDO GABARITO PADRÃO (SEM EMBARALHAMENTO): {gabarito}")

        except Exception as e:
            logger.error(f"ERRO AO RECUPERAR GABARITO: {str(e)}")
            import traceback
            logger.error(f"TRACEBACK: {traceback.format_exc()}")

            # Fallback em caso de erro
            questoes_simulado = QuestaoSimulado.objects.filter(simulado=simulado).order_by('ordem')
            gabarito = {str(item.ordem): item.questao.resposta_correta for item in questoes_simulado}
            logger.warning(f"USANDO GABARITO DE FALLBACK: {gabarito}")

        # Log final do gabarito que será enviado
        logger.info(f"GABARITO FINAL ENVIADO: {gabarito}")
        logger.info(f"========== FIM DA SOLICITAÇÃO ==========")

        return Response({
            'simulado_id': simulado.id,
            'titulo': simulado.titulo,
            'versao': versao_param,
            'tipo_prova': tipo_prova,
            'gabarito': gabarito,
            'versao_oficial': versao_oficial.get_versao_curta() if versao_oficial else None
        })

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Arquiva um simulado adicionando seu ID a um arquivo JSON."""
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

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

        if simulado.id not in arquivado_ids:
            arquivado_ids.append(simulado.id)
            with open(arquivados_path, 'w') as f:
                json.dump(arquivado_ids, f)
            return Response({'status': 'simulado arquivado'}, status=status.HTTP_200_OK)

        return Response({'status': 'simulado já arquivado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Desarquiva um simulado removendo seu ID do arquivo JSON."""
        simulado = get_object_or_404(Simulado, pk=pk, professor=request.user)

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

        if simulado.id in arquivado_ids:
            arquivado_ids.remove(simulado.id)
            with open(arquivados_path, 'w') as f:
                json.dump(arquivado_ids, f)
            return Response({'status': 'simulado desarquivado'}, status=status.HTTP_200_OK)

        return Response({'status': 'simulado não estava arquivado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def corrigir(self, request, pk=None):
        """Corrige um simulado baseado nas respostas enviadas"""
        simulado = self.get_object()
        serializer = CartaoRespostaSerializer(data=request.data)

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"====== INÍCIO DE CORREÇÃO DE SIMULADO ======")

        if serializer.is_valid():
            aluno_id = serializer.validated_data['aluno_id']
            respostas = serializer.validated_data['respostas']
            # Obter versão e tipo de prova dos parâmetros
            versao = request.data.get('versao', 'versao1')
            tipo_prova = request.data.get('tipo_prova', '1')

            logger.info(f"CORREÇÃO DE SIMULADO - ID: {simulado.id}, TÍTULO: {simulado.titulo}")
            logger.info(f"PARÂMETROS RECEBIDOS - Aluno: {aluno_id}, Versão: {versao}, Tipo: {tipo_prova}")
            logger.info(f"RESPOSTAS RECEBIDAS DO ALUNO: {respostas}")

            try:
                aluno = Student.objects.get(id=aluno_id)
                logger.info(f"ALUNO ENCONTRADO: ID={aluno.id}, NOME={aluno.name}")
            except Student.DoesNotExist:
                logger.error(f"ALUNO NÃO ENCONTRADO: ID={aluno_id}")
                return Response({'error': 'Aluno não encontrado'}, status=status.HTTP_404_NOT_FOUND)

            # Lógica de correção
            resultado = self.processar_correcao(simulado, aluno, respostas, versao=versao, tipo_prova=tipo_prova)
            logger.info(f"CORREÇÃO FINALIZADA")
            logger.info(f"========== FIM DA CORREÇÃO ==========")

            return Response(resultado)
        else:
            logger.error(f"DADOS INVÁLIDOS: {serializer.errors}")
            logger.info(f"========== FIM DA CORREÇÃO COM ERRO ==========")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def processar_correcao(self, simulado, aluno, respostas, versao='versao1', tipo_prova='1'):
        """Processa a correção do simulado e salva os resultados - CORRIGIDO"""
        import logging
        logger = logging.getLogger(__name__)

        # Mapear o parâmetro 'tipo_prova' para o índice correto (1 -> 0, 2 -> 1, etc.)
        versao_index = int(tipo_prova) - 1
        if versao_index < 0 or versao_index > 4:
            versao_index = 0

        logger.info(f"====== PROCESSANDO CORREÇÃO (CORRIGIDA) ======")
        logger.info(f"SIMULADO: ID={simulado.id}, TÍTULO={simulado.titulo}")
        logger.info(f"ALUNO: ID={aluno.id}, NOME={aluno.name}")
        logger.info(f"VERSÃO: {versao}, TIPO/ÍNDICE: {tipo_prova} -> {versao_index}")

        try:
            # CORREÇÃO PRINCIPAL: Usar versao_gabarito_oficial
            versao_oficial = simulado.versao_gabarito_oficial

            if versao_oficial and versao_oficial.gabaritos_gerados:
                versoes_disponiveis = versao_oficial.gabaritos_gerados
                logger.info(f"VERSÃO OFICIAL ENCONTRADA: {versao_oficial.get_versao_curta()}")
                logger.info(f"VERSÕES DISPONÍVEIS: {len(versoes_disponiveis)}")

                # Verificar se o índice da versão é válido
                if versao_index < len(versoes_disponiveis):
                    versao_escolhida = versoes_disponiveis[versao_index]
                    logger.info(f"VERSÃO ESCOLHIDA: {versao_index+1} (índice {versao_index})")

                    gabarito_raw = versao_escolhida.get('gabarito', {})

                    # Processar o gabarito
                    gabarito = {}
                    for ordem, questao_data in gabarito_raw.items():
                        if isinstance(questao_data, dict):
                            # Usar o tipo específico ou tipo1 como fallback
                            resposta = questao_data.get(f'tipo{tipo_prova}', questao_data.get('tipo1', ''))
                        else:
                            resposta = str(questao_data)
                        gabarito[ordem] = resposta

                    logger.info(f"GABARITO USADO PARA CORREÇÃO (Versão {versao_index+1}): {gabarito}")
                else:
                    # Se o índice estiver fora do intervalo, usar a primeira versão disponível
                    logger.warning(f"ÍNDICE DE VERSÃO {versao_index} FORA DO INTERVALO, USANDO VERSÃO 1")
                    versao_escolhida = versoes_disponiveis[0]
                    gabarito_raw = versao_escolhida.get('gabarito', {})

                    gabarito = {}
                    for ordem, questao_data in gabarito_raw.items():
                        if isinstance(questao_data, dict):
                            resposta = questao_data.get('tipo1', '')
                        else:
                            resposta = str(questao_data)
                        gabarito[ordem] = resposta

                    logger.warning(f"GABARITO ALTERNATIVO USADO: {gabarito}")
            else:
                # Se não houver versão oficial, usar o método antigo
                logger.warning(f"SEM VERSÃO OFICIAL OU GABARITOS GERADOS")
                questoes_simulado = QuestaoSimulado.objects.filter(simulado=simulado).order_by('ordem')
                gabarito = {str(item.ordem): item.questao.resposta_correta for item in questoes_simulado}
                logger.warning(f"USANDO GABARITO PADRÃO: {gabarito}")
        except Exception as e:
            logger.error(f"ERRO AO RECUPERAR GABARITO: {str(e)}")
            import traceback
            logger.error(f"TRACEBACK: {traceback.format_exc()}")

            # Fallback em caso de erro
            questoes_simulado = QuestaoSimulado.objects.filter(simulado=simulado).order_by('ordem')
            gabarito = {str(item.ordem): item.questao.resposta_correta for item in questoes_simulado}
            logger.warning(f"USANDO GABARITO DE FALLBACK DEVIDO A ERRO: {gabarito}")

        # Calcular pontuação e detalhes
        total_questoes = len(gabarito)
        acertos = 0
        detalhes = []

        logger.info(f"====== COMPARANDO RESPOSTAS DO ALUNO COM GABARITO ======")
        logger.info(f"RESPOSTAS DO ALUNO: {respostas}")
        logger.info(f"GABARITO PARA COMPARAÇÃO: {gabarito}")

        for ordem, resposta_aluno in respostas.items():
            resposta_correta = gabarito.get(ordem)
            if resposta_correta is None:
                logger.warning(f"⚠️ Questão {ordem} não encontrada no gabarito!")
                continue

            acertou = resposta_aluno == resposta_correta

            # Log detalhado para depuração
            logger.info(f"Questão {ordem}: Aluno={resposta_aluno}, Correta={resposta_correta}, Acertou={acertou}")

            if acertou:
                acertos += 1

            # Obter dados da questão
            try:
                questao_simulado = QuestaoSimulado.objects.get(simulado=simulado, ordem=int(ordem))
                questao = questao_simulado.questao
                disciplina = questao.disciplina
                logger.info(f"Questão {ordem}: ID={questao.id}, Disciplina={disciplina}")
            except QuestaoSimulado.DoesNotExist:
                logger.error(f"⚠️ QuestaoSimulado não encontrada para ordem {ordem}")
                disciplina = "Não identificada"
                questao = None

            detalhes.append({
                'ordem': ordem,
                'questao_id': questao.id if questao else None,
                'disciplina': disciplina,
                'resposta_aluno': resposta_aluno,
                'resposta_correta': resposta_correta,
                'acertou': acertou
            })

        pontuacao = (acertos / total_questoes) * 100 if total_questoes > 0 else 0

        logger.info(f"====== RESULTADO FINAL ======")
        logger.info(f"ACERTOS: {acertos}/{total_questoes}, PONTUAÇÃO: {pontuacao}%")

        # Salvar o resultado no banco
        try:
            resultado = Resultado.objects.create(
                aluno=aluno,
                simulado=simulado,
                pontuacao=pontuacao,
                total_questoes=total_questoes,
                acertos=acertos,
                data_correcao=timezone.now()
            )
            # Tentar salvar versão e tipo se o modelo suportar esses campos
            if hasattr(Resultado, 'versao'):
                resultado.versao = versao
            if hasattr(Resultado, 'tipo_prova'):
                resultado.tipo_prova = tipo_prova
            resultado.save()

            logger.info(f"RESULTADO SALVO NO BANCO. ID={resultado.id}")

            # Salvar detalhes de cada resposta
            for detalhe in detalhes:
                if detalhe['questao_id']:
                    try:
                        questao = Questao.objects.get(id=detalhe['questao_id'])
                        DetalhesResposta.objects.create(
                            resultado=resultado,
                            questao=questao,
                            ordem=detalhe['ordem'],
                            resposta_aluno=detalhe['resposta_aluno'],
                            resposta_correta=detalhe['resposta_correta'],
                            acertou=detalhe['acertou']
                        )
                        logger.info(f"Detalhe salvo para questão {detalhe['ordem']}")
                    except Exception as e:
                        logger.error(f"Erro ao salvar detalhe da questão {detalhe['ordem']}: {str(e)}")
        except Exception as e:
            logger.error(f"ERRO AO SALVAR RESULTADO: {str(e)}")
            import traceback
            logger.error(f"TRACEBACK: {traceback.format_exc()}")

        # Montando o objeto de retorno com os resultados
        resultado_final = {
            'id': resultado.id if 'resultado' in locals() else None,
            'aluno': aluno.name,
            'simulado': simulado.titulo,
            'versao': versao,
            'tipo_prova': tipo_prova,
            'pontuacao': pontuacao,
            'acertos': acertos,
            'total_questoes': total_questoes,
            'data_correcao': resultado.data_correcao if 'resultado' in locals() else timezone.now(),
            'detalhes': detalhes
        }

        logger.info(f"====== FIM DO PROCESSAMENTO DE CORREÇÃO ======")

        return resultado_final

class CustomAuthToken(ObtainAuthToken):
    """
    API para autenticação e obtenção de token.
    Retorna o token junto com informações do usuário.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'name': user.get_full_name() or user.username,
            'is_staff': user.is_staff
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def test_connection(request):
    """Endpoint simples para testar a conexão com a API"""
    return Response({"message": "Conexão bem-sucedida!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """Retorna informações do usuário autenticado"""
    user = request.user
    return Response({
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'is_staff': user.is_staff
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def app_config(request):
    """Endpoint para fornecer configurações para o aplicativo mobile"""
    disciplines = Questao.objects.values_list('disciplina', flat=True).distinct()
    classes = Class.objects.count()
    simulados = Simulado.objects.count()

    return Response({
        'disciplines': list(disciplines),
        'total_classes': classes,
        'total_simulados': simulados,
        'api_version': '1.0.0',
        'app_info': {
            'min_version': '1.0.0',
            'current_version': '1.0.0',
            'update_required': False
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def procesar_cartao_resposta(request):
    """Endpoint para receber dados de cartão resposta já processados pelo app Flutter"""
    if not all(key in request.data for key in ['simulado_id', 'aluno_id', 'respostas']):
        return Response({'error': 'Dados incompletos'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        simulado = Simulado.objects.get(id=request.data['simulado_id'])
        aluno = Student.objects.get(id=request.data['aluno_id'])
    except (Simulado.DoesNotExist, Student.DoesNotExist):
        return Response({'error': 'Simulado ou aluno não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Delegar a lógica de correção para o método do SimuladoViewSet
    viewset = SimuladoViewSet()
    resultado = viewset.processar_correcao(simulado, aluno, request.data['respostas'])

    return Response(resultado)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_classes(request):
    """
    Endpoint simplificado para listar todas as turmas do usuário.
    Útil para o app Flutter na tela de seleção.
    """
    classes = Class.objects.filter(user=request.user).order_by('name')
    serializer = ClassSerializer(classes, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_class_students(request, class_id):
    """
    Endpoint simplificado para listar alunos de uma turma específica.
    Útil para o app Flutter na tela de seleção.
    """
    try:
        class_obj = Class.objects.get(id=class_id, user=request.user)
        students = Student.objects.filter(classes=class_obj).order_by('name')
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    except Class.DoesNotExist:
        return Response({"error": "Turma não encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_class_simulados(request, class_id):
    """
    Endpoint simplificado para listar simulados de uma turma específica.
    Útil para o app Flutter na tela de seleção.
    """
    try:
        class_obj = Class.objects.get(id=class_id, user=request.user)
        simulados = Simulado.objects.filter(classes=class_obj).order_by('-data_criacao')
        serializer = SimuladoSerializer(simulados, many=True)
        return Response(serializer.data)
    except Class.DoesNotExist:
        return Response({"error": "Turma não encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def debug_token_request(request):
    """Debug view for token requests"""
    return Response({
        'received_data': request.data,
        'content_type': request.content_type,
        'auth_header': request.META.get('HTTP_AUTHORIZATION', None),
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_resultado(request):
    """Endpoint para receber resultados de simulados do aplicativo Flutter e sincronizar com o dashboard"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("====== RECEBENDO RESULTADO DO APP FLUTTER ======")

    try:
        # Obter dados do request
        data = request.data
        aluno_id = data.get('aluno_id')
        simulado_id = data.get('simulado_id')
        versao = data.get('versao', 'versao1')
        nota_final = data.get('nota_final', 0.0)
        respostas_aluno = data.get('respostas_aluno', {})
        gabarito = data.get('gabarito', {})

        # Log para depuração
        logger.info(f"Dados recebidos: aluno={aluno_id}, simulado={simulado_id}, versao={versao}")
        logger.info(f"Nota final: {nota_final}")

        # Verificar dados obrigatórios
        if not aluno_id or not simulado_id:
            logger.error("Dados incompletos: ID do aluno e do simulado são obrigatórios")
            return Response(
                {"error": "Dados incompletos: ID do aluno e do simulado são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar se aluno e simulado existem
        try:
            aluno = Student.objects.get(id=aluno_id)
            simulado = Simulado.objects.get(id=simulado_id)

            logger.info(f"Aluno encontrado: {aluno.name}, Simulado: {simulado.titulo}")
        except Student.DoesNotExist:
            logger.error(f"Aluno com ID {aluno_id} não encontrado")
            return Response(
                {"error": f"Aluno com ID {aluno_id} não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Simulado.DoesNotExist:
            logger.error(f"Simulado com ID {simulado_id} não encontrado")
            return Response(
                {"error": f"Simulado com ID {simulado_id} não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar respostas e calcular acertos
        acertos = 0
        total_questoes = len(gabarito)

        for questao, resposta_aluno in respostas_aluno.items():
            resposta_correta = gabarito.get(questao)
            if resposta_aluno == resposta_correta:
                acertos += 1

        # Processar a versão para armazenamento
        if versao.startswith('versao'):
            tipo_prova = versao.replace('versao', '')
        else:
            tipo_prova = '1'

        # 1. Salvar no modelo Resultado (usado pela API)
        resultado = Resultado.objects.create(
            aluno=aluno,
            simulado=simulado,
            pontuacao=float(nota_final),
            total_questoes=total_questoes,
            acertos=acertos,
            versao=versao,
            tipo_prova=tipo_prova
        )

        logger.info(f"Resultado salvo com sucesso no modelo Resultado. ID={resultado.id}, Versão={versao}")

        # Salvar detalhes das respostas
        detalhes_salvos = 0
        for questao, resposta_aluno in respostas_aluno.items():
            resposta_correta = gabarito.get(questao)
            acertou = resposta_aluno == resposta_correta

            try:
                # Encontrar a questão correspondente no simulado
                questao_simulado = QuestaoSimulado.objects.filter(
                    simulado=simulado,
                    ordem=int(questao)
                ).first()

                if questao_simulado:
                    questao_obj = questao_simulado.questao

                    DetalhesResposta.objects.create(
                        resultado=resultado,
                        questao=questao_obj,
                        ordem=questao,
                        resposta_aluno=resposta_aluno,
                        resposta_correta=resposta_correta,
                        acertou=acertou
                    )
                    detalhes_salvos += 1
            except Exception as e:
                logger.error(f"Erro ao salvar detalhe da questão {questao}: {str(e)}")

        logger.info(f"Detalhes de resposta salvos: {detalhes_salvos}/{len(respostas_aluno)}")

        # 2. Sincronizar com o modelo StudentPerformance (usado pelo Dashboard)
        try:
            from classes.models import StudentPerformance, StudentAnswer

            # Criar ou atualizar o registro de desempenho
            performance, created = StudentPerformance.objects.update_or_create(
                student=aluno,
                simulado=simulado,
                defaults={
                    'score': float(nota_final),
                    'correct_answers': acertos,
                    'total_questions': total_questoes,
                    'versao': tipo_prova  # Salvar a versão como número (1, 2, 3, etc.)
                }
            )

            if created:
                logger.info(f"Novo registro de desempenho criado para o aluno {aluno.name} com versão {tipo_prova}")
            else:
                logger.info(f"Registro de desempenho atualizado para o aluno {aluno.name} com versão {tipo_prova}")

            # Sincronizar também as respostas individuais
            respostas_sincronizadas = 0
            for questao, resposta_aluno in respostas_aluno.items():
                resposta_correta = gabarito.get(questao)
                acertou = resposta_aluno == resposta_correta

                try:
                    questao_simulado = QuestaoSimulado.objects.filter(
                        simulado=simulado,
                        ordem=int(questao)
                    ).first()

                    if questao_simulado:
                        StudentAnswer.objects.update_or_create(
                            student=aluno,
                            simulado=simulado,
                            question=questao_simulado,
                            defaults={
                                'chosen_option': resposta_aluno,
                                'is_correct': acertou
                            }
                        )
                        respostas_sincronizadas += 1
                except Exception as e:
                    logger.error(f"Erro ao sincronizar resposta individual para questão {questao}: {str(e)}")

            logger.info(f"Sincronização com StudentPerformance concluída. Respostas sincronizadas: {respostas_sincronizadas}")

        except Exception as e:
            import traceback
            logger.error(f"Erro na sincronização com StudentPerformance: {str(e)}")
            logger.error(traceback.format_exc())
            # Não impedir a resposta de sucesso se a sincronização falhar

        # Retornar resposta de sucesso
        logger.info("====== PROCESSAMENTO CONCLUÍDO COM SUCESSO ======")
        return Response({
            "success": True,
            "resultado_id": resultado.id,
            "performance_id": getattr(performance, 'id', None) if 'performance' in locals() else None,
            "mensagem": "Resultado salvo com sucesso e sincronizado com dashboard",
            "acertos": acertos,
            "total": total_questoes,
            "nota": float(nota_final),
            "versao_salva": tipo_prova  # Adicionar a versão na resposta
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        logger.error(f"Erro ao processar resultado: {str(e)}")
        logger.error(traceback.format_exc())
        logger.info("====== PROCESSAMENTO FALHOU ======")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

