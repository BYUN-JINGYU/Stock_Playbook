import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const candle = z.object({
  o: z.number(),
  h: z.number(),
  l: z.number(),
  c: z.number(),
  v: z.number().optional(),
});

const chart = z.object({
  title: z.string(),
  description: z.string().optional(),
  kind: z.enum(['candle', 'line']).default('candle'),
  candles: z.array(candle).min(5),
  hlines: z
    .array(z.object({ price: z.number(), label: z.string().optional() }))
    .optional(),
  lines: z
    .array(
      z.object({
        points: z.array(z.object({ i: z.number(), price: z.number() })).min(2),
        label: z.string().optional(),
      }),
    )
    .optional(),
  zones: z
    .array(
      z.object({ from: z.number(), to: z.number(), label: z.string().optional() }),
    )
    .optional(),
  markers: z
    .array(
      z.object({
        i: z.number(),
        type: z.enum(['buy', 'sell', 'note']),
        label: z.string().optional(),
      }),
    )
    .optional(),
  sma: z
    .array(z.object({ period: z.number().int().min(2), label: z.string().optional() }))
    .optional(),
});

export const CATEGORIES = [
  '차트 패턴',
  '보조지표',
  '추세·모멘텀',
  '가치·성장 투자',
  '퀀트·시스템',
  '수급·이벤트',
  '거시·경제지표',
  '리스크·심리',
] as const;

const techniques = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/techniques' }),
  schema: z.object({
    title: z.string(),
    category: z.enum(CATEGORIES),
    tags: z.array(z.string()).default([]),
    difficulty: z.number().int().min(1).max(5),
    reliability: z.number().int().min(1).max(5),
    markets: z.array(z.enum(['KR', 'US'])).min(1),
    summary: z.string(),
    charts: z.array(chart).default([]),
    sources: z.array(z.string()).default([]),
    updated: z.coerce.date(),
    draft: z.boolean().default(false),
    // 경제지표 글 전용: 발표 정보 박스
    indicator: z
      .object({
        publisher: z.string().optional(), // 발표 기관
        frequency: z.string().optional(), // 발표 주기
        where: z.string().optional(), // 확인처
      })
      .optional(),
    // "이럴 때 주목" 체크리스트
    watch_when: z.array(z.string()).default([]),
  }),
});

export const collections = { techniques };
