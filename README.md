# 주식 기법 플레이북

한국·미국 주식시장의 매매 기법을 모아 정리한 학습 웹사이트. Astro 정적 사이트로,
콘텐츠는 전부 마크다운 파일로 관리된다.

## 개발

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # dist/ 에 정적 빌드
```

## 콘텐츠 추가/수정

`src/content/techniques/`에 `.md` 파일을 추가하면 자동으로 사이트에 반영된다.

```markdown
---
title: 기법 이름
category: 차트 패턴   # content.config.ts의 CATEGORIES 중 하나
tags: [태그1, 태그2]
difficulty: 2         # 1~5 (1-2 초급, 3 중급, 4-5 고급)
reliability: 4        # 1~5 (얼마나 오래/널리 검증되었는지)
markets: [KR, US]
summary: 카드와 상단에 표시되는 한두 문장 요약.
updated: 2026-07-20
charts:
  - title: 차트 제목
    description: 설명
    candles: [{ o: 100, h: 104, l: 99, c: 103, v: 1200 }, ...]
    hlines: [{ price: 110, label: 저항선 }]
    sma: [{ period: 20 }]
    markers: [{ i: 25, type: buy, label: 매수 }]
---

## 개요
본문은 일반 마크다운.
```

- `draft: true`를 넣으면 사이트에 노출되지 않는다 (검토 전 초안).
- 초안은 `drafts/` 폴더에 두고, 검토 후 `src/content/techniques/`로 옮긴다.

## 배포

`main`에 push하면 GitHub Actions(`.github/workflows/deploy.yml`)가 GitHub Pages로
자동 배포한다. 저장소 Settings → Pages → Source를 **GitHub Actions**로 설정할 것.

## 자동 수집 (24시간 주기)

매일 스케줄된 Claude 에이전트가 새 기법을 조사해 초안 브랜치 + PR을 생성한다.
PR을 검토하고 머지하면 자동으로 배포된다.
