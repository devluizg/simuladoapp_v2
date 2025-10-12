from django.db import models
from django.utils import timezone
from classes.models import Student
from questions.models import Simulado, Questao

class Resultado(models.Model):
    """Modelo para armazenar os resultados de um simulado para um aluno"""
    aluno = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='api_resultados')
    simulado = models.ForeignKey(Simulado, on_delete=models.CASCADE, related_name='api_resultados')
    pontuacao = models.FloatField()
    total_questoes = models.IntegerField()
    acertos = models.IntegerField()
    data_correcao = models.DateTimeField(auto_now_add=True)
    # Adicionando campos para versão e tipo da prova
    versao = models.CharField(max_length=20, blank=True, null=True)
    tipo_prova = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        unique_together = ('aluno', 'simulado', 'data_correcao')
        ordering = ['-data_correcao']
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        
    def __str__(self):
        return f"{self.aluno.name} - {self.simulado.titulo} - {self.pontuacao}%"
        
    def get_percentual_acerto(self):
        """Retorna o percentual de acerto"""
        if self.total_questoes > 0:
            return (self.acertos / self.total_questoes) * 100
        return 0.0
        
class DetalhesResposta(models.Model):
    """Modelo para armazenar os detalhes das respostas de um resultado"""
    resultado = models.ForeignKey(Resultado, on_delete=models.CASCADE, related_name='detalhes')
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE)
    ordem = models.CharField(max_length=10)  # Número da questão no simulado
    resposta_aluno = models.CharField(max_length=1)  # A, B, C, D ou E
    resposta_correta = models.CharField(max_length=1)  # A, B, C, D ou E
    acertou = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['ordem']
        verbose_name = 'Detalhe de Resposta'
        verbose_name_plural = 'Detalhes de Respostas'
        
    def __str__(self):
        return f"Q{self.ordem}: {self.resposta_aluno} ({'✓' if self.acertou else '✗'})"