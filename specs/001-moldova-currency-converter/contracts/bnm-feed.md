# NBM Rate Feed Contract

## Request

- **Authority**: National Bank of Moldova official exchange rates.
- **URL pattern**: `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`
- **Date format**: `DD.MM.YYYY`.
- **Request headers**: Include a descriptive `User-Agent`.
- **Timeout**: 10 seconds per request.
- **Search window**: Request the chosen date first. On a no-rates result, request the preceding
  calendar date, one day at a time, for at most 10 preceding days.

## Successful XML Response

Expected document shape:

```xml
<ValCurs Date="DD.MM.YYYY" name="Official exchange rate">
  <Valute ID="...">
    <NumCode>...</NumCode>
    <CharCode>...</CharCode>
    <Nominal>...</Nominal>
    <Name>...</Name>
    <Value>...</Value>
  </Valute>
</ValCurs>
```

`Value` is the MDL amount for `Nominal` units of the foreign currency. A quote with
`Nominal=100` and `Value=11.5217` therefore represents `0.115217` MDL per one unit. Use the
`ValCurs` `Date` as the actual rate date shown to the user.

Parse decimal text directly as `Decimal`. Skip an individual `Valute` entry if required fields
are absent or invalid; continue using other valid entries. Reject an unexpected root, malformed
XML, or an HTML document as a source error. A valid `ValCurs` with no usable rate entries is a
no-rates result, not a zero-valued rate set.

## Response Classification

| Response | Service meaning | Action |
|---|---|---|
| Valid XML with usable `Valute` entries | Rates available | Return and cache the complete usable set. |
| Valid, empty `ValCurs` | No rates for requested date | Search previous dates, within the 10-day limit. |
| HTTP 404 with an empty body for a validated date | No date document available | Treat as a date miss and search previous dates. |
| Non-empty HTML, malformed XML, unexpected XML root, or other HTTP/network error | Source failure | Do not cache; offer a usable saved set if present, otherwise show a short Russian error. |
| XML containing some broken entries and at least one usable entry | Partial valid data | Skip broken entries and use/cache the usable set. |
| XML containing no usable entries | Unusable source data | Do not cache; handle as source failure and offer saved rates if present. |

No-rates search ends after the requested date plus at most 10 preceding calendar dates. If no
usable set is found, stop requests, offer saved rates if available, or show an error.

## Test Fixtures

Keep local fixtures for a usable response, an empty `ValCurs`, partially broken entries, malformed
XML, an HTML error page, and the empty-body 404 case. Unit tests use fake responses and never
contact the live service.
