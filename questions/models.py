from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from classes.models import Class
import uuid
from django.utils import timezone
import hashlib
import json


class Questao(models.Model):
    NIVEL_CHOICES = [
        ('F', 'Fácil'),
        ('M', 'Médio'),
        ('D', 'Difícil')
    ]

    # ✅ ÚNICA MUDANÇA: Professor agora pode ser NULL (para questões do admin)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questoes',
        null=True,  # ✅ Permite NULL para questões do administrador
        blank=True
    )

    disciplina = models.CharField(max_length=100)
    conteudo = models.CharField(max_length=100)
    enunciado = RichTextField()
    imagem = models.ImageField(
        upload_to='questoes/',
        null=True,
        blank=True,
        help_text='Imagens devem ter no máximo 5MB'
    )
    alternativa_a = RichTextField()
    alternativa_b = RichTextField()
    alternativa_c = RichTextField()
    alternativa_d = RichTextField()
    alternativa_e = RichTextField()
    resposta_correta = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('E', 'E')
        ]
    )
    nivel_dificuldade = models.CharField(
        max_length=1,
        choices=NIVEL_CHOICES,
        default='M'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_modificacao = models.DateTimeField(auto_now=True)

    # ✅ NOVO CAMPO: Para rastrear questões que são cópias de questões públicas
    questao_publica_original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='copias_personalizadas',
        help_text='Questão pública original da qual esta é uma cópia personalizada'
    )

    class Meta:
        verbose_name = 'Questão'
        verbose_name_plural = 'Questões'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['professor']),
            models.Index(fields=['disciplina']),
            models.Index(fields=['nivel_dificuldade']),
        ]


    def __str__(self):
        if self.professor:
            return f"Questão {self.id} - {self.disciplina} - {self.conteudo}"
        else:
            return f"Questão Pública {self.id} - {self.disciplina} - {self.conteudo}"

    def clean(self):
        if self.imagem and self.imagem.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError('O tamanho máximo da imagem é 5MB')

        # ✅ MÉTODO ATUALIZADO: Verifica se é questão pública (sem professor) e não é cópia
    @property
    def is_publica(self):
        """Retorna True se a questão não tem professor (é pública/do admin) e não é uma cópia personalizada"""
        return self.professor is None and self.questao_publica_original is None

    @property
    def is_copia_personalizada(self):
        """Retorna True se esta questão é uma cópia personalizada de uma questão pública"""
        return self.questao_publica_original is not None

class VersaoGabarito(models.Model):
    """Modelo simplificado apenas para armazenar histórico quando necessário"""
    simulado = models.ForeignKey('Simulado', on_delete=models.CASCADE, related_name='versoes_gabarito')
    versao_id = models.UUIDField(default=uuid.uuid4, unique=True, help_text='ID único da versão do gabarito')
    gabaritos_gerados = models.JSONField(help_text='Armazena as informações de embaralhamento das 5 versões')
    data_geracao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, help_text='Observações sobre esta versão do gabarito')

    # Campos para rastreamento básico
    usuario_geracao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Usuário que gerou esta versão'
    )
    total_questoes = models.IntegerField(default=0, help_text='Número total de questões nesta versão')

    class Meta:
        ordering = ['-data_geracao']
        verbose_name = 'Versão do Gabarito'
        verbose_name_plural = 'Versões dos Gabaritos'

    def __str__(self):
        return f"{self.simulado.titulo} - Versão {self.versao_id.hex[:8]}"

    def get_versao_curta(self):
        """Retorna uma versão curta do UUID para exibição"""
        return self.versao_id.hex[:8].upper()

    def get_resumo_gabaritos(self):
        """Retorna um resumo dos gabaritos para exibição"""
        if not self.gabaritos_gerados or not isinstance(self.gabaritos_gerados, list):
            return []

        resumo = []
        for i, gabarito_versao in enumerate(self.gabaritos_gerados, 1):
            if gabarito_versao and 'gabarito' in gabarito_versao and isinstance(gabarito_versao['gabarito'], dict):
                questoes_resumo = []
                for ordem in sorted(gabarito_versao['gabarito'].keys(), key=int):
                    item_gabarito = gabarito_versao['gabarito'][ordem]

                    if isinstance(item_gabarito, dict):
                        resposta = item_gabarito.get('tipo1') or item_gabarito.get('resposta') or 'N/A'
                    elif isinstance(item_gabarito, str):
                        resposta = item_gabarito
                    else:
                        resposta = str(item_gabarito) if item_gabarito is not None else 'N/A'

                    questoes_resumo.append(f"{ordem}:{resposta}")

                resumo.append({
                    'versao': i,
                    'gabarito_str': ' | '.join(questoes_resumo[:10]) + ('...' if len(questoes_resumo) > 10 else '')
                })
        return resumo

    def tem_resultados_vinculados(self):
        """Verifica se esta versão tem resultados vinculados"""
        return self.resultados.exists()


