# questions/pdf_performance_logger.py
import logging
import time
import os
import inspect
import traceback
from functools import wraps

# Criar diretório de logs se não existir
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar o logger personalizado para performance
perf_logger = logging.getLogger('pdf.performance')
perf_logger.setLevel(logging.DEBUG)

# Adicionar handler de arquivo se ainda não existir
if not perf_logger.handlers:
    # Handler para arquivo detalhado
    file_handler = logging.FileHandler(os.path.join(log_dir, 'pdf_performance.log'))
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    perf_logger.addHandler(file_handler)

    # Handler para console com menos detalhes
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Apenas informações importantes no console
    perf_logger.addHandler(console_handler)

# Usado para rastrear tempo total da operação de geração de PDF
TIMERS = {}

class PerformanceTimer:
    """Contexto para medir e registrar o tempo de execução de blocos de código."""

    def __init__(self, operation_name, user=None, simulado_id=None, extra_data=None):
        self.operation_name = operation_name
        self.user = user
        self.simulado_id = simulado_id
        self.extra_data = extra_data or {}
        self.start_time = None

        # Identificar quem chamou este timer (arquivo e linha)
        frame = inspect.currentframe().f_back
        self.caller = f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"

    def __enter__(self):
        self.start_time = time.time()

        # Construir mensagem de início
        msg_parts = [f"INÍCIO: {self.operation_name}"]
        if self.user:
            msg_parts.append(f"usuário={self.user}")
        if self.simulado_id:
            msg_parts.append(f"simulado={self.simulado_id}")
        if self.extra_data:
            for key, value in self.extra_data.items():
                msg_parts.append(f"{key}={value}")

        perf_logger.debug(f"{' | '.join(msg_parts)} [em {self.caller}]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time

        # Construir mensagem de finalização
        msg_parts = [f"FIM: {self.operation_name} ({elapsed:.3f}s)"]
        if self.user:
            msg_parts.append(f"usuário={self.user}")
        if self.simulado_id:
            msg_parts.append(f"simulado={self.simulado_id}")

        if self.extra_data:
            for key, value in self.extra_data.items():
                msg_parts.append(f"{key}={value}")

        # Se houve exceção, registrar erro
        if exc_type:
            perf_logger.error(f"{' | '.join(msg_parts)} - ERRO: {exc_val} [em {self.caller}]")
            perf_logger.error(traceback.format_exc())
        else:
            log_level = logging.INFO if elapsed > 1.0 else logging.DEBUG
            perf_logger.log(log_level, f"{' | '.join(msg_parts)} [em {self.caller}]")

        return False  # Não suprimir exceções

    def log_intermediate(self, step_name, **additional_data):
        """Registra um ponto intermediário durante a execução."""
        elapsed = time.time() - self.start_time

        msg_parts = [f"ETAPA: {self.operation_name} > {step_name} ({elapsed:.3f}s)"]
        if self.user:
            msg_parts.append(f"usuário={self.user}")
        if self.simulado_id:
            msg_parts.append(f"simulado={self.simulado_id}")

        for key, value in additional_data.items():
            msg_parts.append(f"{key}={value}")

        perf_logger.debug(f"{' | '.join(msg_parts)}")

def time_function(func):
    """Decorador para medir o tempo de execução de uma função."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        # Tentar identificar simulado_id se presente em args ou kwargs
        simulado_id = None
        user = None

        # Tentar extrair informações do simulado e usuário dos argumentos
        for arg in args:
            if hasattr(arg, 'pk') and hasattr(arg, 'titulo'):
                simulado_id = getattr(arg, 'pk', None)
            if hasattr(arg, 'user') and hasattr(arg.user, 'username'):
                user = arg.user.username

        start_time = time.time()
        perf_logger.debug(f"INÍCIO FUNÇÃO: {func_name} | simulado={simulado_id} | user={user}")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            perf_logger.info(f"FIM FUNÇÃO: {func_name} ({elapsed:.3f}s) | simulado={simulado_id} | user={user}")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            perf_logger.error(f"ERRO FUNÇÃO: {func_name} ({elapsed:.3f}s) | simulado={simulado_id} | user={user} | erro={str(e)}")
            perf_logger.error(traceback.format_exc())
            raise

    return wrapper

def start_operation_timer(operation_id, description):
    """Inicia um temporizador para uma operação de longa duração."""
    TIMERS[operation_id] = {
        'start': time.time(),
        'description': description
    }
    perf_logger.info(f"OPERAÇÃO INICIADA: {description} [id={operation_id}]")

def end_operation_timer(operation_id, success=True, **extra_data):
    """Finaliza e registra um temporizador para uma operação de longa duração."""
    if operation_id in TIMERS:
        timer_data = TIMERS.pop(operation_id)
        elapsed = time.time() - timer_data['start']

        msg = f"OPERAÇÃO {'CONCLUÍDA' if success else 'FALHOU'}: {timer_data['description']} ({elapsed:.3f}s) [id={operation_id}]"

        if extra_data:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra_data.items())
            msg += f" | {extra_str}"

        if success:
            perf_logger.info(msg)
        else:
            perf_logger.error(msg)

        return elapsed
    return None

def log_file_size(file_path, description):
    """Registra o tamanho de um arquivo."""
    if os.path.exists(file_path):
        size_kb = os.path.getsize(file_path) / 1024.0
        size_mb = size_kb / 1024.0

        if size_mb >= 1.0:
            perf_logger.info(f"ARQUIVO: {description} - {size_mb:.2f} MB [{file_path}]")
        else:
            perf_logger.info(f"ARQUIVO: {description} - {size_kb:.2f} KB [{file_path}]")
    else:
        perf_logger.warning(f"ARQUIVO NÃO ENCONTRADO: {description} [{file_path}]")