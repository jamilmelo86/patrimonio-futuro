import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { SITE } from "../consts";

export async function GET(context) {
  const posts = (await getCollection("posts", ({ data }) => !data.draft)).sort(
    (a, b) => b.data.data.valueOf() - a.data.data.valueOf(),
  );

  return rss({
    title: SITE.name,
    description: SITE.description,
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.titulo,
      description: post.data.resumo,
      pubDate: post.data.data,
      link: `/noticia/${post.id}/`,
      categories: [post.data.categoria],
    })),
    customData: `<language>pt-br</language>`,
  });
}
