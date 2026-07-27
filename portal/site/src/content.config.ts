import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { CATEGORIA_SLUGS } from "./consts";

// Coleção de notícias: 1 arquivo Markdown por notícia em src/content/posts/.
// O corpo do arquivo é o RESUMO ORIGINAL em português (nunca o texto copiado da fonte).
const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: z.object({
    // Título original que escrevemos (não precisa ser igual ao da fonte).
    titulo: z.string(),
    // Chamada curta exibida nos cards e nas meta tags.
    resumo: z.string(),
    // Categoria — precisa ser um dos slugs em src/consts.ts.
    categoria: z.enum(CATEGORIA_SLUGS as [string, ...string[]]),
    // Data de publicação.
    data: z.coerce.date(),
    // Crédito obrigatório: nome e link da fonte original.
    fonteNome: z.string(),
    fonteUrl: z.string().url(),
    // Imagem de capa (opcional): caminho em /public ou URL de licença livre.
    imagem: z.string().optional(),
    creditoImagem: z.string().optional(),
    // Palavras-chave para SEO / navegação.
    tags: z.array(z.string()).default([]),
    // Rascunho: quando true, NÃO aparece no site. O pipeline cria com draft:true.
    draft: z.boolean().default(false),
    // Destaque na home.
    destaque: z.boolean().default(false),
  }),
});

export const collections = { posts };
