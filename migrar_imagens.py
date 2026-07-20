"""
Script de migração: converte imagens antigas (caminho /static/uploads/...)
para Base64 diretamente no MongoDB.

Execute uma vez na sua máquina antes de compartilhar o banco:
    python migrar_imagens.py
"""

import os
import base64
from config.database import get_database

MIME_TYPES = {
    'jpg':  'image/jpeg',
    'jpeg': 'image/jpeg',
    'png':  'image/png',
    'gif':  'image/gif',
    'webp': 'image/webp',
}

def caminho_para_base64(imagem_url: str) -> str | None:
    """Recebe '/static/uploads/arquivo.jpg' e retorna a data URI em Base64."""
    # Monta o caminho absoluto relativo à pasta do script
    caminho_relativo = imagem_url.lstrip('/')          # 'static/uploads/arquivo.jpg'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_absoluto = os.path.join(base_dir, caminho_relativo)

    if not os.path.isfile(caminho_absoluto):
        print(f"  [AVISO] Arquivo não encontrado: {caminho_absoluto}")
        return None

    extensao = caminho_absoluto.rsplit('.', 1)[-1].lower()
    mime = MIME_TYPES.get(extensao, 'image/jpeg')

    with open(caminho_absoluto, 'rb') as f:
        dados = f.read()

    b64 = base64.b64encode(dados).decode('utf-8')
    return f"data:{mime};base64,{b64}"


def migrar():
    db = get_database()
    colecao = db['atendimentos']

    # Busca todos os registros que ainda têm caminho de arquivo (começa com /static/)
    registros_antigos = list(colecao.find(
        {"imagem_url": {"$regex": "^/static/uploads/"}},
        {"_id": 1, "paciente_nome": 1, "imagem_url": 1}
    ))

    if not registros_antigos:
        print("Nenhum registro com caminho antigo encontrado. Banco já está atualizado.")
        return

    print(f"Encontrados {len(registros_antigos)} registro(s) para migrar.\n")

    convertidos = 0
    falhos = 0

    for registro in registros_antigos:
        nome = registro.get('paciente_nome', 'desconhecido')
        imagem_url = registro['imagem_url']
        print(f"Migrando: {nome} — {imagem_url}")

        nova_url = caminho_para_base64(imagem_url)

        if nova_url:
            colecao.update_one(
                {"_id": registro["_id"]},
                {"$set": {"imagem_url": nova_url}}
            )
            print(f"  [OK] Convertido com sucesso.")
            convertidos += 1
        else:
            falhos += 1

    print(f"\nMigração concluída: {convertidos} convertido(s), {falhos} não encontrado(s).")


if __name__ == '__main__':
    migrar()
