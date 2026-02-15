from google import genai
import os

# Testa com diferentes configurações
configs = [
    {'api_version': 'v1'},
    {'api_version': 'v1beta'},
    {}
]

modelos_testar = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'models/gemini-1.5-flash',
    'models/gemini-1.5-pro'
]

api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCPgU5ImrlF7WgsGEXCzDV4W3a3gk_QXBk')

for config in configs:
    print(f"\n{'='*60}")
    print(f"Testando com config: {config}")
    print('='*60)
    
    try:
        if config:
            client = genai.Client(api_key=api_key, http_options=config)
        else:
            client = genai.Client(api_key=api_key)
        
        # Tenta listar modelos
        print("Listando modelos...")
        try:
            models = list(client.models.list())
            print(f"✅ Encontrados {len(models)} modelos")
            for m in models[:5]:
                print(f"  - {m.name}")
        except Exception as e:
            print(f"❌ Erro ao listar: {e}")
        
        # Testa cada modelo
        for modelo in modelos_testar:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=[{'role': 'user', 'parts': [{'text': 'Oi'}]}]
                )
                print(f"✅ {modelo} FUNCIONOU!")
                break
            except Exception as e:
                erro_str = str(e)[:100]
                print(f"❌ {modelo}: {erro_str}")
        
    except Exception as e:
        print(f"❌ Erro na config: {e}")

print("\n" + "="*60)
