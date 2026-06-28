from src.execution.verify_loop import verify_and_correct

pergunta = "escreva uma função Python que recebe uma lista de números e retorna só os números pares"

resposta_com_bug = """
```python
def filtra_pares(numeros):
    return [n for n in numeros if n % 2 = 0]

print(filtra_pares([1, 2, 3, 4, 5, 6]))
```
"""

resultado = verify_and_correct(pergunta, resposta_com_bug)

print(f"Tem código: {resultado['tem_codigo']}")
print(f"Sucesso final: {resultado['sucesso_final']}\n")

for t in resultado["tentativas"]:
    print(f"--- Tentativa {t['numero']} ---")
    print(f"Sucesso: {t['sucesso']}")
    if t["sucesso"]:
        print(f"stdout: {t['stdout']}")
    else:
        print(f"stderr: {t['stderr']}")
    print()