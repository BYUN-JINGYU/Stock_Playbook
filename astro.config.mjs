import { defineConfig } from 'astro/config';

// GitHub Pages 배포 시: SITE_URL=https://<user>.github.io BASE_PATH=/stock-playbook
const site = process.env.SITE_URL || 'http://localhost:4321';
const base = process.env.BASE_PATH || '/';

export default defineConfig({
  site,
  base,
  trailingSlash: 'ignore',
});
