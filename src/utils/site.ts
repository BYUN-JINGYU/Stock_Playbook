export const SITE_NAME = '주식 기법 플레이북';
export const SITE_DESC =
  '한국·미국 주식시장의 매매 기법을 한곳에 모아 정리한 학습 라이브러리. 원리, 진입·청산 규칙, 차트 예시, 흔한 실수까지.';

export interface CategoryMeta {
  name: string;
  slug: string;
  icon: string;
  desc: string;
}

export const CATEGORY_META: CategoryMeta[] = [
  { name: '차트 패턴', slug: 'chart-patterns', icon: '📈', desc: '지지·저항, 추세선, 반전·지속 패턴 등 가격 움직임 자체를 읽는 기법' },
  { name: '보조지표', slug: 'indicators', icon: '🧮', desc: 'RSI, MACD, 볼린저밴드 등 지표 기반 매매 신호' },
  { name: '추세·모멘텀', slug: 'momentum', icon: '🚀', desc: '돌파, 눌림목, 신고가 등 추세와 모멘텀을 활용하는 기법' },
  { name: '가치·성장 투자', slug: 'value-growth', icon: '💎', desc: '재무제표와 기업 가치에 기반한 중장기 투자 전략' },
  { name: '퀀트·시스템', slug: 'quant', icon: '⚙️', desc: '규칙 기반·데이터 기반의 체계적 매매 전략' },
  { name: '수급·이벤트', slug: 'flow-events', icon: '📰', desc: '수급 주체, 공모주, 실적 발표 등 이벤트 중심 매매' },
  { name: '거시·경제지표', slug: 'macro-indicators', icon: '🌐', desc: 'CDS 프리미엄, 금리, 물가, VIX 등 시장 전체를 움직이는 지표를 언제·어떻게 봐야 하는지' },
  { name: '리스크·심리', slug: 'risk-psychology', icon: '🛡️', desc: '손절, 자금 관리, 매매 심리 등 살아남기 위한 원칙' },
];

export function categoryBySlug(slug: string): CategoryMeta | undefined {
  return CATEGORY_META.find((c) => c.slug === slug);
}

export function categoryByName(name: string): CategoryMeta | undefined {
  return CATEGORY_META.find((c) => c.name === name);
}

export function difficultyLabel(n: number): string {
  if (n <= 2) return '초급';
  if (n === 3) return '중급';
  return '고급';
}

export const RELIABILITY_LABELS: Record<number, string> = {
  1: '참고용',
  2: '보조 신호',
  3: '조건부 유효',
  4: '널리 검증됨',
  5: '장기 검증됨',
};

export function marketLabel(m: string): string {
  return m === 'KR' ? '한국' : '미국';
}

/** base 경로를 붙인 내부 링크 생성 (GitHub Pages 하위 경로 대응) */
export function withBase(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return base + path;
}
