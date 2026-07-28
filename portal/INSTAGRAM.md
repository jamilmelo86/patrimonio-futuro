# Kit de Instagram — O Lado Bom ☀️

Tudo o que você precisa para lançar o @oladobom e transformar as notícias do site
em posts. Os cards são gerados automaticamente a partir das notícias publicadas.

## 1. Perfil

| Campo | Valor |
|-------|-------|
| Usuário | **@oladobom** (confirme a disponibilidade ao criar) |
| Nome | O Lado Bom ☀️ |
| Categoria | Meio de comunicação / Publicação (perfil profissional) |
| Foto de perfil | O sol da marca (use `portal/site/public/favicon.svg` em fundo claro) |
| Link na bio | https://oladobom.com.br |

Dica: crie como **conta profissional** (grátis) para ter estatísticas e agendamento.

## 2. Bio (escolha uma)

**Opção A — direta**
```
☀️ Só as boas notícias do Brasil e do mundo
📰 Histórias reais que renovam a fé na humanidade
👇 Leia a matéria completa
```

**Opção B — com editorias**
```
O lado bom das notícias existe — a gente reúne aqui ☀️
🔬 Ciência · 🤝 Solidariedade · 🌱 Natureza · ⭐ Superação
🔗 oladobom.com.br
```

**Destaques (Stories fixados):** Sobre · Ciência · Animais · Superação · Solidariedade

## 3. Cadência e horários (Brasil)

- **Frequência:** comece com **4–5 posts/semana**; suba para 1/dia quando pegar ritmo.
- **Melhores horários:** **12h–13h** e **19h–21h** em dias de semana; domingo à noite.
- **Stories:** todo dia que postar, replique o card no story com enquete/figurinha.

## 4. Rodízio semanal sugerido

| Dia | Editoria | Por quê |
|-----|----------|---------|
| Segunda | Superação | motiva o começo da semana |
| Terça | Ciência / Saúde | conteúdo de credibilidade |
| Quarta | Animais | alto engajamento |
| Quinta | Solidariedade | conexão emocional |
| Sexta | Meio Ambiente | esperança pro fim de semana |
| Sábado | Mundo | boa notícia leve |
| Domingo | **Carrossel** "Resumo da semana" (3–5 notícias) | recap |

## 5. Modelo de legenda

```
[emoji] [frase de abertura que prende]

[2 a 3 frases resumindo a boa notícia, em tom positivo]

📰 Matéria completa no link da bio → oladobom.com.br
Fonte: [veículo]

.
.
[bloco de hashtags]
```

## 6. Hashtags (copie e cole; use 8–15 por post)

**Fixas:** `#boasnoticias #noticiaboa #boanoticiadodia #otimismo #esperanca #brasil #oladobom #façaobem`

**Por editoria:**
- Superação: `#superacao #inspiracao #historiareal #foco #determinacao`
- Ciência/Saúde: `#ciencia #saude #sus #descoberta #inovacao`
- Animais: `#animais #resgate #conservacao #natureza #petsdobem`
- Meio Ambiente: `#meioambiente #sustentabilidade #natureza #clima`
- Solidariedade: `#solidariedade #voluntariado #doacao #gentequefazobem`
- Mundo: `#mundo #boasnoticiasdomundo #humanidade`

## 7. Como transformar uma notícia em post (fluxo)

1. Escolha uma notícia **publicada** no site.
2. Gere o card:
   ```bash
   cd portal/pipeline
   python cards_sociais.py <slug-da-noticia>      # sai em pipeline/_cards/
   python cards_sociais.py --todos                # gera de todas de uma vez
   ```
3. Poste o card no feed com a legenda (modelo acima) + hashtags.
4. Sempre direcione: **"link na bio"** → o tráfego vai para o site (onde ficam os anúncios).
5. Replique no Story com uma enquete ("Você sabia disso?") para engajar.

## 8. Dicas de crescimento

- Responda os comentários nos **primeiros 60 minutos** (o algoritmo premia).
- Faça **Reels** de vez em quando (vídeo curto narrando a manchete) — o alcance é bem maior.
- **Consistência > perfeição**: melhor 4 posts simples por semana do que 1 elaborado por mês.
- Peça para amigos compartilharem nos Stories no lançamento.

## 9. Próximas plataformas

Depois que o Instagram engrenar, o mesmo card serve para **TikTok** e **Kwai** (como imagem
ou fundo de Reel) e o texto vira thread no **Threads/X**. Um conteúdo, vários canais.
