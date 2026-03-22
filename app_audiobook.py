import streamlit as st
import PyPDF2
import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import edge_tts
import asyncio
import re
import tempfile

st.set_page_config(page_title="PDF para Audiobook", page_icon="🎧", layout="centered")

async def criar_audio_neural(texto, caminho_saida):
    voz = "pt-BR-AntonioNeural" 
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(caminho_saida)

def limpar_texto(texto):
    texto = re.sub(r'https?://\S+|www\.\S+', '', texto)
    texto = re.sub(r'(?m)^\s*\d+\s*$', '', texto)
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

st.title("🎧 Gerador de Audiobook Neural")
st.write("Transforme qualquer livro ou artigo em PDF em um áudio super realista para ouvir no celular.")

arquivo_enviado = st.file_uploader("Faça o upload do seu PDF aqui", type=["pdf"])

if arquivo_enviado is not None:
    if st.button("Gerar Audiobook"):
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp:
            pdf_temp.write(arquivo_enviado.read())
            caminho_pdf = pdf_temp.name
            
        caminho_audio = caminho_pdf.replace('.pdf', '.mp3')
        
        barra_progresso = st.progress(0)
        status_texto = st.empty()
        
        try:
            status_texto.info("Analisando o PDF...")
            
            with open(caminho_pdf, 'rb') as arquivo:
                leitor = PyPDF2.PdfReader(arquivo)
                total_paginas = len(leitor.pages)
                texto_teste = ""
                for i in range(min(3, total_paginas)):
                    extraido = leitor.pages[i].extract_text()
                    if extraido:
                        texto_teste += extraido
                        
            media_letras = len(texto_teste) / min(3, total_paginas) if total_paginas > 0 else 0
            texto_completo = ""
            
            if media_letras > 100:
                status_texto.info("Modo super rápido ativado (Texto Digital)...")
                with open(caminho_pdf, 'rb') as arquivo_aberto:
                    leitor_completo = PyPDF2.PdfReader(arquivo_aberto)
                    for i, pagina in enumerate(leitor_completo.pages):
                        texto_pagina = pagina.extract_text()
                        if texto_pagina:
                            texto_completo += limpar_texto(texto_pagina) + " "
                        barra_progresso.progress((i + 1) / total_paginas)
            else:
                status_texto.warning("PDF Escaneado detectado. Iniciando leitura visual (OCR) otimizada para nuvem... Isso pode demorar.")
                
                # Descobre o total de páginas sem sobrecarregar a RAM
                info = pdfinfo_from_path(caminho_pdf)
                total_paginas = info["Pages"]
                
                # Lê uma página por vez
                for i in range(1, total_paginas + 1):
                    pagina_atual = convert_from_path(caminho_pdf, first_page=i, last_page=i)[0]
                    texto_pagina = pytesseract.image_to_string(pagina_atual, lang='por')
                    texto_completo += limpar_texto(texto_pagina) + " "
                    barra_progresso.progress(i / total_paginas)
                    
            status_texto.success(f"Leitura concluída! {len(texto_completo)} letras prontas. Gravando o áudio...")
            
            asyncio.run(criar_audio_neural(texto_completo, caminho_audio))
            
            st.success("🎉 Audiobook gerado com sucesso!")
            st.audio(caminho_audio, format="audio/mp3")
            
            with open(caminho_audio, "rb") as arquivo_mp3:
                st.download_button(
                    label="⬇️ Baixar Audiobook (MP3)",
                    data=arquivo_mp3,
                    file_name=arquivo_enviado.name.replace('.pdf', '_Audiobook.mp3'),
                    mime="audio/mp3"
                )
                
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
