# Colocar "O Lado Bom" no ar (deploy grátis no Netlify)

Guia passo a passo, pensado para quem não é programador. Tempo: ~15 minutos.
No fim, o site estará no ar com HTTPS e domínio próprio.

> Já está tudo pronto no código: o arquivo `netlify.toml` (na raiz do repositório)
> diz ao Netlify como construir o site. Você só precisa conectar e clicar.

---

## Passo 1 — Criar conta no Netlify
1. Acesse **https://app.netlify.com** e clique em **Sign up**.
2. Escolha **GitHub** para entrar (usa a mesma conta do repositório).

## Passo 2 — Importar o repositório
1. No painel, clique em **Add new site → Import an existing project**.
2. Escolha **Deploy with GitHub** e autorize o Netlify.
3. Selecione o repositório **`jamilmelo86/patrimonio-futuro`**.
4. Em **Branch to deploy**, escolha a branch onde está o site:
   - por enquanto: `claude/positive-news-portal-6h25uf`
   - depois que fizer o merge: `master`
5. Os campos de build vêm **preenchidos automaticamente** pelo `netlify.toml`
   (base `portal/site`, comando `npm run build`, publicação `dist`). Não precisa mexer.
6. Clique em **Deploy**. Em ~1–2 min o site sai no ar num endereço tipo
   `https://algum-nome.netlify.app`.

## Passo 3 — Renomear o site (opcional)
Em **Site configuration → Change site name**, troque para algo como `o-lado-bom`
→ vira `https://o-lado-bom.netlify.app` enquanto o domínio próprio não liga.

## Passo 4 — Ligar o domínio `oladobom.com.br`
> Antes: registre o domínio no **https://registro.br** (~R$40/ano).

1. No Netlify: **Domain management → Add a domain** → digite `oladobom.com.br`.
2. O Netlify mostra como apontar o domínio. Duas opções:
   - **(Mais fácil) Usar Netlify DNS:** o Netlify te dá 4 *nameservers*
     (ex.: `dns1.p0X.nsone.net`). No **registro.br**, em **Alterar servidores DNS**,
     cole esses 4 e salve.
   - **(Alternativa) Manter o DNS do registro.br:** crie os registros:
     - `A` para `@` (oladobom.com.br) → `75.2.60.5`
     - `CNAME` para `www` → `o-lado-bom.netlify.app`
3. A propagação leva de minutos a algumas horas. O **HTTPS (cadeado) é automático**.

## Passo 5 — Ativar o painel de curadoria `/admin`
Para publicar notícias pelo navegador (sem mexer em arquivos):
1. No Netlify: **Site configuration → Identity → Enable Identity**.
2. Ainda em Identity: **Services → Git Gateway → Enable**.
3. Em **Identity → Invite users**, convide o seu e-mail e aceite o convite.
4. Confira que `portal/site/public/admin/config.yml` tem `branch:` igual à branch
   que você está publicando (Passo 2).
5. Acesse `https://oladobom.com.br/admin` e faça login. Pronto: os rascunhos
   aparecem lá para você editar e publicar (é só desmarcar "Rascunho").

## Passo 6 — Aparecer no Google
1. Acesse **https://search.google.com/search-console** e adicione a propriedade
   `https://oladobom.com.br` (verifique via DNS ou HTML).
2. Em **Sitemaps**, envie: `sitemap-index.xml`.
3. Pronto — o Google começa a indexar as notícias.

---

## Como fica o dia a dia depois de no ar
- **Todo push na branch** → o Netlify reconstrói e publica sozinho.
- **O robô diário** (GitHub Actions) gera rascunhos e faz commit → você revê no `/admin`
  e publica. Cada publicação dispara um novo deploy automático.
- **Anúncios:** quando o AdSense aprovar, preencha `adsenseClient` em
  `portal/site/src/consts.ts` e os espaços já existentes passam a exibir anúncios.

## Dúvidas comuns
- **Deu erro no build?** Veja o log em **Deploys → (último) → Deploy log**. Quase sempre
  é versão de Node — o `netlify.toml` já fixa a 20.
- **O `/admin` não loga?** Confirme os passos 5.1 a 5.3 (Identity + Git Gateway + convite).
- **Trocar o domínio/nome depois?** Edite só `portal/site/src/consts.ts` e
  `portal/site/astro.config.mjs` (campo `site`).
