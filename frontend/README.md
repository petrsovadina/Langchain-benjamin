This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Citation System

Czech MedAI pouziva citation rendering system pro transparentni zobrazeni zdroju.

### Komponenty

- **CitedResponse**: Main component pro renderovani odpovedi s citacemi
- **CitationBadge**: Inline citation badge [1][2][3] s hover preview
- **CitationPopup**: Modal s full citation details
- **ReferencesSection**: Seznam vsech citaci na konci odpovedi

### Podporovane zdroje

1. **SUKL** (Statni ustav pro kontrolu leciv)
   - Format: `[N] SUKL - {source_type}. Reg. c.: {registration_number}. {url}`

2. **PubMed** (Biomedicinska literatura)
   - Format: `[N] {authors}. {title}. {journal}. {year}. PMID: {pmid}. {url}`

3. **Guidelines** (CLS JEP, ESC, ERS)
   - Format: `[N] {source}. {guideline_id}. {year}. {url}`

### Usage

```tsx
import { CitedResponse } from "@/components/CitedResponse";

<CitedResponse
  answer="Metformin je lek prvni volby [1]."
  retrievedDocs={[
    {
      page_content: "...",
      metadata: {
        source: "sukl",
        source_type: "drug_search",
        registration_number: "0012345",
      }
    }
  ]}
/>
```

## Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e
```

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
