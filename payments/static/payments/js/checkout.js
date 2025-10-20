/**
 * SimuladoApp - Checkout JavaScript
 * Gerencia o processo de checkout com Stripe
 */

(function() {
    'use strict';

    // ========================================
    // CONFIGURAÇÃO E INICIALIZAÇÃO
    // ========================================

    const CheckoutManager = {
        stripe: null,
        elements: null,
        cardElement: null,
        form: null,
        submitButton: null,
        
        /**
         * Inicializa o checkout
         */
        init: function(stripePublicKey) {
            console.log('Inicializando Checkout...');
            
            // Inicializa o Stripe
            this.stripe = Stripe(stripePublicKey);
            this.elements = this.stripe.elements();
            
            // Configura os elementos
            this.setupCardElement();
            this.setupForm();
            this.setupEventListeners();
            
            console.log('Checkout inicializado com sucesso');
        },
        
        /**
         * Configura o elemento de cartão do Stripe
         */
        setupCardElement: function() {
            const style = {
                base: {
                    color: '#32325d',
                    fontFamily: '"Inter", "Poppins", sans-serif',
                    fontSmoothing: 'antialiased',
                    fontSize: '16px',
                    '::placeholder': {
                        color: '#aab7c4'
                    }
                },
                invalid: {
                    color: '#fa755a',
                    iconColor: '#fa755a'
                }
            };
            
            this.cardElement = this.elements.create('card', { style: style });
            this.cardElement.mount('#card-element');
            
            // Listener para erros do cartão
            this.cardElement.on('change', (event) => {
                this.displayCardError(event.error ? event.error.message : '');
            });
        },
        
        /**
         * Configura o formulário
         */
        setupForm: function() {
            this.form = document.getElementById('checkout-form');
            this.submitButton = document.getElementById('submit-button');
            
            if (!this.form || !this.submitButton) {
                console.error('Formulário ou botão de submit não encontrado');
                return;
            }
        },
        
        /**
         * Configura os event listeners
         */
        setupEventListeners: function() {
            if (this.form) {
                this.form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleSubmit();
                });
            }
            
            // Previne saída acidental durante processamento
            window.addEventListener('beforeunload', (e) => {
                if (this.submitButton && this.submitButton.disabled) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            });
        },
        
        // ========================================
        // PROCESSAMENTO DO CHECKOUT
        // ========================================
        
        /**
         * Processa o envio do formulário
         */
        handleSubmit: async function() {
            console.log('Processando checkout...');
            
            // Validações
            if (!this.validateForm()) {
                return;
            }
            
            // Desabilita o botão e mostra loading
            this.setLoading(true);
            
            try {
                // Pega o plan slug
                const planSlug = this.form.dataset.planSlug || 
                                window.location.pathname.split('/').filter(x => x).pop();
                
                // Cria a sessão de checkout
                const session = await this.createCheckoutSession(planSlug);
                
                if (session.error) {
                    throw new Error(session.error);
                }
                
                // Redireciona para o checkout do Stripe
                const result = await this.stripe.redirectToCheckout({
                    sessionId: session.sessionId
                });
                
                if (result.error) {
                    throw new Error(result.error.message);
                }
                
                        } catch (error) {
                console.error('Erro no checkout:', error);
                this.showError(error.message || 'Erro ao processar pagamento');
                this.setLoading(false);
            }
        },
        
        /**
         * Cria sessão de checkout no backend
         */
        createCheckoutSession: async function(planSlug) {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch('/payments/checkout/session/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    plan_slug: planSlug
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erro ao criar sessão de checkout');
            }
            
            return await response.json();
        },
        
        // ========================================
        // VALIDAÇÕES
        // ========================================
        
        /**
         * Valida o formulário antes do envio
         */
        validateForm: function() {
            // Valida checkbox de termos
            const termsCheckbox = document.getElementById('terms-checkbox');
            if (termsCheckbox && !termsCheckbox.checked) {
                this.showError('Você precisa aceitar os termos de serviço');
                return false;
            }
            
            return true;
        },
        
        // ========================================
        // UI E FEEDBACK
        // ========================================
        
        /**
         * Define estado de loading
         */
        setLoading: function(isLoading) {
            if (this.submitButton) {
                this.submitButton.disabled = isLoading;
                
                if (isLoading) {
                    this.submitButton.classList.add('loading');
                    this.showLoadingOverlay(true);
                } else {
                    this.submitButton.classList.remove('loading');
                    this.showLoadingOverlay(false);
                }
            }
        },
        
        /**
         * Mostra/esconde overlay de loading
         */
        showLoadingOverlay: function(show) {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                if (show) {
                    overlay.classList.add('active');
                } else {
                    overlay.classList.remove('active');
                }
            }
        },
        
        /**
         * Exibe erro do cartão
         */
        displayCardError: function(message) {
            const errorElement = document.getElementById('card-errors');
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.style.display = message ? 'block' : 'none';
            }
        },
        
        /**
         * Exibe erro genérico
         */
        showError: function(message) {
            // Tenta usar alertas do Bootstrap se disponível
            if (typeof bootstrap !== 'undefined') {
                this.showBootstrapAlert(message, 'danger');
            } else {
                alert(message);
            }
        },
        
        /**
         * Exibe sucesso
         */
        showSuccess: function(message) {
            if (typeof bootstrap !== 'undefined') {
                this.showBootstrapAlert(message, 'success');
            } else {
                alert(message);
            }
        },
        
        /**
         * Cria alerta Bootstrap
         */
        showBootstrapAlert: function(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.setAttribute('role', 'alert');
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const form = this.form || document.body;
            form.insertBefore(alertDiv, form.firstChild);
            
            // Auto-remove após 5 segundos
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        },
        
        // ========================================
        // UTILIDADES
        // ========================================
        
        /**
         * Obtém o CSRF token
         */
        getCSRFToken: function() {
            const input = document.querySelector('[name=csrfmiddlewaretoken]');
            if (input) {
                return input.value;
            }
            
            // Tenta pegar do cookie
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='));
            
            return cookieValue ? cookieValue.split('=')[1] : '';
        },
        
        /**
         * Formata preço
         */
        formatPrice: function(price) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(price);
        }
    };
    
    // ========================================
    // FUNÇÕES AUXILIARES GLOBAIS
    // ========================================
    
    /**
     * Inicializa o checkout quando a página carregar
     */
    window.initCheckout = function(stripePublicKey) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                CheckoutManager.init(stripePublicKey);
            });
        } else {
            CheckoutManager.init(stripePublicKey);
        }
    };
    
    /**
     * Aplica cupom de desconto
     */
    window.applyCoupon = async function(couponCode) {
        if (!couponCode) {
            alert('Por favor, insira um código de cupom');
            return;
        }
        
        try {
            const csrfToken = CheckoutManager.getCSRFToken();
            
            const response = await fetch('/payments/apply-coupon/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ coupon_code: couponCode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                CheckoutManager.showSuccess(`Cupom aplicado! Desconto: ${data.discount}%`);
                // Atualiza o preço na tela
                if (data.new_price) {
                    updatePriceDisplay(data.new_price);
                }
            } else {
                CheckoutManager.showError(data.error || 'Cupom inválido');
            }
        } catch (error) {
            console.error('Erro ao aplicar cupom:', error);
            CheckoutManager.showError('Erro ao aplicar cupom');
        }
    };
    
    /**
     * Atualiza exibição de preço
     */
    function updatePriceDisplay(newPrice) {
        const priceElements = document.querySelectorAll('.price-display .amount');
        priceElements.forEach(el => {
            el.textContent = CheckoutManager.formatPrice(newPrice);
        });
    }
    
    // ========================================
    // ANALYTICS E TRACKING
    // ========================================
    
    /**
     * Rastreia evento de checkout iniciado
     */
    function trackCheckoutStarted(planSlug) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'begin_checkout', {
                items: [{
                    id: planSlug,
                    name: planSlug,
                    category: 'subscription'
                }]
            });
        }
        
        console.log('Checkout iniciado:', planSlug);
    }
    
    /**
     * Rastreia evento de checkout completado
     */
    window.trackCheckoutCompleted = function(planSlug, value) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'purchase', {
                transaction_id: Date.now(),
                value: value,
                currency: 'BRL',
                items: [{
                    id: planSlug,
                    name: planSlug,
                    category: 'subscription',
                    price: value
                }]
            });
        }
        
        console.log('Checkout completado:', planSlug, value);
    };
    
    // Expõe o CheckoutManager globalmente para debug
    window.CheckoutManager = CheckoutManager;
    
})();