class Simulado(models.Model):
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulados'
    )

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    questoes = models.ManyToManyField(
        'Questao',
        through='QuestaoSimulado',
        related_name='simulados'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_modificacao = models.DateTimeField(auto_now=True)
    cabecalho = RichTextField(blank=True, null=True)
    instrucoes = RichTextField(blank=True, null=True)
    classes = models.ManyToManyField(Class, related_name='simulados', blank=True)

    versao_gabarito_oficial = models.ForeignKey(
        'VersaoGabarito',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='simulado_oficial',
        help_text='Versão do gabarito definida como oficial para correção'
    )

    # CAMPO SIMPLES PARA PONTUAÇÃO
    pontuacao_total = models.PositiveIntegerField(
        default=5,
        help_text='Quanto vale este simulado (número inteiro positivo)'
    )

    class Meta:
        verbose_name = 'Simulado'
        verbose_name_plural = 'Simulados'
        ordering = ['-data_criacao']

    def __str__(self):
        return self.titulo

    def clean(self):
        # Só verifica o número de questões se o simulado já foi salvo
        if self.pk:
            if self.questoes.count() > 45:
                raise ValidationError('O simulado não pode ter mais que 45 questões')

    def calcular_pontuacao(self, acertos, total_questoes):
        """
        Calcula a pontuação baseada no valor total do simulado
        """
        if total_questoes == 0:
            return 0.0

        # Calcula proporcionalmente baseado no valor total configurado
        pontos_por_questao = self.pontuacao_total / total_questoes
        return round(acertos * pontos_por_questao, 2)

    def gerar_novo_gabarito_sempre(self, usuario=None):
        """
        SEMPRE gera um novo gabarito com embaralhamento.
        Não verifica cache nem versões anteriores.
        """
        print(f"DEBUG - Gerando NOVO gabarito para simulado {self.pk} (sem cache)")

        # Importar aqui para evitar importação circular
        from .utils import gerar_gabaritos_embaralhados

        # SEMPRE gerar novo embaralhamento
        gabaritos_gerados = gerar_gabaritos_embaralhados(self)

        # Salvar no histórico (opcional, para auditoria)
        if gabaritos_gerados:
            versao_historico = VersaoGabarito.objects.create(
                simulado=self,
                gabaritos_gerados=gabaritos_gerados,
                usuario_geracao=usuario,
                total_questoes=self.questoes.count()
            )
            print(f"DEBUG - Versão histórica criada: {versao_historico.get_versao_curta()}")

        return gabaritos_gerados

    def limpar_todo_cache(self):
        """Remove completamente qualquer cache relacionado ao simulado"""
        from django.core.cache import cache

        print(f"DEBUG - Limpando TODO o cache do simulado {self.pk}")

        # Lista de possíveis chaves de cache para limpar
        cache_patterns = [
            f'simulado_zip_{self.pk}_*',
            f'pdf_versao_*_{self.pk}_*',
            f'html_versao_*_{self.pk}_*',
            f'simulado_{self.pk}_*',
        ]

        # Cache específico por versão (1 a 5)
        for versao in range(1, 6):
            cache_keys = [
                f'pdf_versao_{versao}_{self.pk}',
                f'html_versao_{versao}_{self.pk}',
                f'gabarito_versao_{versao}_{self.pk}',
            ]
            for key in cache_keys:
                cache.delete(key)

        # Cache geral
        cache_keys_gerais = [
            f'simulado_{self.pk}_questoes',
            f'simulado_{self.pk}_gabaritos',
            f'simulado_{self.pk}_metadata',
            f'simulado_{self.pk}_pdf_data',
        ]

        for key in cache_keys_gerais:
            cache.delete(key)

        print(f"DEBUG - Cache completamente limpo para simulado {self.pk}")

    def get_historico_gabaritos(self):
        """Retorna o histórico de gabaritos apenas para auditoria"""
        return self.versoes_gabarito.all().order_by('-data_geracao')

    def get_total_versoes_gabarito(self):
        """Retorna o número total de versões de gabarito no histórico"""
        return self.versoes_gabarito.count()


class QuestaoSimulado(models.Model):
    simulado = models.ForeignKey(Simulado, on_delete=models.CASCADE)
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField()

    class Meta:
        ordering = ['ordem']
        unique_together = [
            ['simulado', 'questao'],
            ['simulado', 'ordem']
        ]

    def save(self, *args, **kwargs):
        """Limpa cache quando questão é adicionada/reordenada"""
        super().save(*args, **kwargs)
        # Limpar cache sempre que houver mudança
        self.simulado.limpar_todo_cache()
        print(f"DEBUG - Cache limpo após salvar questão {self.questao.pk} no simulado {self.simulado.pk}")

    def delete(self, *args, **kwargs):
        """Limpa cache quando questão é removida"""
        simulado = self.simulado
        super().delete(*args, **kwargs)
        # Limpar cache sempre que houver remoção
        simulado.limpar_todo_cache()
        print(f"DEBUG - Cache limpo após remover questão do simulado {simulado.pk}")

    def clean(self):
        # Verificar se a questão já existe no simulado
        if QuestaoSimulado.objects.filter(
            simulado=self.simulado,
            questao=self.questao
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Esta questão já foi adicionada ao simulado.')

        # Verificar se a ordem já está em uso
        if QuestaoSimulado.objects.filter(
            simulado=self.simulado,
            ordem=self.ordem
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Esta ordem já está em uso neste simulado.')

    def __str__(self):
        return f"Questão {self.questao.id} no Simulado {self.simulado.id} (Ordem: {self.ordem})"


class Resultado(models.Model):
    """Modelo para armazenar os resultados de um simulado para um aluno"""
    aluno = models.ForeignKey('classes.Student', on_delete=models.CASCADE, related_name='questions_resultados')
    simulado = models.ForeignKey(Simulado, on_delete=models.CASCADE, related_name='questions_resultados')
    versao_gabarito = models.ForeignKey(
        VersaoGabarito,
        on_delete=models.CASCADE,
        related_name='resultados',
        help_text='Versão do gabarito usada na correção',
        null=True,  # Permitir null para compatibilidade
        blank=True
    )
    pontuacao = models.FloatField()
    total_questoes = models.IntegerField()
    acertos = models.IntegerField()
    data_correcao = models.DateTimeField(auto_now_add=True)
    versao = models.CharField(max_length=20, blank=True, null=True)
    tipo_prova = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        ordering = ['-data_correcao']
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'

    def __str__(self):
        return f"{self.aluno.name} - {self.simulado.titulo} - {self.pontuacao} pontos"

    def get_percentual_acerto(self):
        """Retorna o percentual de acerto"""
        if self.total_questoes > 0:
            return (self.acertos / self.total_questoes) * 100
        return 0.0


class DetalhesResposta(models.Model):
    """Modelo para armazenar os detalhes das respostas de um resultado"""
    resultado = models.ForeignKey(Resultado, on_delete=models.CASCADE, related_name='detalhes')
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='questions_detalhes_resposta')
    ordem = models.CharField(max_length=10)
    resposta_aluno = models.CharField(max_length=1)
    resposta_correta = models.CharField(max_length=1)
    acertou = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Detalhe de Resposta'
        verbose_name_plural = 'Detalhes de Respostas'

    def __str__(self):
        return f"Q{self.ordem}: {self.resposta_aluno} ({'✓' if self.acertou else '✗'})"