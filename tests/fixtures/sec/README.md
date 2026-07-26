# Synthetic SEC fixtures

Every file here is **hand-written and synthetic**. None was retrieved from the SEC,
and no fixture is derived from a real filing body. They exist so Stage M2.1 can test
header parsing shapes, index payloads, and failure handling entirely offline.

| File | Purpose |
|---|---|
| `header_modern.txt` | Complete-submission header with acceptance datetime, filed-as-of date, and one registrant |
| `header_after_cutoff.txt` | Acceptance after the cutoff with a later official filing date |
| `header_multi_registrant.txt` | Two registrants on one accession |
| `header_missing_acceptance.txt` | Required acceptance value absent |
| `submissions_min.json` | Minimal Submissions-API shape used for provisional discovery |
| `index_min.json` | Minimal accession index listing documents |
| `block_page.html` | SEC automated-access block page signature |
| `truncated.json` | JSON body cut off mid-document |
| `not_a_zip.bin` | Payload that fails the ZIP signature check |

The CIKs and accession numbers are fabricated. `0000000000` style values and
`example.invalid` hosts are used so no fixture can be mistaken for real evidence.
