# KDP Metadata Spec

Objetivo: definir los metadatos mínimos y recomendados para automatizar la carga de libros en Amazon KDP desde el flujo Publisher Lore.

Nota de alcance:
- Este documento cubre metadatos editoriales y de catálogo, no maquetación interior, portada ni contenidos de derechos.
- Los requisitos exactos pueden variar según tipo de libro y país/mercado. El flujo automatizado debe tratar ciertos campos como obligatorios para el pipeline aunque KDP los marque como opcionales en algunos casos.

## 1) Metadata envelope

Campos base que el sistema debe producir para cada título:

- `title` — requerido
- `subtitle` — opcional, pero recomendado si ayuda al descubrimiento
- `series_name` — opcional
- `series_number` — opcional
- `author_name` — requerido
- `contributors` — opcional
- `language` — requerido
- `book_description` — requerido
- `categories` — requerido
- `keywords` — requerido
- `publication_type` — requerido (`ebook` | `paperback` | `hardcover`)
- `publication_date` — opcional
- `edition` — opcional
- `publisher_name` — requerido si aplica al imprint/brand setup
- `imprint` — opcional, pero useful for catalog consistency
- `is_part_of_collection` — opcional
- `territories` — required if rights are not worldwide
- `age_and_grade` — optional, when relevant for children's or educational books
- `content_guidance` — optional, for sensitive / mature content flags
- `isbn` — required for paperback/hardcover if not using KDP-assigned ISBN; optional for ebook
- `asin` — output field after KDP creation, not input
- `interior_format` — required for automation routing (ebook reflowable / fixed layout / print)
- `trim_size` — required for print books
- `page_count` — required for print books
- `cover_type` — required for print books

## 2) Required fields by product type

### 2.1 Ebook

Minimum automation fields:
- title
- author_name
- language
- book_description
- categories
- keywords
- publication_type = `ebook`
- rights / territories
- interior_format = `reflowable` or `fixed_layout`
- content_guidance if applicable

Common print-only fields that do not apply:
- trim_size
- page_count
- cover_type
- print_isbn

### 2.2 Paperback / Hardcover

Minimum automation fields:
- title
- author_name
- language
- book_description
- categories
- keywords
- publication_type = `paperback` or `hardcover`
- trim_size
- page_count
- cover_type
- interior_format
- isbn or KDP-assigned ISBN decision
- territories / rights
- publication_date if scheduled

## 3) Field constraints for automation

### title
- Keep canonical title stable across all exports.
- Avoid stuffing keywords into the title.
- Must match cover text and manuscript metadata.

### subtitle
- Use only when it adds discoverability or clarifies the premise.
- Must be consistent with cover and marketing copy.

### author_name
- Must be the public-facing pen name or brand name used in KDP.
- Keep exact spelling stable across exports.

### language
- Use one ISO-style language value consistently across the pipeline.
- English is the safest default for GoalWorld public releases.

### book_description
- Short sales copy for KDP detail page.
- Should be plain text or lightly formatted.
- Avoid unsupported markup or keyword spam.

### categories
- KDP category selection is critical for discoverability.
- Use a controlled taxonomy in the pipeline.
- Store both the human-readable label and the platform mapping if possible.

### keywords
- Track exactly the keyword phrases submitted to KDP.
- Use a fixed-length array for repeatable automation.
- Avoid duplicates and avoid repeated words across slots when possible.

### publication_type
- Route automation with an explicit type because ebook and print differ in required fields.

### territories
- Must reflect publishing rights.
- If rights are not worldwide, automation must block or require review.

### isbn
- For print: capture whether KDP supplies the ISBN or the project uses an external ISBN.
- For ebook: ISBN is usually not required for KDP publishing.

### trim_size
- Required for print output.
- Must be one of the KDP-supported sizes selected by the production pipeline.

### page_count
- Required for print setup and spine calculations.
- Must match final manuscript after pagination.

### cover_type
- Track paperback / hardcover cover construction separately from interior.

## 4) Automation schema proposal

Recommended JSON shape:

```json
{
  "title": "",
  "subtitle": "",
  "series_name": "",
  "series_number": null,
  "author_name": "",
  "contributors": [],
  "language": "en",
  "publication_type": "ebook",
  "book_description": "",
  "categories": [""],
  "keywords": ["", "", "", "", "", "", "", "", "", ""],
  "rights": {
    "territories": ["worldwide"],
    "ownership": "original"
  },
  "content_guidance": {
    "mature_content": false,
    "notes": ""
  },
  "print": {
    "trim_size": null,
    "page_count": null,
    "cover_type": null,
    "isbn_mode": "kdp_assigned"
  },
  "ebook": {
    "interior_format": "reflowable"
  },
  "publisher_name": "",
  "imprint": "",
  "publication_date": null,
  "edition": "",
  "source_refs": []
}
```

## 5) Validation rules

- Fail if `title`, `author_name`, `language`, `book_description`, `categories`, or `keywords` are missing.
- Fail if `publication_type` is missing or invalid.
- Fail if `publication_type` is print and any of `trim_size`, `page_count`, or `cover_type` is missing.
- Fail if `rights.territories` does not exist.
- Warn if `subtitle` is empty for a discovery-focused title.
- Warn if keyword array contains duplicates or is shorter than the configured slot count.
- Warn if a print title does not specify `isbn_mode`.

## 6) Operational notes for Publisher Lore

- Treat metadata as part of the canonical saga package, alongside manuscript and cover assets.
- Keep the metadata file versioned with the manuscript so KDP exports are reproducible.
- Use English for public-facing KDP copy unless a specific market requires localization.
- Keep a source trail in `source_refs` so changes can be audited later.

## 7) Open items to verify against the live KDP console

- Exact category taxonomy limits and mapping format.
- Current keyword slot count and any market-specific differences.
- Whether any Amazon UI field labels have changed in the current console flow.
- If metadata requirements differ between ebook, paperback, and hardcover in the latest KDP UI.
