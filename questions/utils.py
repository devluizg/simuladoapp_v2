from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Frame, PageTemplate
from reportlab.lib.units import cm

def create_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    # Criar frames para as duas colunas
    frame1 = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width/2-0.25*cm,  # Largura da primeira coluna
        doc.height,
        id='col1'
    )

    frame2 = Frame(
        doc.leftMargin + doc.width/2+0.25*cm,  # Posição X da segunda coluna
        doc.bottomMargin,
        doc.width/2-0.25*cm,  # Largura da segunda coluna
        doc.height,
        id='col2'
    )

    # Criar template de página com linha separadora
    def draw_separator(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setDash(1, 2)  # Linha tracejada
        canvas.line(
            doc.leftMargin + doc.width/2,  # X1
            doc.bottomMargin,              # Y1
            doc.leftMargin + doc.width/2,  # X2
            doc.height + doc.bottomMargin   # Y2
        )

    template = PageTemplate(
        id='TwoColumns',
        frames=[frame1, frame2],
        onPage=draw_separator
    )

    doc.addPageTemplates([template])

def process_image(image_path, max_width):
    img = utils.ImageReader(image_path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)

    # Ajusta a largura para caber na coluna
    if iw > max_width:
        iw = max_width
        ih = iw * aspect

    return Image(image_path, width=iw, height=ih)

def format_alternativa(letra, texto):
    return f'''
    <para>
        <seq>{letra}</seq> {texto}
    </para>
    '''

def create_question_paragraph(questao):
    alternativas = [
        format_alternativa('A', questao.alternativa_a),
        format_alternativa('B', questao.alternativa_b),
        format_alternativa('C', questao.alternativa_c),
        format_alternativa('D', questao.alternativa_d),
        format_alternativa('E', questao.alternativa_e),
    ]

    return f'''
    <para>
        <questao_numero>{questao.numero}</questao_numero>
        {questao.enunciado}
        <alternativas>
            {''.join(alternativas)}
        </alternativas>
    </para>
    '''