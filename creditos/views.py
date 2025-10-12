from rest_framework import status
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .models import CreditoUsuario, CompraCredito
from .serializers import (
    CreditoUsuarioSerializer,
    AdicionarCreditosSerializer,
    UsarCreditoSerializer,
    ComprarCreditosSerializer
)
from .services import GooglePlayValidationService

logger = logging.getLogger(__name__)

# Mapeamento de produtos para créditos
PRODUTOS_CREDITOS = {
    'starter_300_creditos': 300,
    'professor_ativo_800_creditos': 800,
    'escola_pequena_2000_creditos': 2000,
    'escola_profissional_5000_creditos': 5000,
}

@login_required
def pagina_creditos(request):
    """
    View para exibir a página principal de créditos do usuário.
    Mostra o saldo atual, planos disponíveis e informações do sistema.
    """
    context = {
        'user_creditos': request.user.creditos if hasattr(request.user, 'creditos') else 0,
        'page_title': 'Meus Créditos',
        'planos': [
            {
                'nome': 'Iniciante',
                'creditos': 300,
                'preco': 14.90,
                'preco_por_correcao': 0.05,
                'descricao': 'Professores com 1 turma',
                'ideal_para': '40-300 correções',
                'cor': 'primary'
            },
            {
                'nome': 'Essencial',
                'creditos': 800,
                'preco': 29.90,
                'preco_por_correcao': 0.037,
                'descricao': 'Professores com 2-3 turmas',
                'ideal_para': '100-800 correções',
                'cor': 'success',
                'mais_popular': True,
                'economia': 25
            },
            {
                'nome': 'Profissional',
                'creditos': 2000,
                'preco': 59.90,
                'preco_por_correcao': 0.029,
                'descricao': 'Escolas ou grandes turmas',
                'ideal_para': '300+ correções',
                'cor': 'warning',
                'economia': 40
            }
        ]
    }

    return render(request, 'creditos/pagina_creditos.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consultar_creditos(request):
    """
    GET /api/creditos/
    Retorna os créditos do usuário autenticado.
    Cria registro automaticamente se não existir.
    """
    try:
        # ✅ CORREÇÃO: get_or_create para criar registro se não existir
        credito_usuario, created = CreditoUsuario.objects.get_or_create(
            user=request.user,
            defaults={
                'total_creditos': 0,
                'usados_creditos': 0
            }
        )

        if created:
            logger.info(f"Registro de créditos criado para usuário: {request.user.username}")

        serializer = CreditoUsuarioSerializer(credito_usuario)
        data = serializer.data

        # ✅ ADICIONAR campos compatíveis com Flutter
        data['available_credits'] = data['creditos_restantes']
        data['used_credits'] = data['usados_creditos']
        data['total_credits'] = data['total_creditos']
        data['last_updated'] = data['updated_at']

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erro ao consultar créditos para {request.user.username}: {e}")
        return Response(
            {'error': 'Erro ao carregar créditos', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def adicionar_creditos(request):
    """
    POST /api/adicionar_creditos/
    Adiciona créditos ao usuário autenticado.
    Body: {"quantidade": 10}
    """
    serializer = AdicionarCreditosSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    quantidade = serializer.validated_data['quantidade']

    # Usar get_or_create para garantir que o registro existe
    credito_usuario, created = CreditoUsuario.objects.get_or_create(
        user=request.user,
        defaults={
            'total_creditos': 0,
            'usados_creditos': 0
        }
    )

    if created:
        logger.info(f"Registro de créditos criado para usuário: {request.user.username}")

    credito_usuario.adicionar_creditos(quantidade)

    # Retorna os dados atualizados
    response_serializer = CreditoUsuarioSerializer(credito_usuario)

    return Response({
        'mensagem': f'{quantidade} créditos adicionados com sucesso!',
        'creditos': response_serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def usar_credito(request):
    """
    POST /api/users/credits/consume/
    Consome 1 crédito do usuário autenticado.
    Compatível com Flutter.
    """
    try:
        # Obter dados do request (compatível com Flutter)
        student_id = request.data.get('student_id')
        simulado_id = request.data.get('simulado_id')
        action = request.data.get('action', 'correction')

        # Verificar se os dados obrigatórios estão presentes
        if not student_id or not simulado_id:
            return Response(
                {'error': 'student_id e simulado_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Usar get_or_create para garantir que o registro existe
        credito_usuario, created = CreditoUsuario.objects.get_or_create(
            user=request.user,
            defaults={
                'total_creditos': 0,
                'usados_creditos': 0
            }
        )

        if created:
            logger.warning(f"Usuário {request.user.username} tentou usar crédito sem registro. Registro criado com 0 créditos.")
            return Response({
                'success': False,
                'remaining_credits': 0,
                'message': 'Você não possui créditos. Compre créditos no aplicativo mobile.'
            }, status=status.HTTP_403_FORBIDDEN)

        if not credito_usuario.pode_usar_credito():
            return Response({
                'success': False,
                'remaining_credits': credito_usuario.creditos_restantes,
                'message': 'Créditos insuficientes para realizar esta operação.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Usa o crédito
        sucesso = credito_usuario.usar_credito()

        if sucesso:
            return Response({
                'success': True,
                'message': 'Crédito consumido com sucesso',
                'remaining_credits': credito_usuario.creditos_restantes,
                'used_credits': credito_usuario.usados_creditos,
                'total_credits': credito_usuario.total_creditos
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'remaining_credits': credito_usuario.creditos_restantes,
                'message': 'Erro ao consumir crédito.'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Erro ao consumir crédito: {e}")
        return Response(
            {'error': f'Erro ao consumir crédito: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprar_creditos(request):
    """
    POST /api/comprar_creditos/
    Valida compra do Google Play e adiciona créditos ao usuário.

    Body: {
        "purchase_token": "abc123...",
        "produto_id": "creditos_800"
    }
    """
    serializer = ComprarCreditosSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {"erro": "Dados inválidos", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    purchase_token = serializer.validated_data['purchase_token']
    produto_id = serializer.validated_data['produto_id']
    quantidade_creditos = PRODUTOS_CREDITOS[produto_id]

    # Verificar se a compra já foi processada
    if CompraCredito.objects.filter(purchase_token=purchase_token).exists():
        logger.warning(f"Tentativa de reutilizar purchase_token: {purchase_token}")
        return Response(
            {"erro": "Compra já foi processada anteriormente"},
            status=status.HTTP_409_CONFLICT
        )

    # Validar com Google Play
    google_service = GooglePlayValidationService()
    is_valid, purchase_data = google_service.validate_purchase(produto_id, purchase_token)

    if not is_valid:
        logger.error(f"Compra inválida para {request.user.username}: {purchase_data}")
        return Response(
            {"erro": "Compra inválida ou já utilizada", "detalhes": purchase_data.get('error', '')},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Registrar a compra
            compra = CompraCredito.objects.create(
                user=request.user,
                purchase_token=purchase_token,
                produto_id=produto_id,
                quantidade_creditos=quantidade_creditos,
                validada_google=True
            )

            # Obter ou criar registro de créditos do usuário
            credito_usuario, created = CreditoUsuario.objects.get_or_create(
                user=request.user,
                defaults={'total_creditos': 0, 'usados_creditos': 0}
            )

            # Adicionar créditos
            credito_usuario.adicionar_creditos(quantidade_creditos)

            # Reconhecer a compra no Google Play
            google_service.acknowledge_purchase(produto_id, purchase_token)

            logger.info(
                f"Compra processada com sucesso: {request.user.username} - "
                f"{produto_id} - {quantidade_creditos} créditos"
            )

            return Response({
                "mensagem": "Créditos adicionados com sucesso",
                "creditos_atuais": credito_usuario.creditos_restantes,
                "creditos_adicionados": quantidade_creditos,
                "compra_id": compra.id
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erro ao processar compra: {e}")
        return Response(
            {"erro": "Erro interno ao processar compra"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_history(request):
    """
    GET /api/users/credits/history/
    Retorna histórico de transações de créditos
    """
    try:
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))

        # Buscar histórico de compras do usuário
        compras = CompraCredito.objects.filter(user=request.user).order_by('-data_compra')[offset:offset+limit]

        history_data = []
        for compra in compras:
            history_data.append({
                'id': compra.id,
                'transaction_type': 'purchase',
                'amount': compra.quantidade_creditos,
                'description': f'Compra de {compra.quantidade_creditos} créditos - {compra.produto_id}',
                'created_at': compra.data_compra.isoformat(),
                'product_id': compra.produto_id,
                'validated': compra.validada_google
            })

        return Response({
            'results': history_data,
            'count': CompraCredito.objects.filter(user=request.user).count(),
            'has_next': (offset + limit) < CompraCredito.objects.filter(user=request.user).count()
        })

    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return Response(
            {'error': f'Erro ao obter histórico: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_plans(request):
    """
    GET /api/credits/plans/
    Retorna planos de créditos disponíveis compatível com Flutter
    """
    try:
        plans = [
            {
                'id': 'starter_300_creditos',
                'localId': 'starter',
                'name': 'Starter',
                'credits': 300,
                'price': 14.90,
                'description': 'Ideal para professores iniciantes',
                'color': 'blue',
                'popular': False,
            },
            {
                'id': 'professor_ativo_800_creditos',
                'localId': 'professor_ativo',
                'name': 'Professor Ativo',
                'credits': 800,
                'price': 29.90,
                'description': 'Para uso regular em sala de aula',
                'color': 'green',
                'popular': True,
            },
            {
                'id': 'escola_pequena_2000_creditos',
                'localId': 'escola_pequena',
                'name': 'Escola Pequena',
                'credits': 2000,
                'price': 59.90,
                'description': 'Para escolas com até 200 alunos',
                'color': 'orange',
                'popular': False,
            },
            {
                'id': 'escola_profissional_5000_creditos',
                'localId': 'escola_profissional',
                'name': 'Escola Profissional',
                'credits': 5000,
                'price': 99.90,
                'description': 'Para instituições de ensino grandes',
                'color': 'purple',
                'popular': False,
            }
        ]

        return Response(plans)

    except Exception as e:
        logger.error(f"Erro ao obter planos: {e}")
        return Response(
            {'error': f'Erro ao obter planos: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )