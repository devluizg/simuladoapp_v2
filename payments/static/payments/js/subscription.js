/**
 * SimuladoApp - Subscription Management JavaScript
 * Gerencia ações de assinatura (cancelar, reativar, upgrade)
 */

(function() {
    'use strict';

    // ========================================
    // CONFIGURAÇÃO
    // ========================================

    const SubscriptionManager = {
        csrfToken: null,
        
        /**
         * Inicializa o gerenciador de assinaturas
         */
        init: function() {
            console.log('Inicializando Subscription Manager...');
            
            this.csrfToken = this.getCSRFToken();
            this.setupEventListeners();
            this.checkSubscriptionStatus();
            
            console.log('Subscription Manager inicializado');
        },
        
        /**
         * Configura event listeners
         */
        setupEventListeners: function() {
            // Botões de cancelamento
            const cancelButtons = document.querySelectorAll('[data-action="cancel-subscription"]');
            cancelButtons.forEach(btn => {
                btn.addEventListener('click', () => this.showCancelModal());
            });
            
            // Botões de reativação
            const reactivateButtons = document.querySelectorAll('[data-action="reactivate-subscription"]');
            reactivateButtons.forEach(btn => {
                btn.addEventListener('click', () => this.reactivateSubscription());
            });
            
            // Botões de upgrade
            const upgradeButtons = document.querySelectorAll('[data-action="upgrade-subscription"]');
            upgradeButtons.forEach(btn => {
                const planSlug = btn.dataset.planSlug;
                btn.addEventListener('click', () => this.showUpgradeModal(planSlug));
            });
        },
        
        // ========================================
        // CANCELAMENTO
        // ========================================
        
        /**
         * Exibe modal de cancelamento
         */
        showCancelModal: function() {
            const modal = document.getElementById('cancelModal');
            if (modal && typeof bootstrap !== 'undefined') {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        },
        
        /**
         * Cancela a assinatura
         */
        cancelSubscription: async function(immediately = false, reason = '') {
            if (!confirm('Tem certeza que deseja cancelar sua assinatura?')) {
                return;
            }
            
            this.showLoading(true);
            
            try {
                const response = await fetch('/payments/subscription/cancel/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({
                        immediately: immediately,
                        reason: reason
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showSuccess('Assinatura cancelada com sucesso');
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Erro ao cancelar assinatura');
                }
            } catch (error) {
                console.error('Erro ao cancelar:', error);
                this.showError(error.message);
            } finally {
                this.showLoading(false);
            }
        },
        
        // ========================================
        // REATIVAÇÃO
        // ========================================
        
        /**
         * Reativa a assinatura
         */
        reactivateSubscription: async function() {
            if (!confirm('Deseja reativar sua assinatura?')) {
                return;
            }
            
            this.showLoading(true);
            
            try {
                const response = await fetch('/payments/subscription/reactivate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showSuccess('Assinatura reativada com sucesso!');
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Erro ao reativar assinatura');
                }
            } catch (error) {
                console.error('Erro ao reativar:', error);
                this.showError(error.message);
            } finally {
                this.showLoading(false);
            }
        },
        
        // ========================================
        // UPGRADE/DOWNGRADE
        // ========================================
        
        /**
         * Exibe modal de upgrade
         */
        showUpgradeModal: function(planSlug) {
            const modal = document.getElementById('upgradeModal');
            if (modal && typeof bootstrap !== 'undefined') {
                // Atualiza informações do modal
                document.getElementById('upgradePlanName').textContent = planSlug;
                
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
                
                // Armazena o plan slug para uso posterior
                modal.dataset.planSlug = planSlug;
            }
        },
        
        /**
         * Faz upgrade do plano
         */
        upgradeSubscription: async function(planSlug) {
            this.showLoading(true);
            
            try {
                                const response = await fetch('/payments/subscription/upgrade/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({
                        plan_slug: planSlug
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showSuccess('Plano atualizado com sucesso!');
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Erro ao fazer upgrade');
                }
            } catch (error) {
                console.error('Erro ao fazer upgrade:', error);
                this.showError(error.message);
            } finally {
                this.showLoading(false);
            }
        },
        
        // ========================================
        // STATUS DA ASSINATURA
        // ========================================
        
        /**
         * Verifica status da assinatura
         */
        checkSubscriptionStatus: async function() {
            try {
                const response = await fetch('/payments/api/check-subscription/');
                const data = await response.json();
                
                // Atualiza UI baseado no status
                this.updateSubscriptionUI(data);
                
                // Verifica expiração próxima
                if (data.has_subscription && data.is_active) {
                    this.checkExpirationWarning(data);
                }
                
            } catch (error) {
                console.error('Erro ao verificar status:', error);
            }
        },
        
        /**
         * Atualiza UI baseado no status
         */
        updateSubscriptionUI: function(data) {
            const statusElements = document.querySelectorAll('[data-subscription-status]');
            
            statusElements.forEach(el => {
                if (data.has_subscription) {
                    el.textContent = data.is_active ? 'Ativa' : 'Inativa';
                    el.className = data.is_active ? 'badge bg-success' : 'badge bg-danger';
                } else {
                    el.textContent = 'Sem assinatura';
                    el.className = 'badge bg-secondary';
                }
            });
        },
        
        /**
         * Verifica e exibe aviso de expiração próxima
         */
        checkExpirationWarning: function(data) {
            if (!data.current_period_end) return;
            
            const endDate = new Date(data.current_period_end);
            const now = new Date();
            const daysUntilExpiration = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
            
            if (daysUntilExpiration <= 7 && daysUntilExpiration > 0) {
                this.showExpirationWarning(daysUntilExpiration);
            }
        },
        
        /**
         * Exibe aviso de expiração
         */
        showExpirationWarning: function(days) {
            const warningHTML = `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Atenção!</strong> Sua assinatura expira em ${days} dia${days > 1 ? 's' : ''}.
                    <a href="/payments/subscription/" class="alert-link">Renovar agora</a>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            const container = document.getElementById('subscription-warnings');
            if (container) {
                container.innerHTML = warningHTML;
            }
        },
        
        // ========================================
        // ADICIONAR TURMAS EXTRAS
        // ========================================
        
        /**
         * Adiciona turmas extras
         */
        addExtraClasses: async function(quantity) {
            if (!quantity || quantity < 1) {
                this.showError('Quantidade inválida');
                return;
            }
            
            this.showLoading(true);
            
            try {
                const response = await fetch('/payments/subscription/add-extra-classes/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({
                        quantity: quantity
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showSuccess(`${quantity} turma(s) extra adicionada(s)!`);
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Erro ao adicionar turmas');
                }
            } catch (error) {
                console.error('Erro ao adicionar turmas:', error);
                this.showError(error.message);
            } finally {
                this.showLoading(false);
            }
        },
        
        // ========================================
        // UTILIDADES
        // ========================================
        
        /**
         * Obtém CSRF Token
         */
        getCSRFToken: function() {
            const input = document.querySelector('[name=csrfmiddlewaretoken]');
            if (input) {
                return input.value;
            }
            
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='));
            
            return cookieValue ? cookieValue.split('=')[1] : '';
        },
        
        /**
         * Exibe loading
         */
        showLoading: function(show) {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = show ? 'flex' : 'none';
            }
            
            // Desabilita botões durante loading
            const buttons = document.querySelectorAll('button[data-action]');
            buttons.forEach(btn => {
                btn.disabled = show;
            });
        },
        
        /**
         * Exibe mensagem de sucesso
         */
        showSuccess: function(message) {
            this.showToast(message, 'success');
        },
        
        /**
         * Exibe mensagem de erro
         */
        showError: function(message) {
            this.showToast(message, 'danger');
        },
        
                /**
         * Exibe toast
         */
        showToast: function(message, type) {
            // Tenta usar Bootstrap Toast se disponível
            if (typeof bootstrap !== 'undefined' && document.getElementById('toast-container')) {
                const toastHTML = `
                    <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                        <div class="d-flex">
                            <div class="toast-body">
                                ${message}
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                        </div>
                    </div>
                `;
                
                const container = document.getElementById('toast-container');
                container.insertAdjacentHTML('beforeend', toastHTML);
                
                const toastElement = container.lastElementChild;
                const toast = new bootstrap.Toast(toastElement);
                toast.show();
                
                // Remove após esconder
                toastElement.addEventListener('hidden.bs.toast', () => {
                    toastElement.remove();
                });
            } else {
                // Fallback para alert
                alert(message);
            }
        },
        
        /**
         * Formata data
         */
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        },
        
        /**
         * Formata moeda
         */
        formatCurrency: function(value) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        }
    };
    
    // ========================================
    // FUNÇÕES GLOBAIS
    // ========================================
    
    /**
     * Confirma cancelamento do modal
     */
    window.confirmCancel = function() {
        const immediately = document.getElementById('cancelImmediately');
        const reason = document.getElementById('cancelReason');
        
        const isImmediate = immediately ? immediately.checked : false;
        const cancelReason = reason ? reason.value : '';
        
        SubscriptionManager.cancelSubscription(isImmediate, cancelReason);
        
        // Fecha o modal
        const modal = document.getElementById('cancelModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    };
    
    /**
     * Reativa assinatura
     */
    window.reactivateSubscription = function() {
        SubscriptionManager.reactivateSubscription();
    };
    
    /**
     * Confirma upgrade do modal
     */
    window.confirmUpgrade = function() {
        const modal = document.getElementById('upgradeModal');
        if (modal && modal.dataset.planSlug) {
            SubscriptionManager.upgradeSubscription(modal.dataset.planSlug);
            
            // Fecha o modal
            if (typeof bootstrap !== 'undefined') {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        }
    };
    
    /**
     * Upgrade para plano específico
     */
    window.upgradeToPlan = function(planSlug) {
        SubscriptionManager.showUpgradeModal(planSlug);
    };
    
    /**
     * Adiciona turmas extras
     */
    window.addExtraClasses = function() {
        const input = document.getElementById('extra-classes-quantity');
        if (input) {
            const quantity = parseInt(input.value);
            SubscriptionManager.addExtraClasses(quantity);
        }
    };
    
    /**
     * Calcula custo de turmas extras
     */
    window.calculateExtraClassesCost = function(quantity, pricePerClass) {
        const total = quantity * pricePerClass;
        const formattedTotal = SubscriptionManager.formatCurrency(total);
        
        const resultElement = document.getElementById('extra-classes-total');
        if (resultElement) {
            resultElement.textContent = formattedTotal;
        }
        
        return total;
    };
    
    /**
     * Abre portal do cliente
     */
    window.openCustomerPortal = function() {
        window.location.href = '/payments/portal/';
    };
    
    /**
     * Baixa fatura
     */
    window.downloadInvoice = function(invoiceId) {
        window.open(`https://dashboard.stripe.com/invoices/${invoiceId}`, '_blank');
    };
    
    /**
     * Compara planos
     */
    window.comparePlans = function(currentPlanSlug, newPlanSlug) {
        // Redireciona para página de comparação
        window.location.href = `/payments/plans/compare/?current=${currentPlanSlug}&new=${newPlanSlug}`;
    };
    
    // ========================================
    // AUTO-REFRESH DE STATUS
    // ========================================
    
    /**
     * Auto-refresh do status da assinatura
     */
    function autoRefreshStatus() {
        const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutos
        
        setInterval(() => {
            SubscriptionManager.checkSubscriptionStatus();
        }, REFRESH_INTERVAL);
    }
    
    // ========================================
    // NOTIFICAÇÕES WEB PUSH (OPCIONAL)
    // ========================================
    
    /**
     * Solicita permissão para notificações
     */
    function requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    /**
     * Envia notificação local
     */
    function sendLocalNotification(title, options) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, options);
        }
    }
    
    // ========================================
    // ANALYTICS E TRACKING
    // ========================================
    
    /**
     * Rastreia cancelamento
     */
    function trackCancellation(reason) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'subscription_cancelled', {
                reason: reason
            });
        }
        console.log('Subscription cancelled:', reason);
    }
    
    /**
     * Rastreia upgrade
     */
    function trackUpgrade(fromPlan, toPlan) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'subscription_upgraded', {
                from_plan: fromPlan,
                to_plan: toPlan
            });
        }
        console.log('Subscription upgraded:', fromPlan, '->', toPlan);
    }
    
    // ========================================
    // INICIALIZAÇÃO
    // ========================================
    
    /**
     * Inicializa quando DOM estiver pronto
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            SubscriptionManager.init();
            autoRefreshStatus();
        });
    } else {
        SubscriptionManager.init();
        autoRefreshStatus();
    }
    
    // Expõe o SubscriptionManager globalmente para debug
    window.SubscriptionManager = SubscriptionManager;
    
})();

/**
 * Helper para criar toast container se não existir
 */
(function() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
})();

/**
 * Helper para criar loading overlay se não existir
 */
(function() {
    if (!document.getElementById('loading-overlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9998;
            justify-content: center;
            align-items: center;
        `;
        overlay.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p style="margin-top: 15px; color: #333;">Processando...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }
})();