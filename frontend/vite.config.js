import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const siteOrigin = (env.VITE_SITE_ORIGIN || '').replace(/\/$/, '')

  return {
    plugins: [
      vue(),
      tailwindcss(),
      {
        name: 'seo-index-and-static',
        transformIndexHtml(html) {
          if (siteOrigin) {
            return html
              .replaceAll('__SITE_ORIGIN__', siteOrigin)
              .replace(/<!--SEO:REQUIRES_ORIGIN_START-->\s*/g, '')
              .replace(/\s*<!--SEO:REQUIRES_ORIGIN_END-->/g, '')
          }
          return html.replace(
            /<!--SEO:REQUIRES_ORIGIN_START-->[\s\S]*?<!--SEO:REQUIRES_ORIGIN_END-->/g,
            '',
          )
        },
        closeBundle() {
          if (!siteOrigin) return
          const outDir = path.resolve(__dirname, 'dist')
          if (!fs.existsSync(outDir)) return
          const robots = `User-agent: *\nAllow: /\nSitemap: ${siteOrigin}/sitemap.xml\n\n# AI / GEO: 站点摘要与能力说明（llms.txt 约定路径）\n# ${siteOrigin}/llms.txt\n`
          const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>${siteOrigin}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n  <url>\n    <loc>${siteOrigin}/llms.txt</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.3</priority>\n  </url>\n</urlset>\n`
          fs.writeFileSync(path.join(outDir, 'robots.txt'), robots, 'utf8')
          fs.writeFileSync(path.join(outDir, 'sitemap.xml'), sitemap, 'utf8')
        },
      },
    ],
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
