import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// 커스텀 도메인 배포: SITE_URL=https://jusikgongbu.org BASE_PATH=/
const site = process.env.SITE_URL || 'http://localhost:4321';
const base = process.env.BASE_PATH || '/';

export default defineConfig({
  site,
  base,
  trailingSlash: 'ignore',
  integrations: [
    sitemap({
      // /my 는 개인 학습 데이터 페이지 — noindex이므로 sitemap에서도 뺀다
      filter: (page) => !/\/my\/?$/.test(page),
      // 기법 상세 페이지가 핵심 콘텐츠이므로 우선순위를 높인다.
      serialize(item) {
        if (item.url.includes('/techniques/')) {
          item.priority = 0.9;
          item.changefreq = 'monthly';
        } else if (item.url.includes('/category/')) {
          item.priority = 0.7;
          item.changefreq = 'weekly';
        } else if (/\/(privacy|my)\/?$/.test(item.url)) {
          item.priority = 0.2;
        } else {
          item.priority = 1.0;
          item.changefreq = 'weekly';
        }
        return item;
      },
    }),
  ],
});
