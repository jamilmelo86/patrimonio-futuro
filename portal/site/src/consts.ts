// Configuração central do site. Altere aqui o nome, domínio e categorias.

export const SITE = {
  /** Nome da marca. */
  name: "O Lado Bom",
  /** Slogan curto exibido no cabeçalho e nas meta tags. */
  tagline: "Só as boas notícias do Brasil e do mundo",
  /** Descrição para SEO / redes sociais. */
  description:
    "Um portal de notícias positivas: histórias de ciência, solidariedade, meio ambiente, saúde e superação — sempre com a fonte original.",
  /** URL final do site em produção (usada em sitemap, RSS e Open Graph). */
  url: "https://oladobom.com.br",
  /** Idioma padrão. */
  lang: "pt-BR",
  /** E-mail de contato exibido nas páginas institucionais. */
  email: "contato@oladobom.com.br",
  /** Handles de redes sociais (deixe vazio para ocultar). */
  social: {
    instagram: "",
    tiktok: "",
    youtube: "",
  },
  /** ID do AdSense (ca-pub-XXXX). Vazio = anúncios desligados. */
  adsenseClient: "ca-pub-1125789866460980",
  /**
   * Token do Cloudflare Web Analytics (grátis, sem cookies). Vazio = desligado.
   * Como obter: cloudflare.com → conta grátis → "Web Analytics" → "Add a site"
   * → oladobom.com.br. Copie o valor de `data-cf-beacon` "token" (32 hex) e cole
   * aqui. Nada mais precisa mudar — o site já injeta o script quando há token.
   */
  cfAnalyticsToken: "5bea0471692748fba5036aa58f7bbe40",
} as const;

export type Categoria = {
  slug: string;
  nome: string;
  emoji: string;
  descricao: string;
  /** Cor suave de fundo usada no placeholder de imagem. */
  cor: string;
};

/** Categorias editoriais do portal. O `slug` vira a URL /categoria/<slug>. */
export const CATEGORIAS: Categoria[] = [
  { slug: "ciencia", nome: "Ciência", emoji: "🔬", descricao: "Descobertas e avanços que melhoram a vida.", cor: "#e6effb" },
  { slug: "solidariedade", nome: "Solidariedade", emoji: "🤝", descricao: "Gente ajudando gente pelo Brasil e pelo mundo.", cor: "#fdeede" },
  { slug: "meio-ambiente", nome: "Meio Ambiente", emoji: "🌱", descricao: "Natureza se recuperando e boas práticas verdes.", cor: "#e6f5ea" },
  { slug: "saude", nome: "Saúde", emoji: "❤️", descricao: "Tratamentos, curas e conquistas da medicina.", cor: "#fdeaea" },
  { slug: "animais", nome: "Animais", emoji: "🐾", descricao: "Resgates, proteção e histórias fofas.", cor: "#fbf0dd" },
  { slug: "superacao", nome: "Superação", emoji: "⭐", descricao: "Pessoas que venceram desafios e inspiram.", cor: "#efeafb" },
  { slug: "tecnologia", nome: "Tecnologia do Bem", emoji: "💡", descricao: "Inovação usada para o bem comum.", cor: "#e2f4f2" },
  { slug: "mundo", nome: "Mundo", emoji: "🌍", descricao: "Boas notícias que vêm de fora, traduzidas.", cor: "#e8f0fb" },
];

export const CATEGORIA_SLUGS = CATEGORIAS.map((c) => c.slug);

export function categoriaPorSlug(slug: string): Categoria | undefined {
  return CATEGORIAS.find((c) => c.slug === slug);
}
