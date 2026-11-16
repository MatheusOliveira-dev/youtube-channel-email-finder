*Versão em inglês desta página: `README.md`.*

# YouTube Channel Email Finder

Encontra o email de contato comercial publicado por canais do YouTube, a partir
de uma lista de canais ou de uma palavra-chave de nicho. A cobrança se aplica
apenas aos canais em que um endereço é encontrado.

Taxa medida: **35,4% dos canais entregam um endereço** (124 de 350 canais
amostrados em 25 nichos). Esse número está publicado aqui, com seus intervalos
de confiança e o método por trás, porque a promessa habitual de "emails
verificados em massa" não diz nada ao comprador sobre o que uma execução vai de
fato retornar.

## Para que serve

- Montar uma lista de contatos para marketing de influência ou de criadores, por nicho
- Enriquecer uma lista de canais já existente com dados de contato
- Prospecção de patrocínio, filtrada por faixa de inscritos
- Pesquisa competitiva sobre quais criadores uma categoria está abordando
- Alimentar um CRM ou uma planilha pela API, de forma agendada

## Quanto custa uma execução

$0,03 por canal que entrega um endereço. Canais que voltam vazios não são
cobrados.

Na taxa medida, 1.000 canais varridos retornam cerca de 354 endereços e custam
aproximadamente **$10,60**, o que dá $0,03 por endereço utilizável.

Vários actors da categoria cobram por canal varrido. A $0,075 por canal, 1.000
canais custam $75 e retornam cerca de 117 endereços caso apenas a aba Sobre seja
lida — por volta de $0,64 por endereço utilizável. O número anunciado e o real
divergem, e a diferença é invisível até a execução terminar.

Existem opções mais baratas, e a tabela de comparação adiante as nomeia.

## De onde vêm os endereços

Três fontes, verificadas em ordem de custo, parando no primeiro acerto. Um canal
que publica seu endereço na aba Sobre custa, portanto, uma única requisição.

| Fonte | Canais com endereço, acumulado |
|---|---|
| 1. A aba Sobre do canal | 21,1% |
| 2. Descrições de vídeos recentes | 27,1% |
| 3. O site do próprio criador e sua página de contato | **35,4%** |

A fonte 2 existe porque muitos criadores colocam "contato comercial" na
descrição do vídeo em vez da aba Sobre; ela encontrou endereços em 21 canais nos
quais a fonte 1 não achou nada. A fonte 3 segue o link que o próprio canal
publica, resolvendo links encurtados, e verifica as páginas de contato usuais.
Ela respondeu por outros 29.

As duas podem ser desligadas com `scanVideoDescriptions` e
`enrichFromLinkedSite`, para uma passagem mais rápida que lê apenas a aba Sobre.

### Por que 35% é o teto, e não um ponto de partida

Ampliar as fontes públicas foi testado em 80 canais que hoje voltam vazios: ler
os vídeos 3 a 8, em vez de apenas os dois primeiros, converteu 1 deles, e seguir
agregadores de link não converteu nenhum. Projetado sobre a amostra inteira, isso
é +0,8 ponto, ao custo de várias vezes mais requisições.

Cerca de dois terços dos canais do YouTube não publicam endereço de contato
alcançável em lugar algum. Isso é uma característica do YouTube, e é a razão pela
qual a cobrança está atrelada a resultados, e não a canais varridos.

## Como endereços de terceiros são excluídos

O site de um criador carrega endereços que não são dele: o construtor de
formulário por trás da página de contato, a plataforma de loja, um endereço
no-reply do Patreon, ocasionalmente um órgão de padronização citado na marcação
da página. Sob cobrança por resultado, cada um desses apareceria como um achado
cobrável.

Um endereço encontrado em site linkado só é mantido quando seu domínio
corresponde ao site onde foi encontrado, ou quando pertence a um provedor de
email como Gmail ou Outlook. `hello@tally.so` em um site de dermatologia é um
construtor de formulário, não um contato, e por isso é descartado. A regra
elimina a categoria em vez de manter uma lista de nomes.

## O que as medições mostram

O tipo de nicho importa mais do que qualquer outro fator. Nichos construídos em
torno de patrocínio publicam dados de contato, porque recebem propostas e querem
estar acessíveis. Nichos de hobby e artesanato, em geral, não.

