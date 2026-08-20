# Dados da equipe

O gerador procura `dados/equipe_real.json`. Se o arquivo existir, a planilha é construída com o
cadastro e as ausências reais e gravada como `Centro_Cirurgico_Escala_Diaria_REAL.xlsx`.
Se não existir, é usado o cadastro fictício de demonstração embutido no gerador.

`equipe_real.json` e `*_REAL.xlsx` estão no `.gitignore`: **o repositório é público e não deve
receber nome, COREN ou matrícula de ninguém.**

Formato:

```json
{
 "pessoas":   [{"nome": "...", "coren": "...", "matricula": "...", "funcao": "Téc.Enf.", "horario": "07:00-13:00"}],
 "ausencias": [{"tec": "...", "tipo": "Folga|Férias|Atestado|Licença|Treinamento|FH|Licença gestação",
                "ini": "AAAA-MM-DD", "fim": "AAAA-MM-DD"}],
 "afastados": ["nome de quem está fora do quadro no período"],
 "periodo_ini": "AAAA-MM-DD",
 "coordenacao": "Enfª ..."
}
```
