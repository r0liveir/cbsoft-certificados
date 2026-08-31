# Certificados CBSoft

CLI em Python para gerar um certificado PDF por linha de uma aba de planilha. O modelo é genérico: selecione o slide do certificado e use variáveis como `{{NOME_REVISOR}}` ou `{{NOME_EVENTO}}` no PowerPoint.

## Instalação

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Instale também o LibreOffice e mantenha `libreoffice` disponível no `PATH`, pois ele faz a conversão final para PDF.

## Planilha

Cada linha da aba escolhida produz um certificado. O caminho mais simples é usar os próprios nomes das variáveis como cabeçalhos:

| Aba |
| --- |
| `NOME_REVISOR` |
| `John Doe` |

O CLI busca uma variável diretamente na linha atual.

### Mapeamento opcional e amigável a coordenadores

Quando a planilha usa cabeçalhos como `Nome`, `Título` ou `Autores e Instituições`, forneça um JSON de mapeamento. O mapeamento também pode definir valores fixos, como o nome do evento. Veja [`examples/reviewer-mapping.json`](examples/reviewer-mapping.json):

```json
{
  "variables": {
    "NOME_EVENTO": { "source": "value", "value": "Nome do Evento" },
    "NOME_REVISOR": { "source": "row", "column": "Nome" }
  }
}
```

O mapeamento é definido uma vez por tipo de certificado. Use `source: "row"` para pegar valores da linha e `source: "value"` para valores fixos.

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
  --input "Template para evento - Premiados.xlsx" \
  --sheet revisor_destaque \
  --mapping examples/reviewer-mapping.json \
  --output output/revisores
```

Gere artigos premiados a partir do slide 2:

```bash
certgen generate \
  --template "Cópia de Certificados.pptx" \
  --slide 2 \
  --input "Template para evento - Premiados.xlsx" \
  --sheet artigo_destaque \
  --mapping examples/paper-mapping.json \
  --output output/artigos
```

Para uma planilha Google compartilhada publicamente ou publicada, passe a URL dela em `--input`; o CLI baixa sua exportação XLSX. Para planilhas privadas, baixe o XLSX e passe o arquivo local. Os certificados são nomeados pelo número da linha, por exemplo `revisor_destaque-1.pdf`.

Antes de criar arquivos, o CLI verifica todas as linhas e interrompe a execução caso um campo exigido esteja ausente. Para preservar melhor a tipografia, mantenha cada `{{VARIAVEL}}` inteira em uma única caixa de texto no PowerPoint.
