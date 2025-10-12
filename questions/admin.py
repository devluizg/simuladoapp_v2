# questions/admin.py
from django.contrib import admin
from django.db import models  # Adicionado este import
from .models import Questao, Simulado, QuestaoSimulado, VersaoGabarito, Resultado, DetalhesResposta

@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'disciplina', 'conteudo', 'tipo_questao_display', 'nivel_dificuldade', 'data_criacao']
    list_filter = ['disciplina', 'nivel_dificuldade', 'professor', 'data_criacao']
    search_fields = ['disciplina', 'conteudo', 'enunciado']
    readonly_fields = ['data_criacao', 'ultima_modificacao']

    fieldsets = (
        ('Tipo da Questão', {
            'fields': ('professor',),
            'description': '<strong>IMPORTANTE:</strong> Para criar questões públicas (visíveis para todos), deixe o campo "Professor" VAZIO. Para questões privadas, selecione um professor.',
            'classes': ('wide',)
        }),
        ('Identificação', {
            'fields': ('disciplina', 'conteudo', 'nivel_dificuldade')
        }),
        ('Conteúdo da Questão', {
            'fields': ('enunciado', 'imagem')
        }),
        ('Alternativas', {
            'fields': ('alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e')
        }),
        ('Resposta', {
            'fields': ('resposta_correta',)
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'ultima_modificacao'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """Personaliza a queryset baseada nas permissões do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            # Superusuários veem todas as questões
            return qs
        elif request.user.is_staff:
            # Staff vê questões públicas + suas próprias
            return qs.filter(
                models.Q(professor__isnull=True) | models.Q(professor=request.user)
            )
        else:
            # Usuários normais não acessam o admin
            return qs.none()

    def save_model(self, request, obj, form, change):
        """Personaliza o salvamento para questões"""
        # Se não foi definido professor, criar como questão pública
        if not obj.professor:
            # Questão pública - não fazer nada especial
            pass
        elif not change:  # Se é criação nova e tem professor
            # Manter o professor selecionado
            pass

        super().save_model(request, obj, form, change)

    def tipo_questao_display(self, obj):
        """Exibe o tipo da questão na listagem"""
        if obj.professor:
            return f"Privada ({obj.professor.username})"
        else:
            return "📢 Pública"
    tipo_questao_display.short_description = 'Tipo'

    def has_module_permission(self, request):
        """Permite acesso ao módulo apenas para staff"""
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        """Controla permissão de edição"""
        if not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Staff pode editar questões públicas ou próprias
        return obj.professor is None or obj.professor == request.user

    def has_delete_permission(self, request, obj=None):
        """Controla permissão de exclusão"""
        if not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Staff pode excluir questões públicas ou próprias
        return obj.professor is None or obj.professor == request.user


@admin.register(Simulado)
class SimuladoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'professor', 'data_criacao', 'total_questoes']
    list_filter = ['professor', 'data_criacao']
    search_fields = ['titulo', 'descricao']
    readonly_fields = ['data_criacao', 'ultima_modificacao']

    def get_queryset(self, request):
        """Staff só vê próprios simulados, superuser vê todos"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(professor=request.user)

    def total_questoes(self, obj):
        """Mostra total de questões no simulado"""
        return obj.questoes.count()
    total_questoes.short_description = 'Total de Questões'


# Registro dos demais modelos (apenas para superusuários)
@admin.register(VersaoGabarito)
class VersaoGabaritoAdmin(admin.ModelAdmin):
    list_display = ['get_versao_curta', 'simulado', 'usuario_geracao', 'data_geracao', 'total_questoes']
    list_filter = ['data_geracao', 'usuario_geracao']
    readonly_fields = ['versao_id', 'data_geracao', 'gabaritos_gerados']

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'simulado', 'pontuacao', 'acertos', 'total_questoes', 'data_correcao']
    list_filter = ['simulado', 'data_correcao']
    readonly_fields = ['data_correcao']

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(DetalhesResposta)
class DetalhesRespostaAdmin(admin.ModelAdmin):
    list_display = ['resultado', 'questao', 'ordem', 'resposta_aluno', 'resposta_correta', 'acertou']
    list_filter = ['acertou', 'resposta_correta']

    def has_module_permission(self, request):
        return request.user.is_superuser


# Configuração adicional do admin
admin.site.site_header = "SimuladoApp - Administração"
admin.site.site_title = "SimuladoApp Admin"
admin.site.index_title = "Painel de Administração"