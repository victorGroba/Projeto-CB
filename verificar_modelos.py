import google.generativeai as genai
import os

# Configura a chave
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERRO: Chave API não encontrada!")
    exit()

genai.configure(api_key=api_key)

print(f"--- Consultando modelos disponíveis para sua chave ---")
try:
    # Lista os modelos
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Nome: {m.name}")
            
    print("--- Fim da lista ---")
except Exception as e:
    print(f"ERRO AO LISTAR: {e}")
