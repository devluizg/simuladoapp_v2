# payments/services.py
import stripe
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone  # <-- IMPORTAÇÃO CORRIGIDA
from decimal import Decimal
from .models import Plan, Subscription, Payment, StripeWebhookEvent

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Serviço para integração com Stripe"""
    
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
    
    # ========== PRODUTOS E PREÇOS ==========
    
    def create_product(self, plan):
        """Cria um produto no Stripe"""
        try:
            product = stripe.Product.create(
                name=plan.name,
                description=plan.description,
                metadata={
                    'plan_id': plan.id,
                    'plan_type': plan.plan_type,
                }
            )
            
            plan.stripe_product_id = product.id
            plan.save()
            
            return product
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar produto: {str(e)}")
    
    def create_price(self, plan):
        """Cria um preço no Stripe"""
        if not plan.stripe_product_id:
            self.create_product(plan)
        
        try:
            # Converte período para o formato do Stripe
            interval_mapping = {
                'monthly': 'month',
                'semester': 'month',
                'annual': 'year',
            }

            interval = interval_mapping.get(plan.billing_period, 'month')
            interval_count = 6 if plan.billing_period == 'semester' else 1
            
            # Converte preço para centavos (Stripe usa centavos)
            unit_amount = int(plan.price * 100)
            
            price = stripe.Price.create(
                product=plan.stripe_product_id,
                unit_amount=unit_amount,
                currency='brl',
                recurring={
                    'interval': interval,
                    'interval_count': interval_count,
                },
                metadata={
                    'plan_id': plan.id,
                }
            )
            
            plan.stripe_price_id = price.id
            plan.save()
            
            return price
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar preço: {str(e)}")
    
    def sync_plan_to_stripe(self, plan):
        """Sincroniza um plano completo com o Stripe"""
        if not plan.stripe_product_id:
            self.create_product(plan)
        
        if not plan.stripe_price_id:
            self.create_price(plan)
        
        return plan
    
    # ========== CLIENTES ==========
    
    def create_customer(self, user, email=None):
        """Cria um customer no Stripe"""
        try:
            customer = stripe.Customer.create(
                email=email or user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    'user_id': user.id,
                    'username': user.username,
                }
            )
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar customer: {str(e)}")
    
    def get_or_create_customer(self, user):
        """Busca ou cria um customer no Stripe"""
        # Verifica se o usuário já tem uma assinatura com customer_id
        existing_subscription = Subscription.objects.filter(user=user).first()
        
        if existing_subscription and existing_subscription.stripe_customer_id:
            try:
                # Verifica se o customer ainda existe no Stripe
                customer = stripe.Customer.retrieve(existing_subscription.stripe_customer_id)
                return customer
            except stripe.error.StripeError:
                pass
        
        # Se não encontrou, cria um novo
        return self.create_customer(user)
    
    # ========== ASSINATURAS ==========
    
    def create_subscription(self, user, plan, payment_method_id=None):
        """Cria uma assinatura no Stripe"""
        try:
            # Garante que o plano está sincronizado
            if not plan.stripe_price_id:
                self.sync_plan_to_stripe(plan)
            
            # Busca ou cria customer
            customer = self.get_or_create_customer(user)
            
            subscription_data = {
                'customer': customer.id,
                'items': [{'price': plan.stripe_price_id}],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {
                    'save_default_payment_method': 'on_subscription'
                },
                'expand': ['latest_invoice.payment_intent'],
                'metadata': {
                    'user_id': user.id,
                    'plan_id': plan.id,
                }
            }
            
            # Se forneceu método de pagamento, adiciona
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            # Cria registro local
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer.id,
                status=stripe_subscription.status,
                # CORRIGIDO: Usa dt_timezone.utc
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start, tz=dt_timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end, tz=dt_timezone.utc
                ),
            )
            
            return {
                'subscription': subscription,
                'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret if stripe_subscription.latest_invoice else None,
                'stripe_subscription': stripe_subscription
            }
            
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar assinatura: {str(e)}")
    
    def cancel_subscription(self, stripe_subscription_id, immediately=False):
        """Cancela uma assinatura"""
        try:
            if immediately:
                stripe_subscription = stripe.Subscription.delete(stripe_subscription_id)
            else:
                stripe_subscription = stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Atualiza registro local
            subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
            subscription.status = stripe_subscription.status
            
            if immediately:
                subscription.canceled_at = timezone.now()
                subscription.ended_at = timezone.now()
            else:
                subscription.canceled_at = timezone.now()
            
            subscription.save()
            
            return subscription
            
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao cancelar assinatura: {str(e)}")
        except Subscription.DoesNotExist:
            raise Exception("Assinatura não encontrada no banco de dados")
    
    def reactivate_subscription(self, stripe_subscription_id):
        """Reativa uma assinatura cancelada"""
        try:
            stripe_subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            subscription.cancel_at_period_end = False
            subscription.canceled_at = None
            subscription.save()
            
            return subscription
            
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao reativar assinatura: {str(e)}")
    
    def update_subscription_plan(self, stripe_subscription_id, new_plan):
        """Atualiza o plano de uma assinatura"""
        try:
            if not new_plan.stripe_price_id:
                self.sync_plan_to_stripe(new_plan)
            
            # Busca a assinatura no Stripe
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Atualiza o item da assinatura
            stripe.Subscription.modify(
                stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0].id,
                    'price': new_plan.stripe_price_id,
                }],
                proration_behavior='always_invoice',
            )
            
            # Atualiza registro local
            subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            subscription.plan = new_plan
            subscription.save()
            
            return subscription
            
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao atualizar plano: {str(e)}")
    
    # ========== CHECKOUT SESSION ==========
    
    def create_checkout_session(self, user, plan, success_url, cancel_url):
        """Cria uma sessão de checkout do Stripe"""
        try:
            if not plan.stripe_price_id:
                self.sync_plan_to_stripe(plan)
            
            customer = self.get_or_create_customer(user)
            
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                }
            )
            
            return session
            
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar checkout session: {str(e)}")
    
    # ========== PORTAL DO CLIENTE ==========
    
    def create_customer_portal_session(self, stripe_customer_id, return_url):
        """Cria sessão do portal do cliente"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=return_url,
            )
            return session
        except stripe.error.StripeError as e:
            raise Exception(f"Erro ao criar portal session: {str(e)}")
    
    # ========== WEBHOOKS ==========
    
    def verify_webhook_signature(self, payload, sig_header):
        """Verifica a assinatura do webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise Exception("Payload inválido")
        except stripe.error.SignatureVerificationError:
            raise Exception("Assinatura inválida")
    
    def handle_webhook_event(self, event):
        """Processa eventos do webhook"""
        event_type = event['type']
        data = event['data']['object']
        
        # Salva o evento
        webhook_event, created = StripeWebhookEvent.objects.get_or_create(
            stripe_event_id=event['id'],
            defaults={
                'event_type': event_type,
                'data': event,
                'processed': False
            }
        )
        
        if not created and webhook_event.processed:
            return {'status': 'already_processed'}
        
        try:
            # Processa baseado no tipo de evento
            if event_type == 'checkout.session.completed':
                self._handle_checkout_completed(data)
            
            elif event_type == 'customer.subscription.created':
                self._handle_subscription_created(data)
            
            elif event_type == 'customer.subscription.updated':
                self._handle_subscription_updated(data)
            
            elif event_type == 'customer.subscription.deleted':
                self._handle_subscription_deleted(data)
            
            elif event_type == 'invoice.paid':
                self._handle_invoice_paid(data)
            
            elif event_type == 'invoice.payment_failed':
                self._handle_invoice_payment_failed(data)
            
            # Marca como processado
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            return {'status': 'success', 'event_type': event_type}
            
        except Exception as e:
            webhook_event.error_message = str(e)
            webhook_event.save()
            raise

    def _handle_checkout_completed(self, session):
        """Processa conclusão do checkout"""
        from django.contrib.auth import get_user_model

        subscription_id = session.get('subscription')
        customer_id = session.get('customer')
        user_id = session['metadata'].get('user_id')
        plan_id = session['metadata'].get('plan_id')

        if all([subscription_id, user_id, plan_id]):
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                plan = Plan.objects.get(id=plan_id)
            except (User.DoesNotExist, Plan.DoesNotExist) as e:
                print(f"Webhook Error: User or Plan not found. Details: {str(e)}")
                return

            stripe_subscription = stripe.Subscription.retrieve(subscription_id)

            Subscription.objects.update_or_create(
                stripe_subscription_id=subscription_id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'stripe_customer_id': customer_id,
                    'status': stripe_subscription.status,
                    # CORRIGIDO: Usa dt_timezone.utc
                    'current_period_start': datetime.fromtimestamp(
                        stripe_subscription.current_period_start, tz=dt_timezone.utc
                    ),
                    'current_period_end': datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=dt_timezone.utc
                    ),
                }
            )
    
    def _handle_subscription_created(self, subscription_data):
        """Processa criação de assinatura"""
        subscription_id = subscription_data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = subscription_data['status']
            # CORRIGIDO: Usa dt_timezone.utc
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=dt_timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=dt_timezone.utc
            )
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    def _handle_subscription_updated(self, subscription_data):
        """Processa atualização de assinatura"""
        subscription_id = subscription_data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = subscription_data['status']
            # CORRIGIDO: Usa dt_timezone.utc
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=dt_timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=dt_timezone.utc
            )
            subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
            
            if subscription_data.get('canceled_at'):
                # CORRIGIDO: Usa dt_timezone.utc
                subscription.canceled_at = datetime.fromtimestamp(
                    subscription_data['canceled_at'], tz=dt_timezone.utc
                )
            
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    def _handle_subscription_deleted(self, subscription_data):
        """Processa cancelamento de assinatura"""
        subscription_id = subscription_data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = 'canceled'
            subscription.ended_at = timezone.now()
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    def _handle_invoice_paid(self, invoice_data):
        """Processa pagamento de invoice"""
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                
                Payment.objects.create(
                    subscription=subscription,
                    user=subscription.user,
                    stripe_invoice_id=invoice_data['id'],
                    stripe_charge_id=invoice_data.get('charge'),
                    stripe_payment_intent_id=invoice_data.get('payment_intent'),
                    amount=Decimal(invoice_data['amount_paid']) / 100,
                    currency=invoice_data['currency'].upper(),
                    status='succeeded',
                    description=f"Pagamento - {subscription.plan.name}",
                    # CORRIGIDO: Usa dt_timezone.utc
                    paid_at=datetime.fromtimestamp(
                        invoice_data['status_transitions']['paid_at'], tz=dt_timezone.utc
                    )
                )
                
                subscription.status = 'active'
                subscription.save()
                
            except Subscription.DoesNotExist:
                pass
    
    def _handle_invoice_payment_failed(self, invoice_data):
        """Processa falha no pagamento"""
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = 'past_due'
                subscription.save()
                
                Payment.objects.create(
                    subscription=subscription,
                    user=subscription.user,
                    stripe_invoice_id=invoice_data['id'],
                    stripe_payment_intent_id=invoice_data.get('payment_intent'),
                    amount=Decimal(invoice_data['amount_due']) / 100,
                    currency=invoice_data['currency'].upper(),
                    status='failed',
                    description=f"Falha no pagamento - {subscription.plan.name}",
                )
            except Subscription.DoesNotExist:
                pass
