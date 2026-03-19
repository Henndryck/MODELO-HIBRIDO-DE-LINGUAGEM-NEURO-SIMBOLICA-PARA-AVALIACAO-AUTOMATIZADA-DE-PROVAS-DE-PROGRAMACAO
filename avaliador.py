import json
import ast
from llama_cpp import Llama

class AvaliadorIA:
    def __init__(self, caminho_modelo):
        print(">>> Inicializando Motor Híbrido (Estável)...")
        self.llm = Llama(model_path=caminho_modelo, n_ctx=4096, n_gpu_layers=-1, verbose=False)

    def _verificar_loops(self, tree):
        violacoes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.While): violacoes.append("Uso de laço 'WHILE'")
            if isinstance(node, ast.For): violacoes.append("Uso de laço 'FOR'")
        return violacoes

    def _verificar_recursao(self, tree):
        nomes_funcoes = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in nomes_funcoes: return [] 
        return []

    def _verificar_funcoes_prontas(self, tree, lista_proibida):
        violacoes = []
        for node in ast.walk(tree):
            nome = None
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name): nome = node.func.id
                elif isinstance(node.func, ast.Attribute): nome = node.func.attr
            if nome and nome in lista_proibida:
                violacoes.append(f"Uso da função proibida '{nome}()'")
        return violacoes

    def _analise_estatica_dinamica(self, codigo, config):
        try:
            tree = ast.parse(codigo)
            relatorio_erros = []

            # Verificar configurações da rubrica
            if config.get("proibir_loops", False):
                erros = self._verificar_loops(tree)
                if erros: relatorio_erros.extend(erros)

            proibidas = config.get("proibir_funcoes_prontas", [])
            if proibidas:
                erros = self._verificar_funcoes_prontas(tree, proibidas)
                if erros: relatorio_erros.extend(erros)

            if config.get("proibir_recursao", False):
                nomes_funcoes = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                recursivo = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id in nomes_funcoes: recursivo = True
                if recursivo: relatorio_erros.append("Uso de Recursividade")

            if not relatorio_erros:
                return "SUCESSO"
            
            return "VIOLAÇÕES DETECTADAS: " + ", ".join(set(relatorio_erros))

        except SyntaxError:
            return "ERRO CRÍTICO: Código com erro de sintaxe (não compila)."
        except Exception as e:
            return f"ERRO NO ANALISADOR: {str(e)}"

    def avaliar(self, enunciado, rubrica, codigo_aluno):
        config_ast = rubrica.get("configuracao_ast", {})
        relatorio_ast = self._analise_estatica_dinamica(codigo_aluno, config_ast)
        
        
        if "ERRO CRÍTICO" in relatorio_ast or "VIOLAÇÕES" in relatorio_ast:
            
            print(f">>> BLOQUEIO AST: {relatorio_ast}")
            
            return {
                "raciocinio": f"O código foi rejeitado automaticamente pela análise estática. Motivo: {relatorio_ast}",
                "nota_final": 0.0,
                "pontos_positivos": [],
                "pontos_negativos": [relatorio_ast],
                "feedback": f"Seu código não pôde ser avaliado. Erro estrutural grave: {relatorio_ast}"
            }
       
        prompt = f"""[INST] <<SYS>>
Você é um professor de programação. O código passou na verificação de sintaxe.
Avalie a LÓGICA do algoritmo.

CRITÉRIOS:
1. Se a lógica estiver correta e resolver o problema: Nota 10.
2. Se tiver erros de lógica (índices, loop infinito, cálculo errado): Variação da nota.
3. Se fugir do tema (ex: média em vez de ordenação): Nota 0.

IMPORTANTE:
Analise o que o enunciado pede. Escreva o feedback direto para o aluno.

SAÍDA JSON:
{{
  "raciocinio": "Análise da lógica",
  "nota_final": 0.0,
  "pontos_positivos": ["Acertos"],
  "pontos_negativos": ["Erros"],
  "feedback": " "
}}
<</SYS>>

### ENUNCIADO:
{enunciado}

### CÓDIGO DO ALUNO:
{codigo_aluno}

### SUA RESPOSTA (JSON):
[/INST]"""
        
        print(f">>> ESTRUTURA OK. Analisando Lógica com IA...")
        
        output = self.llm(prompt, max_tokens=1000, temperature=0.1, stop=["[/INST]"])
        texto_gerado = output['choices'][0]['text'].strip()
        
        try:
            inicio = texto_gerado.find('{')
            fim = texto_gerado.rfind('}') + 1
            return json.loads(texto_gerado[inicio:fim])
        except:
            return {
                "raciocinio": "Erro ao processar JSON da IA.",
                "nota_final": 0.0,
                "pontos_positivos": [],
                "pontos_negativos": ["Falha técnica na resposta da IA"],
                "feedback": "Erro interno. Verifique o console."
            }