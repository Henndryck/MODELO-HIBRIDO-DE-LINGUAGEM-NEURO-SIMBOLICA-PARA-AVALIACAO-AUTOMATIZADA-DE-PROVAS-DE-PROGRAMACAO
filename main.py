import argparse
import os
import json
import csv
import glob
from avaliador import AvaliadorIA

def ler_arquivo(caminho):
    if not os.path.exists(caminho):
        print(f"ERRO: Arquivo não encontrado: {caminho}")
        return None
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()

def modo_lote(avaliador, args):
    print(f"\n--- INICIANDO CORREÇÃO EM LOTE (Turma: {args.pasta_alunos}) ---")
    texto_enunciado = ler_arquivo(args.enunciado)
    json_rubrica = json.loads(ler_arquivo(args.rubrica))
    
    arquivos_alunos = glob.glob(os.path.join(args.pasta_alunos, "*.py"))
    
    relatorio_geral = []

    for caminho_aluno in arquivos_alunos:
        nome_aluno = os.path.basename(caminho_aluno)
        print(f"\n> Avaliando: {nome_aluno}...")
        
        texto_codigo = ler_arquivo(caminho_aluno)
        resultado = avaliador.avaliar(texto_enunciado, json_rubrica, texto_codigo)
        
        # Salvar JSON
        caminho_json = caminho_aluno.replace(".py", "_resultado.json")
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        
        # Feedback Visual
        nota = resultado.get("nota_final", 0.0)
        print(f"  -> Nota: {nota} | Raciocínio: {resultado.get('raciocinio', '')[:60]}...")

        # Preparação do CSV
        texto_negativo = str(resultado.get("pontos_negativos", [])).lower()
        is_violacao = "violação" in texto_negativo or "erro crítico" in texto_negativo or "proibida" in texto_negativo
        
        feedback_limpo = resultado.get("feedback", "").replace('\n', ' ').replace('\r', '').replace(';', ',')

        relatorio_geral.append({
            "Arquivo": nome_aluno,
            "Nota": str(nota).replace('.', ','),
            "Status AST": "VIOLAÇÃO" if is_violacao else "OK",
            "Feedback Resumido": feedback_limpo[:150]
        })

    # Gerar CSV
    caminho_csv = "Relatorio_Notas_Turma.csv"
    with open(caminho_csv, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Arquivo", "Nota", "Status AST", "Feedback Resumido"], delimiter=';')
        writer.writeheader()
        writer.writerows(relatorio_geral)
    
    print(f"\nCONCLUÍDO! Planilha salva em: {caminho_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelo', default="codellama-7b-instruct.Q4_K_M.gguf")
    parser.add_argument('--enunciado', required=True)
    parser.add_argument('--rubrica', required=True)
    parser.add_argument('--pasta_alunos', required=True)
    
    args = parser.parse_args()
    avaliador = AvaliadorIA(args.modelo)
    modo_lote(avaliador, args)

if __name__ == "__main__":
    main()