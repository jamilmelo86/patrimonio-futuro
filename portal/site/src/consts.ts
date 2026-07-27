// Configuração central do site. Altere aqui o nome, domínio e categorias.

export const SITE = {
  /** Nome da marca (placeholder — troque quando definir o nome final). */
  name: "Lado Bom",
  /** Slogan curto exibido no cabeçalho e nas meta tags. */
  tagline: "Só as boas notícias do Brasil e do mundo",
  /** Descrição para SEO / redes sociais. */
  description:
    "Um portal de notícias positivas: histórias de ciência, solidariedade, meio ambiente, saúde e superação — sempre com a fonte original.",
  /** URL final do site em produção (usada em sitemap, RSS e Open Graph). */
  url: "https://ladobom.com.br",
  /** Idioma padrão. */
  lang: "pt-BR",
  /** E-mail de contato exibido nas páginas institucionais. */
  email: "contato@ladobom.com.br",
  /** Handles de redes sociais (deixe vazio para ocultar). */
  social: {
    instagram: "",
    tiktok: "",
    youtube: "",
  },
  /** ID do AdSense (ca-pub-XXXX). Vazio = anúncios desligados. */
  adsenseClient: "",
} as const;

export type Categoria = {
  slug: string;
  nome: string;
  emoji: string;
  descricao: string;
};

/** Categorias editoriais do portal. O `slug` vira a URL /categoria/<slug>. */
export const CATEGORIAS: Categoria[] = [
  { slug: "ciencia", nome: "Ciência", emoji: "🔬", descricao: "Descobertas e avanços que melhoram a vida." },
  { slug: "solidariedade", nome: "Solidariedade", emoji: "🤝", descricao: "Gente ajudando gente pelo Brasil e pelo mundo." },
  { slug: "meio-ambiente", nome: "Meio Ambiente", emoji: "🌱", descricao: "Natureza se recuperando e boas práticas verdes." },
  { slug: "saude", nome: "Saúde", emoji: "❤️", descricao: "Tratamentos, curas e conquistas da medicina." },
  { slug: "animais", nome: "Animais", emoji: "🐾", descricao: "Resgates, proteção e histórias fofas." },
  { slug: "superacao", nome: "Superação", emoji: "⭐", descricao: "Pessoas que venceram desafios e inspiram." },
  { slug: "tecnologia", nome: "Tecnologia do Bem", emoji: "💡", descricao: "Inovação usada para o bem comum." },
  { slug: "mundo", nome: "Mundo", emoji: "🌍", descricao: "Boas notícias que vêm de fora, traduzidas." },
];

export const CATEGORIA_SLUGS = CATEGORIAS.map((c) => c.slug);

export function categoriaPorSlug(slug: string): Categoria | undefined {
  return CATEGORIAS.find((c) => c.slug === slug);
}
