# Catálogo de modelos de cena (gerado por producao/catalogo.py — não editar à mão)

Campos comuns a todos: `tipo`, `em` (palavras da narração onde a cena começa; None = início do capítulo),
`passos` (quando cada elemento entra: segundos desde o início da cena OU palavras da narração; 99 = nunca/fim),
`detetive` (pose: neutro, pensa, desconfia, surpreso, preocupado, bravo, aponta), `fundo` (papel|noite|agua), `foco` [x,y], `semFade`.
Texto com *asteriscos* = destaque em itálico terracota.

## titulo
- campos lidos: `alinha`, `detX`, `detetive`, `fundo`, `icone`, `iconeS`, `iconeX`, `iconeY`, `maxW`, `sub`, `tam`, `texto`, `y`
- exemplo real (bankskandale-completo):
```python
{"tipo": "titulo", "em": "Bar einzahlen", "texto": "Bar einzahlen *fällt auf.*", "icone": "alerta", "detetive": "preocupado"}
```

## numero
- campos lidos: `carimbo`, `casas`, `conta`, `fundo`, `icone`, `nota`, `nota2`, `prefixo`, `rotulo`, `sufixo`, `tam`, `valor`
- exemplo real (bankskandale-completo):
```python
{"tipo": "numero", "em": "über", "valor": 900, "prefixo": "über ", "sufixo": "Kunden", "rotulo": "betreut von einer Gesellschaft", "icone": "documento", "passos": [0.1, 99, 99]}
```

## comparar
- campos lidos: `carimbo`, `fundo`, `itens`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "comparar", "em": "Und 2024", "titulo": "Und *2024?*", "itens": [{"valor": 4.25, "texto": "4,25 Mio. €", "rotulo": "Bußgeld 2021"}, {"valor": 9.2, "texto": "9,2 Mio. €", "rotulo": "Bußgeld 2024"}], "passos": [0.4, "nächste Bußgeld", 99]}
```

## local
- campos lidos: `data`, `fundo`, `lugar`, `seed`, `sub`
- exemplo real (bankskandale-completo):
```python
{"tipo": "local", "em": "Allein eine Konzerngesellschaft", "lugar": "Britische Jungferninseln", "data": "2016", "sub": "eine Konzerngesellschaft", "passos": ["Jungferninseln", "soll"]}
```

## banco
- campos lidos: `carimbo`, `carimboTam`, `cor`, `detetive`, `fundo`, `nome`, `sub`, `subY`, `tam`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "banco", "em": "Die Berliner Smartphone-Bank", "nome": "N26", "titulo": "N26", "sub": "Smartphone-Bank aus Berlin", "passos": [0.6, 99], "detetive": "desconfia"}
```

## rota
- campos lidos: `cidades`, `fundo`, `nota`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "rota", "em": "Ein Beispiel", "titulo": "Ein Beispiel: *rund 55 Mio. Dollar* von VimpelCom", "cidades": [["ING-Konto", 520, 600, "Telekomkonzern VimpelCom"], ["Gibraltar", 1400, 600, "eine Firma"]], "passos": ["ING-Konto", "Gibraltar"]}
```

## fluxo
- campos lidos: `destacaFim`, `fundo`, `nos`, `nota`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "fluxo", "em": "und Geld aus Straftaten", "titulo": "Geld aus Straftaten *durchschleusen*", "nos": [{"texto": "Geld aus Straftaten", "icone": "notas"}, {"texto": "Briefkastenfirma", "icone": "documento"}, {"texto": "Bankkonto", "icone": "banco"}], "passos": [0.2, 0.9, 1.6, 99], "destacaFim": true}
```

## iceberg
- campos lidos: `nivel`, `passos`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "iceberg", "em": "Und es fängt harmlos an", "nivel": 0, "passos": ["Bank auf deinem Handy", "die einfach wegschauen", "wegschauen", "Kartellgeld", "einzigen Filiale", "ganz unten", "Das ist der Eisberg"], "titulo": "Der Eisberg der *Geldwäsche-Skandale*"}
```

## documento
- campos lidos: `aspas`, `cabecalho`, `carimbo`, `citacao`, `detetive`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "documento", "em": "Der Verdacht", "cabecalho": "Razzia · 29.11.2018", "titulo": "Der Verdacht", "citacao": "Briefkastenfirmen in Steueroasen gründen", "passos": ["Briefkastenfirmen", 99], "detetive": "desconfia"}
```

## lista
- campos lidos: `detetive`, `fundo`, `itens`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "lista", "em": "Wir haben", "titulo": "Wir haben durchgesehen:", "itens": ["Gerichtsakten", "Behördenberichte", "Leaks"], "passos": ["Gerichtsakten", "Behördenberichte", "Leaks"], "detetive": "pensa"}
```

## celular
- campos lidos: `fase`, `sub`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "celular", "em": "Also brauchst du", "fase": "abrir", "texto": "Ein Konto – *per App* eröffnet", "passos": ["per App", 99]}
```

## guiche
- campos lidos: `sub`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "guiche", "em": "Drogenhändler lassen sich", "texto": "Kisten mit den *exakten Maßen* der Schalterfenster", "sub": "Damit das Bargeld genau durch den Schalter passt.", "passos": ["Damit das Bargeld"]}
```

## carta
- campos lidos: `anos`, `destinos`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "carta", "em": "Ende 2013", "texto": "Ende 2013: eine *Warnung*", "destinos": ["Vorstand", "Compliance", "interne Revision"], "anos": "fast 5 Jahre", "passos": ["Vorstand", "Es dauert"]}
```

## teia
- campos lidos: `centro`, `sub`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "teia", "em": "Der Senat beschreibt", "texto": "Ein *kunstvolles Spinnennetz*", "sub": "verbunden über eine undurchdringliche Reihe von Holdinggesellschaften", "passos": ["undurchdringliche"]}
```

## balanca
- campos lidos: `direita`, `esquerda`, `sub`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "balanca", "em": "Doch die Bank wird nicht angeklagt", "texto": "Angeklagt: *niemand.*", "esquerda": "1,9 Mrd. $", "direita": "Anklagen: 0", "sub": "Nicht die Bank. Und keine einzige Person.", "passos": [0.4, "keine einzige"]}
```

## detetive
- campos lidos: `balao`, `fundo`, `icone`, `pose`, `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "detetive", "em": "Stell dir vor", "pose": "pensa", "icone": "notas", "balao": "Geld aus einem Betrug", "passos": ["Betrug"]}
```

## tempo
- campos lidos: `marcos`, `titulo`
- exemplo real (bankskandale-completo):
```python
{"tipo": "tempo", "em": "Bei der Deutschen Bank ist es", "titulo": "Kein einzelner Skandal – *eine Reihe*", "marcos": [["2017", "Spiegelgeschäfte"], ["2018", "Razzia Frankfurt"], ["2020", "Epstein"], ["2020", "FinCEN Files"]], "passos": [0.3, 0.8, 1.3, 1.8]}
```

## cta
- campos lidos: `texto`
- exemplo real (bankskandale-completo):
```python
{"tipo": "cta", "em": "Wenn du wissen willst", "texto": "Alle Methoden der Geldwäscher – *erklärt.*", "passos": ["abonnier"]}
```

## thumb
- campos lidos: —
