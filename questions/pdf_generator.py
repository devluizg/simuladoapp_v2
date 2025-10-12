#pdf_generator.py
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from io import BytesIO
import os
from django.conf import settings
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def generate_pdf(simulado):
    # Renderiza o template HTML
    html_string = render_to_string('questions/simulado_pdf.html', {
        'simulado': simulado,
        'questoes': simulado.questoes.all(),
    })

    # Cria um arquivo PDF
    result = BytesIO()

    # Configurações do PDF
    pdf_options = {
        'page-size': 'A4',
        'margin-top': '2cm',
        'margin-right': '2cm',
        'margin-bottom': '2cm',
        'margin-left': '2cm',
        'allow-spliting': True,
    }

    # Converte HTML para PDF com as configurações
    pdf = pisa.CreatePDF(
        BytesIO(html_string.encode('UTF-8')),
        result,
        encoding='UTF-8',
        link_callback=fetch_resources
    )

    if not pdf.err:
        return HttpResponse(
            result.getvalue(),
            content_type='application/pdf'
        )
    return None

def fetch_resources(uri, rel):
    """
    Callback para recuperar recursos (imagens, etc)
    """
    if uri.startswith('http'):
        return uri

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = os.path.join(settings.STATIC_ROOT, uri)

    if not os.path.isfile(path):
        return uri

    return path

def gerar_cartao_resposta_pdf(dir_path, caderno, tipo, num_questoes):
    """Gera um cartão resposta padrão em formato PDF com índices fora do retângulo."""
    nome_arquivo = f"{dir_path}/Cartao_Resposta_{caderno}_Tipo{tipo}.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    c.setTitle(f"Cartão Resposta - Tipo {tipo}")
    c.setAuthor("Sistema de Correção")
    c.setSubject("Cartão Resposta")
    c.setPageCompression(0)
    largura, altura = A4

    # Determina o número de colunas: 1 coluna para até 23 questões, 2 colunas para 24-45 questões
    num_colunas = 1 if num_questoes <= 23 else 2

    # Distribuição das questões entre as colunas
    questoes_por_coluna = []
    if num_colunas == 1:
        questoes_por_coluna = [num_questoes]
    else:
        # MODIFICAÇÃO: Se número de questões for ímpar, coloca uma questão a mais na primeira coluna
        if num_questoes % 2 == 0:  # Se for par
            questoes_por_coluna = [num_questoes // 2, num_questoes // 2]
        else:  # Se for ímpar
            questoes_por_coluna = [(num_questoes // 2) + 1, num_questoes // 2]

    # Dimensões básicas
    margem_superior = 50 * mm
    margem_lateral = 30 * mm
    espaco_entre_colunas = 15 * mm
    alternativas = ['A', 'B', 'C', 'D', 'E']
    diametro_circulo = 4 * mm
    espaco_entre_circulos = 6 * mm
    espaco_entre_questoes = 8 * mm
    margem_interna = 3 * mm
    largura_bolhas = (5 * espaco_entre_circulos)
    largura_indice = 8 * mm  # Ainda usado, mas agora fora do retângulo
    largura_necessaria = largura_bolhas + (2 * margem_interna)

    largura_total_necessaria = (largura_necessaria * num_colunas) + (espaco_entre_colunas * (num_colunas - 1)) + (largura_indice * num_colunas)
    margem_lateral = (largura - largura_total_necessaria) / 2

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem_lateral- 20 * mm, altura - 20 * mm, f"CARTÃO RESPOSTA - TIPO {tipo}")

    questoes_processadas = 0

    for coluna in range(num_colunas):
        x_inicial_indice = margem_lateral + (coluna * (largura_necessaria + espaco_entre_colunas + largura_indice))
        x_inicial_retangulo = x_inicial_indice + largura_indice
        largura_bolhas_total = (len(alternativas) - 1) * espaco_entre_circulos
        x_inicial_bolhas = x_inicial_retangulo + ((largura_necessaria - largura_bolhas_total) / 2)

        questoes_nesta_coluna = questoes_por_coluna[coluna]
        altura_necessaria = (questoes_nesta_coluna * espaco_entre_questoes) + (2 * margem_interna)

        c.setLineWidth(0.7 * mm)
        c.rect(x_inicial_retangulo,
              altura - margem_superior - altura_necessaria,
              largura_necessaria,
              altura_necessaria)

        # Cabeçalho das alternativas
        for i, alt in enumerate(alternativas):
            x = x_inicial_bolhas + (i * espaco_entre_circulos)
            y = altura - margem_superior + 5 * mm
            c.setFont("Helvetica", 10)
            c.drawString(x - 1 * mm, y, alt)

        for q in range(questoes_nesta_coluna):
            numero_questao = questoes_processadas + q + 1
            y = altura - margem_superior - ((q + 1) * espaco_entre_questoes)

            # Número da questão FORA do retângulo
            c.setFont("Helvetica", 10)
            if numero_questao < 10:
                c.drawString(x_inicial_indice, y - 1 * mm, f"0{numero_questao}")
            else:
                c.drawString(x_inicial_indice, y - 1 * mm, f"{numero_questao}")

            # Bolhas das alternativas
            for i in range(5):
                x = x_inicial_bolhas + (i * espaco_entre_circulos)
                c.circle(x, y, diametro_circulo / 2, stroke=1, fill=0)

        questoes_processadas += questoes_nesta_coluna

    c.setFont("Helvetica", 8)
    c.drawString(margem_lateral, 15 * mm, f"Total de questões: {num_questoes}")
    c.drawString(margem_lateral, 10 * mm, "Preencha completamente os círculos com caneta preta ou azul")

    c.save()
    return nome_arquivo