| Tipo de nicho | Canais com endereço | Confiança 95% |
|---|---|---|
| **Produtos, dinheiro, viagem** — skincare, beleza, finanças pessoais, imóveis, viagem, van life, cuidado com animais | 55/98 = **56%** | 46–66% |
| **Instrucional e profissional** — análise de tecnologia, idiomas, jardinagem, podcasts, culinária, xadrez | 30/84 = **36%** | 26–46% |
| **Hobby, artesanato e games** — marcenaria, guitarra, fitness, café, impressão 3D, fotografia, drones, carros, meditação, games, crochê | 39/168 = **23%** | 17–30% |

O tamanho do canal separa menos do que se poderia esperar, e realmente só no
extremo inferior:

| Inscritos | Canais com endereço | Confiança 95% |
|---|---|---|
| 100 mil ou mais | 81/194 = 42% | 35–49% |
| 10 mil a 100 mil | 24/59 = 41% | 29–53% |
| abaixo de 10 mil | 18/84 = 21% | 14–31% |

O filtro `minSubscribers` existe por esse motivo: um piso em torno de 10.000
mantém a execução longe da faixa em que endereços são escassos.

### Por que não há números por nicho aqui

Os mesmos 350 canais foram medidos duas vezes durante o desenvolvimento, com duas
versões do código de extração. A taxa geral quase não se moveu: 35,1% para 35,4%.
Os nichos individuais se moveram muito: van life de 64% para 50%, games de 7%
para 29%, crochê de 0% para 14%.

Cada nicho dessa amostra tem 14 canais, e nesse tamanho um resultado próximo de
50% carrega um intervalo de confiança de cerca de 45 pontos. "Van life: 64%"
significaria "algo entre 39% e 84%", o que não é preciso o suficiente para ser
publicado como orientação. Agrupados nas três famílias acima, as amostras se
mantêm estáveis: 56%, 36% e 23% na segunda execução, contra 57%, 39% e 20% na
primeira.

