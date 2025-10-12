# classes/management/commands/sync_results.py
from django.core.management.base import BaseCommand
from api.models import Resultado, DetalhesResposta
from classes.models import Student, StudentPerformance, StudentAnswer
from questions.models import Simulado, QuestaoSimulado

class Command(BaseCommand):
    help = 'Sincroniza resultados do aplicativo com o dashboard do aluno'

    def handle(self, *args, **options):
        # Encontrar todos os resultados do aplicativo que ainda não estão no dashboard
        self.stdout.write("Iniciando sincronização de resultados...")
        
        resultados = Resultado.objects.all()
        count_created = 0
        count_updated = 0
        count_errors = 0
        
        for resultado in resultados:
            try:
                # Verificar se já existe um desempenho para este aluno e simulado
                performance, created = StudentPerformance.objects.get_or_create(
                    student=resultado.aluno,
                    simulado=resultado.simulado,
                    defaults={
                        'score': resultado.pontuacao,
                        'correct_answers': resultado.acertos,
                        'total_questions': resultado.total_questoes
                    }
                )
                
                if not created:
                    # Atualizar se já existir
                    performance.score = resultado.pontuacao
                    performance.correct_answers = resultado.acertos
                    performance.total_questions = resultado.total_questoes
                    performance.save()
                    count_updated += 1
                else:
                    count_created += 1
                
                # Sincronizar também as respostas individuais
                detalhes = DetalhesResposta.objects.filter(resultado=resultado)
                
                for detalhe in detalhes:
                    try:
                        # Encontrar a questão do simulado
                        questao_simulado = QuestaoSimulado.objects.filter(
                            simulado=resultado.simulado,
                            ordem=int(detalhe.ordem)
                        ).first()
                        
                        if questao_simulado:
                            # Criar ou atualizar resposta do aluno
                            StudentAnswer.objects.update_or_create(
                                student=resultado.aluno,
                                simulado=resultado.simulado,
                                question=questao_simulado,
                                defaults={
                                    'chosen_option': detalhe.resposta_aluno,
                                    'is_correct': detalhe.acertou
                                }
                            )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Erro ao sincronizar resposta: {str(e)}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao sincronizar resultado {resultado.id}: {str(e)}"))
                count_errors += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Sincronização concluída: {count_created} criados, {count_updated} atualizados, {count_errors} erros"
        ))