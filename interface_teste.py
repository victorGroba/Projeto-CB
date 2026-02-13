import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tools import tools_config, ferramenta_ver_agenda, agendar_consulta

# Carrega variáveis de ambiente
load_dotenv()

# --- Configuração da Página ---
st.set_page_config(page_title="Teste Clara - IA", page_icon="🤖")
st.title("🤖 Clara - Ambiente de Teste")
st.caption("Teste a lógica da IA e o uso de ferramentas sem usar o WhatsApp.")

# --- Configuração da API ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ Chave API não encontrada no .env")
    st.stop()

genai.configure(api_key=api_key)

# --- Personalidade (Prompt do Sistema) ---
system_instruction = """
Você é a Clara, secretária virtual do Dr. Victor.
Sua função é agendar consultas e tirar dúvidas sobre a clínica.

PERSONALIDADE:
- Seja empática, profissional e direta.
- Use emojis moderadamente (ex: 👋, 📅).
- Use formatação (negrito, listas) para facilitar a leitura.

REGRAS OBRIGATÓRIAS:
1. Se perguntarem horários, você DEVE usar a ferramenta 'ver_agenda'.
2. Para agendar, colete: Nome, Telefone e Data de Nascimento.
3. Antes de finalizar com 'agendar_consulta', peça confirmação dos dados.
"""

# --- Inicialização do Chat (Memória) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Inicia o chat do Gemini com histórico vazio
    st.session_state.chat = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        tools=tools_config,
        system_instruction=system_instruction
    ).start_chat(history=[])

# --- Renderiza Mensagens Antigas ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Área de Input ---
if prompt := st.chat_input("Digite sua mensagem para a Clara..."):
    # 1. Mostra a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Processa a resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("Clara está pensando..."):
            try:
                # Envia para o Gemini
                response = st.session_state.chat.send_message(prompt)
                
                # --- Lógica de Ferramentas (Function Calling) ---
                # Loop para lidar com múltiplas chamadas (ex: ver agenda -> responder)
                while response.candidates[0].content.parts and \
                      response.candidates[0].content.parts[0].function_call:
                    
                    part = response.candidates[0].content.parts[0]
                    fn = part.function_call
                    
                    # Mostra visualmente que uma ferramenta está sendo usada
                    with st.expander(f"🛠️ Usando ferramenta: {fn.name}", expanded=False):
                        st.json(dict(fn.args))
                        
                        function_response = None
                        if fn.name == 'ver_agenda':
                            args = dict(fn.args)
                            dados = ferramenta_ver_agenda(args.get('data_relativa', 'hoje'))
                            function_response = {'result': dados}
                            st.write("Retorno da Agenda:", dados)
                            
                        elif fn.name == 'agendar_consulta':
                            args = dict(fn.args)
                            # Nota: Isso vai agendar de verdade no seu calendário!
                            # Se quiser apenas simular, comente a linha abaixo e retorne um fake.
                            resultado = agendar_consulta(
                                nome_paciente=args.get('nome_paciente'),
                                telefone=args.get('telefone'),
                                data=args.get('data'),
                                horario=args.get('horario')
                            )
                            function_response = {'result': resultado}
                            st.write("Resultado Agendamento:", resultado)
                    
                    # Devolve o resultado da ferramenta para a IA
                    if function_response:
                        response = st.session_state.chat.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=fn.name,
                                        response=function_response
                                    )
                                )]
                            )
                        )
                
                # Exibe a resposta final de texto
                texto_final = response.text
                st.markdown(texto_final)
                
                # Salva no histórico da interface
                st.session_state.messages.append({"role": "assistant", "content": texto_final})

            except Exception as e:
                st.error(f"Erro: {e}")
