from django import template
import random
import re
from bs4 import BeautifulSoup
import base64

register = template.Library()

@register.filter
def shuffle(arg):
    """Embaralha uma lista de itens aleatoriamente"""
    tmp = list(arg)[:]
    random.shuffle(tmp)
    return tmp

@register.filter
def get_item(dictionary, key):
    """Obtém um item de um dicionário pela chave"""
    return dictionary.get(key)

@register.filter
def extract_image_src(html_content):
    """Extrai o URL da primeira imagem encontrada no HTML"""
    if not html_content:
        return ""

    # Tentar extrair usando regex (mais rápido)
    match = re.search(r'<img[^>]+src="([^">]+)"', str(html_content))
    if match:
        return match.group(1)

    # Se falhar, usar BeautifulSoup
    try:
        soup = BeautifulSoup(str(html_content), 'html.parser')
        img = soup.find('img')
        if img and img.has_attr('src'):
            return img['src']
    except:
        pass

    return ""

@register.filter
def contains(text, substring):
    """Verifica se um texto contém uma substring"""
    if text is None:
        return False
    return substring in str(text)

@register.filter
def is_image(text):
    """Verifica se o texto contém uma tag de imagem"""
    if not text:
        return False
    return '<img' in str(text)

@register.filter
def strip_images(html_content):
    """Remove imagens do conteúdo HTML, retornando apenas o texto"""
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(str(html_content), 'html.parser')
        # Remover todas as tags img
        for img in soup.find_all('img'):
            img.decompose()
        return str(soup)
    except:
        # Fallback para regex se o BeautifulSoup falhar
        return re.sub(r'<img[^>]*>', '', str(html_content))

@register.filter
def base64(value):
    """Converte bytes para string em base64"""
    if value:
        try:
            return base64.b64encode(value).decode('utf-8')
        except Exception:
            return ""
    return ""

@register.filter
def simplify_html(html_content):
    """Simplifica o HTML removendo comentários e espaços em branco desnecessários"""
    if not html_content:
        return ""

    # Remover comentários
    cleaned = re.sub(r'<!--.*?-->', '', str(html_content), flags=re.DOTALL)
    # Remover espaços em branco excessivos
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned