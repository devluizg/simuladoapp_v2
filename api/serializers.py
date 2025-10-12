from rest_framework import serializers
from classes.models import Class, Student
from questions.models import Questao, Simulado, QuestaoSimulado

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'student_id', 'classes']

class QuestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questao
        fields = ['id', 'disciplina', 'conteudo', 'enunciado', 'alternativa_a', 'alternativa_b',
                  'alternativa_c', 'alternativa_d', 'alternativa_e', 'resposta_correta',
                  'nivel_dificuldade']

class QuestaoSimuladoSerializer(serializers.ModelSerializer):
    questao = QuestaoSerializer()

    class Meta:
        model = QuestaoSimulado
        fields = ['ordem', 'questao']

class SimuladoSerializer(serializers.ModelSerializer):
    questoes = QuestaoSimuladoSerializer(source='questaosimulado_set', many=True, read_only=True)
    numero_questoes = serializers.SerializerMethodField()
    pontuacao_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Simulado
        fields = ['id', 'titulo', 'descricao', 'questoes', 'data_criacao', 'ultima_modificacao',
                  'cabecalho', 'instrucoes', 'classes', 'pontuacao_total', 'numero_questoes']

    def get_numero_questoes(self, obj):
        """Retorna o número de questões do simulado"""
        return obj.questoes.count()

class CartaoRespostaSerializer(serializers.Serializer):
    aluno_id = serializers.IntegerField()
    simulado_id = serializers.IntegerField(required=False)
    respostas = serializers.DictField(child=serializers.CharField())

class DetalhesRespostaSerializer(serializers.Serializer):
    """Serializer para os detalhes das respostas de uma questão"""
    ordem = serializers.CharField()
    questao_id = serializers.IntegerField()
    disciplina = serializers.CharField()
    resposta_aluno = serializers.CharField()
    resposta_correta = serializers.CharField()
    acertou = serializers.BooleanField()

class ResultadoSerializer(serializers.Serializer):
    """Serializer para os resultados de um simulado"""
    id = serializers.IntegerField(read_only=True)
    aluno = serializers.CharField(read_only=True)
    simulado = serializers.CharField(read_only=True)
    pontuacao = serializers.FloatField(read_only=True)
    acertos = serializers.IntegerField(read_only=True)
    total_questoes = serializers.IntegerField(read_only=True)
    data_correcao = serializers.DateTimeField(read_only=True)
    detalhes = DetalhesRespostaSerializer(many=True, read_only=True)

class DashboardDisciplinaSerializer(serializers.Serializer):
    """Serializer para o desempenho por disciplina no dashboard"""
    disciplina = serializers.CharField()
    total_questoes = serializers.IntegerField()
    acertos = serializers.IntegerField()
    taxa_acerto = serializers.FloatField()

class DashboardAlunoSerializer(serializers.Serializer):
    """Serializer para o dashboard completo de um aluno"""
    aluno = serializers.CharField()
    total_simulados = serializers.IntegerField()
    media_geral = serializers.FloatField()
    desempenho_disciplinas = DashboardDisciplinaSerializer(many=True)
    evolucao_timeline = serializers.ListField(child=serializers.DictField())