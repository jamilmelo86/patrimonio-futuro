// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// IMPORTANTE: mantenha `site` igual ao SITE.url em src/consts.ts.
export default defineConfig({
  site: "https://oladobom.com.br",
  integrations: [sitemap()],
  build: {
    // URLs "limpas": /noticia/slug/ em vez de /noticia/slug.html
    format: "directory",
  },
});
