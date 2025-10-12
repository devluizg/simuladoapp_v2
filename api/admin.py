from django.contrib import admin
from .models import Resultado, DetalhesResposta

class DetalhesRespostaInline(admin.TabularInline):
    model = DetalhesResposta
    extra = 0
    readonly_fields = ('ordem', 'questao', 'resposta_aluno', 'resposta_correta', 'acertou')

@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'simulado', 'pontuacao', 'acertos', 'total_questoes', 'data_correcao')
    list_filter = ('simulado', 'data_correcao')
    search_fields = ('aluno__name', 'simulado__titulo')
    readonly_fields = ('pontuacao', 'acertos', 'total_questoes')
    inlines = [DetalhesRespostaInline]

@admin.register(DetalhesResposta)
class DetalhesRespostaAdmin(admin.ModelAdmin):
    list_display = ('resultado', 'ordem', 'resposta_aluno', 'resposta_correta', 'acertou')
    list_filter = ('acertou', 'resultado__simulado')
    search_fields = ('resultado__aluno__name', 'ordem')