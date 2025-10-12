# creditos/management/commands/manage_credits.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from creditos.models import CreditoUsuario

User = get_user_model()

class Command(BaseCommand):
    help = 'Gerenciar créditos dos usuários'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username ou email do usuário')
        parser.add_argument('--add', type=int, help='Quantidade de créditos para adicionar')
        parser.add_argument('--set', type=int, help='Definir quantidade total de créditos')
        parser.add_argument('--list-all', action='store_true', help='Listar todos os usuários e seus créditos')
        parser.add_argument('--give-all', type=int, help='Dar créditos para todos os usuários')

    def handle(self, *args, **options):
        if options['list_all']:
            self.list_all_users()
        elif options['give_all']:
            self.give_credits_to_all(options['give_all'])
        elif options['user']:
            user = self.get_user(options['user'])
            if user:
                if options['add']:
                    self.add_credits(user, options['add'])
                elif options['set']:
                    self.set_credits(user, options['set'])
                else:
                    self.show_user_credits(user)
        else:
            self.stdout.write(self.style.ERROR('Use --help para ver as opções disponíveis'))

    def get_user(self, identifier):
        """Buscar usuário por username ou email"""
        try:
            if '@' in identifier:
                return User.objects.get(email=identifier)
            else:
                return User.objects.get(username=identifier)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuário "{identifier}" não encontrado'))
            return None

    def add_credits(self, user, amount):
        """Adicionar créditos ao usuário"""
        credito_usuario, created = CreditoUsuario.objects.get_or_create(
            user=user,
            defaults={'total_creditos': 0, 'usados_creditos': 0}
        )

        credito_usuario.adicionar_creditos(amount)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {amount} créditos adicionados para {user.username}! '
                f'Total atual: {credito_usuario.creditos_restantes}'
            )
        )

    def set_credits(self, user, amount):
        """Definir quantidade total de créditos"""
        credito_usuario, created = CreditoUsuario.objects.get_or_create(
            user=user,
            defaults={'total_creditos': amount, 'usados_creditos': 0}
        )

        if not created:
            credito_usuario.total_creditos = amount
            credito_usuario.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Créditos de {user.username} definidos para {amount}! '
                f'Disponíveis: {credito_usuario.creditos_restantes}'
            )
        )

    def show_user_credits(self, user):
        """Mostrar créditos do usuário"""
        try:
            credito_usuario = CreditoUsuario.objects.get(user=user)
            self.stdout.write(
                f'👤 {user.username} ({user.email})\n'
                f'💰 Total: {credito_usuario.total_creditos}\n'
                f'💳 Usados: {credito_usuario.usados_creditos}\n'
                f'✅ Disponíveis: {credito_usuario.creditos_restantes}'
            )
        except CreditoUsuario.DoesNotExist:
            self.stdout.write(f'❌ {user.username} não tem créditos registrados')

    def list_all_users(self):
        """Listar todos os usuários e seus créditos"""
        creditos = CreditoUsuario.objects.select_related('user').all()

        if not creditos:
            self.stdout.write('❌ Nenhum usuário com créditos encontrado')
            return

        self.stdout.write('📋 TODOS OS USUÁRIOS COM CRÉDITOS:')
        self.stdout.write('-' * 50)

        for credito in creditos:
            status = '🟢' if credito.creditos_restantes > 10 else '🟡' if credito.creditos_restantes > 0 else '🔴'
            self.stdout.write(
                f'{status} {credito.user.username:<20} '
                f'({credito.user.email:<30}) '
                f'- {credito.creditos_restantes:>3} créditos'
            )

    def give_credits_to_all(self, amount):
        """Dar créditos para todos os usuários"""
        users = User.objects.all()
        updated = 0

        for user in users:
            credito_usuario, created = CreditoUsuario.objects.get_or_create(
                user=user,
                defaults={'total_creditos': 0, 'usados_creditos': 0}
            )
            credito_usuario.adicionar_creditos(amount)
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 {amount} créditos adicionados para {updated} usuários!'
            )
        )