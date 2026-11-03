# Phase 824 — Public EduAutomate Provider Discovery

## Research date
2026-11-03

## Identity finding
Public search surfaced an EduAutomate-branded school ERP published by Weblink.IN. Its official product site is https://www.weblink.in/school-erp-software/ and its linked login is https://eduautomate.weblink.in/. The page identifies Weblink.in contact details and describes admin, teacher, parent and student roles, with admission, attendance, classroom, HR, academics, examinations, results, fee, payroll, student, transport, timetable, library, gate-pass and complaint-tracking modules.

Important: this public vendor product is not yet confirmed to be the same EduAutomate product/system intended by the KMH OIA project owner. Do not assume the vendor, tenancy, account ownership, or API relationship from a matching product name.

## API documentation finding
Searches located no official public API/OpenAPI reference, authentication guide, webhook signature specification, or sandbox API endpoint for the Weblink.IN EduAutomate product. The public product pages and login page are not sufficient evidence to implement a provider-specific connector.

Search results also surfaced `edumate.net` API documentation and `eduMe` webhook documentation. These are distinct names/domains and must not be treated as EduAutomate API documentation.

## Evidence sources
- Official EduAutomate product overview: https://www.weblink.in/school-erp-software/
- Official EduAutomate login linked from product page: https://eduautomate.weblink.in/
- Weblink.IN about page: https://www.weblink.in/school-erp-software/about-eduautomate
- Non-matching Edumate API docs (do not use as EduAutomate contract): https://integrations.edumate.net/apidoc/
- Non-matching eduMe webhook docs (do not use as EduAutomate contract): https://developers.edume.com/guide/webhooks/webhook-security

## Next required owner confirmation
Before any provider-specific adapter is implemented, the project owner must confirm whether the target is (A) the Weblink.IN EduAutomate ERP above, or (B) the separate KMH/EduAutomate application referenced in the KMH OIA project. If A, obtain API access and official documentation directly from Weblink.IN through an authorized account. If B, provide the actual backend repository/API owner and OpenAPI schema.

## Security and release boundary
No login, account, endpoint probing, credentials, student data, or external requests were used. No integration was made. The existing provider-neutral contract remains a proposal only. Production remains HOLD.