# O Lado Bom — Portal de Notícias Positivas

Um portal de **boas notícias** do Brasil e do mundo: um robô varre fontes confiáveis todos os
dias, escreve **resumos originais em português** (nunca copia a matéria) e deixa **rascunhos** para
você revisar e publicar. Sempre com **link para a fonte original**.

> **Nome:** O Lado Bom · **Domínio:** `oladobom.com.br` (disponível para registro).
> Para trocar o nome/domínio, edite num só lugar: `site/src/consts.ts`
> (e `site/astro.config.mjs` → campo `site`).

## Como funciona (visão rápida)

```
Fontes (RSS + APIs)  ─►  Pipeline Python (diário)  ─►  Rascunhos .md (draft:true)
                                                              │
                                             Você revisa/publica no painel /admin
                                                              │
                                                     Site Astro (público) ─► anúncios / newsletter
```

- **`site/`** — o site público (Astro). Rápido, ótimo para o Google, pronto para anúncios.
- **`pipeline/`** — a coleta + curadoria por IA (Python). Só gera rascunhos, nunca publica sozinho.
- **`/admin`** — painel de curadoria (Decap CMS) onde você edita e publica com um clique.

---

## 1) Rodar o site localmente

Pré-requisito: Node 18+.

```bash
cd site
npm install
npm run dev        # abre em http://localhost:4321
npm run build      # gera o site em site/dist/
```

As notícias são arquivos Markdown em `site/src/content/posts/`. Um arquivo com `draft: true`
**não aparece** no site.

## 2) Rodar o pipeline (gerar rascunhos)

Pré-requisito: Python 3.11+.

```bash
cd pipeline
pip install -r requirements.txt
cp .env.example .env          # preencha as chaves que tiver (todas opcionais)
python gerar_rascunhos.py
```

- **Com `ANTHROPIC_API_KEY`**: a IA (Claude Haiku) escreve título + resumo originais e escolhe a
  categoria. Custo: centavos por notícia.
- **Sem chave**: gera "esqueletos" (sem texto da fonte) para você escrever à mão — assim nunca
  copiamos conteúdo de terceiros.
- Fontes extras opcionais: `GUARDIAN_API_KEY`, `NEWSDATA_API_KEY`.

Os rascunhos surgem em `site/src/content/posts/` com `draft: true`.

## 3) Revisar e publicar

**Opção fácil (painel web):** acesse `/admin` no site publicado. O Decap CMS mostra os rascunhos;
edite o texto, confira a fonte e **desmarque "Rascunho"** para publicar. Ele faz o commit e o site
se reconstrói sozinho. Configure o backend em `site/public/admin/config.yml` (veja comentários lá).

**Opção manual:** edite o arquivo `.md`, ajuste o texto e mude `draft: true` → `draft: false`.

> ⚖️ **Regra de ouro:** o texto publicado é sempre **resumo original**, com **crédito e link** para
> a fonte. Nunca cole trechos da matéria original.

## 4) Automação diária (grátis)

Dois robôs cuidam do conteúdo via GitHub Actions (na raiz, `.github/workflows/`):

- **Coletor** (`ingestao.yml`) — roda **3x/dia** (06h/12h/18h BRT). Busca, escreve e **publica
  automaticamente** as boas notícias, com **critério rigoroso** da IA (só publica com confiança
  alta; veta opinião, autoajuda, propaganda, fofoca, etc.).
- **Revisor** (`revisao.yml`) — roda **a cada 2 dias**. Relê as publicações, corrige português e
  qualidade e **despublica** o que estiver fraco ou duvidoso (registro em `pipeline/_estado/`).

Para voltar ao modo com aprovação manual, defina `PUBLICAR_AUTOMATICO=0`. Para ativar os robôs:

1. Em **Settings → Secrets and variables → Actions**, adicione `ANTHROPIC_API_KEY`
   (e, se quiser, `GUARDIAN_API_KEY` / `NEWSDATA_API_KEY`).
2. O cron só roda a partir da **branch padrão** do repositório. Use "Run workflow" para testar.

## 5) Cards para redes sociais

```bash
cd pipeline
python cards_sociais.py <slug>     # ex.: exemplo-resgate-animais
python cards_sociais.py --todos    # gera de todos os posts publicados
```

As imagens 1080×1080 saem em `pipeline/_cards/`. Publique no Instagram com "link na bio" → site.

## 6) Publicar na internet (deploy)

📘 **Guia clicável completo:** veja [`DEPLOY.md`](./DEPLOY.md). O `netlify.toml` na raiz
do repositório já configura tudo — é só conectar o repo no Netlify.

Recomendado: **Netlify** ou **Vercel** (plano gratuito).

- **Base directory:** `portal/site`
- **Build command:** `npm run build`
- **Publish directory:** `portal/site/dist`

Depois: aponte seu domínio, ative HTTPS e envie o `sitemap-index.xml` ao
**Google Search Console**. Se usar o painel `/admin` com Netlify, ative **Identity** + **Git Gateway**.

---

## Monetização (em camadas)

1. **Google AdSense** — os espaços de anúncio já existem no site (`AdSlot.astro`). Ao ser aprovado,
   preencha `adsenseClient` em `consts.ts`. Requer ~15–20 posts originais + páginas Sobre/Contato/
   Privacidade (já prontas).
2. **Afiliados** — links contextuais (Amazon Associates BR etc.), sempre com aviso.
3. **Newsletter** — a caixa de captura já existe (`NewsletterSignup.astro`); ligue no seu provedor
   (MailerLite/Beehiiv). Vira canal próprio e espaço para patrocínio.
4. **Tração** — patrocínio na newsletter, "apoie o projeto" (apoia.se/Catarse), conteúdo patrocinado.

## Ajustes rápidos

| O quê | Onde |
|-------|------|
| Nome, slogan, domínio, e-mail, redes | `site/src/consts.ts` |
| Domínio no build (sitemap/RSS) | `site/astro.config.mjs` (`site:`) |
| Categorias | `site/src/consts.ts` (`CATEGORIAS`) |
| Fontes RSS/APIs | `pipeline/fontes.py` |
| Sensibilidade do filtro | `pipeline/filtro.py` (léxicos) |
| Estilo do resumo por IA | `pipeline/resumir.py` (`PROMPT_SISTEMA`) |
| Cor/identidade | `site/src/styles/global.css` |

## Aspectos legais
- **Sem cópia:** somente resumo original + link para a fonte.
- **Imagens:** use bancos livres (Unsplash/Pexels) ou os cards gerados; só use imagem da fonte se a
  licença permitir, com crédito.
- **LGPD:** newsletter com consentimento; Política de Privacidade já incluída.