O detalhamento completo dos 25 nichos, com as duas execuções lado a lado e os
intervalos, está em [SAMPLE.md](https://github.com/MatheusOliveira-dev/youtube-channel-email-finder/blob/main/SAMPLE.md).

### Medindo um nicho específico

A maioria dos nichos não está nessa amostra, e uma medição do alvo real vale mais
que qualquer média publicada aqui. Como somente os endereços encontrados são
cobrados, um piloto custa muito pouco:

```json
{
  "mode": "search",
  "searchQueries": ["o nicho em questão"],
  "maxChannelsPerQuery": 50,
  "minSubscribers": 10000,
  "includeChannelsWithoutEmail": true
}
```

O log encerra com uma linha na forma
`scanned=50 with_email=19 hit_rate=38.0%`. Essa é a taxa real para aquele nicho,
e os canais vazios listados no dataset não geram cobrança.

## Quanto tempo leva uma execução

Medido em concorrência 10, com as três fontes ativas:

| Canais | Tempo aproximado |
|---|---|
| 30 | menos de um minuto |
| 100 | 1 a 2 minutos |
| 500 | 6 a 10 minutos |
| 1.000 | 12 a 20 minutos |

Canais que entregam o endereço na aba Sobre terminam em bem menos de um segundo.
O tempo é gasto nos que não entregam, já que esses acionam as buscas por vídeo e
por site. Uma execução com `scanVideoDescriptions` e `enrichFromLinkedSite`
desligados é cerca de três vezes mais rápida e encontra cerca de 40% menos
endereços.

O endpoint `run-sync-get-dataset-items` da API tem limite de 300 segundos, então
execuções acima de aproximadamente 300 canais se encaixam melhor no endpoint
assíncrono ou em um agendamento.

## Entrada

Buscando um nicho:

```json
{
  "mode": "search",
  "searchQueries": ["skincare routine", "van life"],
  "maxChannelsPerQuery": 25,
  "maxChannels": 200,
  "minSubscribers": 10000
}
```

Trabalhando a partir de uma lista existente. URLs de canal, `@handles` e ids
`UC...` são todos aceitos, e podem ser misturados:

```json
{
  "mode": "channels",
  "channels": [
    "@mkbhd",
    "https://www.youtube.com/@LinusTechTips",
    "UCBJycsmduvYEL83R_U4JriQ"
  ]
}
```

### Configurações

| Campo | Padrão | Efeito |
|---|---|---|
| `mode` | `channels` | `channels` para lista existente, `search` para encontrar por palavra-chave |
| `channels` | — | URLs, handles ou ids |
| `searchQueries` | — | palavras-chave de nicho, usadas no modo `search` |
| `maxChannelsPerQuery` | 20 | canais extraídos de cada busca |
| `maxChannels` | 100 | teto rígido da execução, para que uma busca ampla não escape do controle |
| `minSubscribers` | — | ignora canais abaixo desse tamanho |
| `maxSubscribers` | — | ignora canais acima dele, para criadores menores |
| `scanVideoDescriptions` | `true` | fonte 2; só roda quando a aba Sobre não trouxe nada |
| `enrichFromLinkedSite` | `true` | fonte 3; só roda quando as fontes 1 e 2 não trouxeram nada |
| `includeChannelsWithoutEmail` | `false` | lista também os canais vazios, mostrando tudo o que foi verificado. Nunca cobrados |
| `language` / `country` | `en` / `US` | afeta quais canais a busca retorna |
| `concurrency` | 5 | varreduras em paralelo, de 1 a 10 |

## Saída

Uma linha por canal. Uma linha real de uma execução de busca:

```json
{
  "channelId": "UC9YAqNOtA38qIymbvf3o_aQ",
  "channelUrl": "https://www.youtube.com/channel/UC9YAqNOtA38qIymbvf3o_aQ",
  "title": "sasa",
  "subscribers": 696000,
  "subscribersText": "696K",
  "videoCountText": "149",
  "emails": ["sasa@starlinemgmt.com", "sasastudio25@gmail.com"],
  "primaryEmail": "sasa@starlinemgmt.com",
  "emailCount": 2,
  "emailSource": "about",
  "sourceUrl": null,
  "externalLinks": ["https://us.selflessbyhyram.com/"],
  "queryMatched": "skincare routine",
  "hasEmail": true
}
```

| Campo | Conteúdo |
|---|---|
| `channelId`, `channelUrl` | identificador estável e link direto |
| `title` | nome do canal |
| `subscribers` | número inteiro, para ordenar e filtrar |
| `subscribersText` | o mesmo número como o YouTube exibe |
| `videoCountText` | volume de publicação, indicador de canal ativo |
| `emails` | todos os endereços encontrados, caixas comerciais primeiro |
| `primaryEmail` | o melhor candidato, para exportação de coluna única |
| `emailCount` | quantos foram encontrados |
| `emailSource` | `about`, `video_description` ou `linked_site` |
| `sourceUrl` | para `linked_site`, a página exata de onde foi lido |
| `externalLinks` | os links do próprio criador, afiliados e encurtados por último |
| `queryMatched` | qual busca trouxe o canal |
| `hasEmail` | booleano, para filtragem rápida |

`emailSource` em conjunto com `sourceUrl` torna cada resultado conferível em sua
origem. Em um produto cobrado por resultado, isso importa: é possível verificar o
que foi cobrado.

## Quando algo dá errado

| Situação | Comportamento | Cobrado |
|---|---|---|
| Nenhum endereço encontrado | Omitido do dataset, ou incluído com `hasEmail: false` quando `includeChannelsWithoutEmail` está ativo | Não |
| Fora do filtro de inscritos | Omitido, contado como `filtered` no log | Não |
| Falha de rede ou de leitura em um canal | Omitido, contado como `failed`, registrado como aviso | Não |
| Handle não pode ser resolvido | Registrado como aviso, a execução continua | Não |
| `maxChannels` alcançado | A execução para no teto | Apenas pelos endereços encontrados |

A linha final do log sempre informa `scanned`, `with_email`, `hit_rate`,
`filtered` e `failed`, de modo que uma execução que retorna pouco pode ser
distinguida de uma execução que deu errado.

## Como isso se compara

Preços conforme listados na Apify Store em novembro de 2026, com o evento de
cobrança de cada actor:

| Actor | Preço | Cobra por | Nota na store |
|---|---|---|---|
| **Este actor** | **$0,03** | canal com endereço encontrado | novo |
| `haketa/youtube-contact-scraper` | $0,003 | item do dataset | 5,0 (1 avaliação) |
| `exporter24/youtube-email-bulk-scraper` | $0,03 | item do dataset | 5,0 (3 avaliações) |
| `automation-lab/…-email-scraper` | $0,023 + $0,0023 | endereço encontrado, mais cada canal processado | sem avaliações |
| `khadinakbar/…-email-extractor` | $0,05 + $0,12 | endereço encontrado, mais um desbloqueio pago | 3,0 (1 avaliação) |
| `endspec/youtube-instant-email-scraper` | $0,075 | cada canal processado | 1,0 (2 avaliações) |
| `creatorlens/social-media-email-scraper-2026` | $0,10 | endereço encontrado | 1,41 (5 avaliações) |
| `dataovercoffee/…-Business-Email-Scraper` | $0,12 | cada email retornado | 4,4 (30 avaliações) |

Cobrar apenas por resultado não é incomum nessa categoria, e este actor não
reivindica isso como invenção. O `haketa` é dez vezes mais barato por item, e o
líder da categoria tem trinta avaliações e nota 4,4.

O que é específico deste: a taxa de acerto é medida e publicada com seus
intervalos de confiança, as fontes são documentadas e podem ser desligadas, cada
endereço carrega a fonte de onde veio, e os nichos em que o desempenho é ruim são
nomeados em vez de omitidos. Nada aqui depende de aceitar uma afirmação por
confiança.

## Perguntas

**Por que alguns canais voltam vazios?**
Cerca de dois terços dos canais não publicam endereço alcançável. Ampliar a busca
foi testado e converteu 1 de 80 canais vazios, então isso é um teto, não algo que
uma configuração resolva. Canais vazios não são cobrados.

**Consegue pegar o endereço atrás do botão "Ver endereço de email"?**
Não. Esse campo está ausente das respostas anônimas: exige uma sessão do Google
autenticada e a resolução de um captcha. Oferecer isso significaria manipular as
credenciais de sessão de quem executa o actor e contornar uma proteção colocada
especificamente para impedir coleta automatizada. Tudo que é lido aqui foi
publicado abertamente pelo canal.

**Os endereços são verificados?**
Não. São retornados exatamente como publicados. Uma passagem de verificação antes
de um envio grande é uma precaução sensata.

**Precisa de proxy, login ou cookies?**
Nenhum dos três. 350 canais foram varridos em sequência sem bloqueio, o que é o
que mantém o custo por execução baixo.

**Quão atual é o dado?**
Cada execução lê o YouTube ao vivo. Nada é armazenado em cache ou revendido entre
execuções.

**Pode rodar de forma agendada?**
Sim, pelos agendamentos da Apify, e os resultados podem ser encaminhados por
webhook ou para Google Sheets, Slack, S3 e similares.

**Como os resultados são exportados?**
O dataset exporta em JSON, JSONL, CSV, XLSX, XML, HTML ou RSS, pelo Console ou
pela API, com `fields` para escolher as colunas.

**Isso é legal?**
Os endereços são publicados pelos próprios criadores para contato comercial, e
somente dados públicos de canal são lidos. A responsabilidade pelo uso recai
sobre quem os utiliza: disparo em massa está sujeito a GDPR, CAN-SPAM e regras
equivalentes conforme a jurisdição.

**O que acontece se o YouTube mudar algo?**
O actor lê a interface interna do YouTube, portanto uma mudança lá pode quebrá-lo
até ser atualizado. A linha final do log torna a quebra evidente: a taxa de
acerto desaba enquanto `scanned` permanece normal.

## Suporte

Problemas vão para a aba Issues na página deste actor, que é acompanhada. Um
relato que inclua o id da execução e a entrada utilizada é o mais rápido de
tratar. Quebra após uma mudança do YouTube é tratada como prioridade.

---

Notas sobre o código, as ferramentas locais de teste e como reproduzir cada
número acima estão em [DEVELOPMENT.md](https://github.com/MatheusOliveira-dev/youtube-channel-email-finder/blob/main/DEVELOPMENT.md).
