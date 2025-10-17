from rest_framework import serializers
from classes.models import Class, Student
from questions.models import Questao, Simulado, QuestaoSimulado
from api.models import Resultado, DetalhesResposta

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    data_nascimento = serializers.DateField(format="%d/%m/%Y", required=False)
    classes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'student_id', 'data_nascimento', 'classes']

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

# ✅ CORREÇÃO: DetalhesRespostaSerializer usando ModelSerializer
class DetalhesRespostaSerializer(serializers.ModelSerializer):
    """Serializer para os detalhes das respostas de uma questão"""
    disciplina = serializers.CharField(source='questao.disciplina', read_only=True)
    questao_id = serializers.IntegerField(source='questao.id', read_only=True)

    class Meta:
        model = DetalhesResposta
        fields = ['ordem', 'questao_id', 'disciplina', 'resposta_aluno', 'resposta_correta', 'acertou']

# ✅ CORREÇÃO: ResultadoSerializer usando ModelSerializer
class ResultadoSerializer(serializers.ModelSerializer):
    """Serializer para os resultados de um simulado"""
    aluno = serializers.CharField(source='aluno.name', read_only=True)
    simulado = serializers.CharField(source='simulado.titulo', read_only=True)
    simulado_id = serializers.IntegerField(source='simulado.id', read_only=True)
    detalhes = DetalhesRespostaSerializer(source='detalhesresposta_set', many=True, read_only=True)

    class Meta:
        model = Resultado
        fields = [
            'id',
            'aluno',
            'simulado',
            'simulado_id',
            'pontuacao',
            'acertos',
            'total_questoes',
            'data_correcao',
            'detalhes'
        ]

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