/**
 * Helper para copiar código de cupom
 */
function copyCouponCode(code) {
    navigator.clipboard.writeText(code).then(function() {
        alert('Código copiado: ' + code);
    }).catch(function(err) {
        console.error('Erro ao copiar:', err);
    });
}

/**
 * Toggle de informações de cupom
 */
function toggleCouponInfo() {
    const couponInfo = document.getElementById('coupon-info');
    if (couponInfo) {
        couponInfo.style.display = couponInfo.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Valida formato de cupom
 */
function validateCouponFormat(code) {
    // Remove espaços
    code = code.trim().toUpperCase();
    
    // Verifica se tem pelo menos 4 caracteres
    if (code.length < 4) {
        return { valid: false, message: 'Código muito curto' };
    }
    
    // Verifica se contém apenas letras e números
    if (!/^[A-Z0-9]+$/.test(code)) {
        return { valid: false, message: 'Código inválido' };
    }
    
    return { valid: true, code: code };
}

/**
 * Preview de desconto
 */
function previewDiscount(originalPrice, discountPercent) {
    const discount = originalPrice * (discountPercent / 100);
    const finalPrice = originalPrice - discount;
    
    return {
        discount: discount,
        finalPrice: finalPrice,
        savings: discount
    };
}

/**
 * Calcula parcelas
 */
function calculateInstallments(totalPrice, maxInstallments = 12) {
    const installments = [];
    
    for (let i = 1; i <= maxInstallments; i++) {
        const installmentValue = totalPrice / i;
        installments.push({
            number: i,
            value: installmentValue,
            total: totalPrice,
            formatted: `${i}x de ${formatCurrency(installmentValue)}`
        });
    }
    
    return installments;
}

/**
 * Formata moeda
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Inicialização automática se a chave pública estiver disponível
 */
(function() {
    const stripeKeyElement = document.getElementById('stripe-public-key');
    if (stripeKeyElement) {
        const stripeKey = stripeKeyElement.value || stripeKeyElement.textContent;
        if (stripeKey) {
            window.initCheckout(stripeKey);
        }
    }
})();