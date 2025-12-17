# Scholar Result Fetcher

A minimal command-line helper that prompts for a keyword, builds a Google
Scholar query restricted to 2025, and extracts the reported result count (e.g.,
`About 12,400 results`). All fetching now runs through Selenium to mimic a real
browser and avoid the 403 errors typical of direct scripted HTTPS requests. The
Chrome options follow the [Bright Data Google Scholar tutorial](https://www.bright.cn/blog/web-data/how-to-scrape-google-scholar)
recommendations (custom UA, larger window, automation flags disabled) to reduce
403 responses.

## Setup

Selenium is required. Install the dependency:

```bash
pip install -r requirements.txt
```

> If your environment sits behind a restrictive proxy, `pip` may be blocked
> from downloading Selenium with a 403 error. In that case you can either
> supply an offline wheel for Selenium or skip live fetching and use the saved
> HTML parsing path shown below to verify the result extractor still works.

Running requires a Chrome-compatible driver on your PATH (`chromedriver`,
`msedgedriver`, or `google-chrome` managed by the Selenium Manager that ships
with recent Selenium versions).

If you only need to exercise the parser without live network access, you can
provide a saved HTML file instead of launching the browser (a sample is
included at `sample_data/scholar_sample.html`).

## Usage

Run the script and provide a keyword when prompted:

```bash
python fetch_results.py
Enter keyword: language model
Result count: 12400
```

To query without an interactive prompt:

```bash
python fetch_results.py --keyword "video generation"
```

To test the parser offline using a saved HTML response:

```bash
python fetch_results.py --html-file sample_data/scholar_sample.html
```

You can also forward extra Chrome options to Selenium if your environment
requires them (for example, `--proxy-server` or `--headless`/`--headful`):

```bash
python fetch_results.py --keyword "video generation" --chrome-option "--headful"
```

If the script cannot find the result count, it will exit with an error message.

## Why you might see 403/connection errors

Google Scholar actively rate-limits and detects automated scraping. Even with
the Bright Data–inspired Selenium configuration, you may occasionally see a 403
or need to complete a CAPTCHA. Typical causes include:

* Requests coming from cloud/hosting IP ranges or shared proxies that Scholar
  distrusts.
* Too many rapid requests from the same IP, which triggers bot defenses.
* Intercepting proxies (corporate or academic) that block or rewrite Scholar
  traffic.

This script does not bypass Scholar's protections; the Selenium option only
mimics a normal browser. To improve reliability while respecting Scholar's
terms, try the following:

* Run the script on a residential or otherwise less-blocked network.
* Avoid rapid repetition; wait between requests and retry later if blocked.
* If your network uses a proxy, ensure it allows outbound HTTPS to
  `scholar.google.com`.
* As a last resort, open the generated URL in a real browser session (which
  may prompt for a CAPTCHA) and manually copy the result count.
