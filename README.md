# Certificados CBSoft

CLI em Python para gerar um certificado PowerPoint por linha de uma planilha. O modelo é genérico: selecione o slide do certificado e use variáveis como `{{NOME_REVISOR}}` ou `{{NOME_EVENTO}}` no PowerPoint.

## Instalação

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Para PDF, instale também o LibreOffice e mantenha `libreoffice` disponível no `PATH`.

## Planilha

Uma planilha tem uma aba de dados e, opcionalmente, uma aba `config` com duas colunas: chave e valor. Cada linha da aba de dados produz um certificado. O caminho mais simples é usar os próprios nomes das variáveis como cabeçalhos/chaves:

| Aba `config` | valor |
| --- | --- |
| `NOME_EVENTO` | `Nome do Evento` |

| Aba `revisor_destaque` |
| --- |
| `NOME_REVISOR` |
| `John Doe` |

O CLI busca primeiro uma variável na linha atual e depois na aba `config`.

### Mapeamento opcional e amigável a coordenadores

Quando a planilha usa cabeçalhos como `Nome` e a chave `evento`, forneça um JSON de mapeamento. Veja [`examples/reviewer-mapping.json`](examples/reviewer-mapping.json):

```json
{
  "variables": {
    "NOME_EVENTO": { "source": "config", "key": "evento" },
    "NOME_REVISOR": { "source": "row", "column": "Nome" }
  }
}
```

O mapeamento é definido uma vez por tipo de certificado; os valores vêm de cada linha.

## Uso

Liste os campos exigidos pelo segundo slide do modelo:

```bash
certgen variables --template "Cópia de Certificados.pptx" --slide 3
```

Gere revisores a partir do XLSX fornecido, preservando o desenho do slide 3:

```bash
certgen generate \
  --template "Cópia de Certificados.pptx" \
  --slide 3 \
  --input "Template de Revisores Premiados.xlsx" \
  --data-sheet revisor_destaque \
  --config-sheet config \
  --mapping examples/reviewer-mapping.json \
  --output output/revisores \
  --pdf
```

Para uma planilha Google compartilhada publicamente ou publicada, passe a URL dela em `--input`; o CLI baixa sua exportação XLSX. Para planilhas privadas, baixe o XLSX e passe o arquivo local. Os certificados são nomeados pelo número da linha, por exemplo `revisor_destaque-1.pptx`.

Antes de criar arquivos, o CLI verifica todas as linhas e interrompe a execução caso um campo exigido esteja ausente. Para preservar melhor a tipografia, mantenha cada `{{VARIAVEL}}` inteira em uma única caixa de texto no PowerPoint.
