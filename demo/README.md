# RedAgent results explorer

A buildless, browser-only view of the repository's published experiments.
The interface is in English for portfolio and recruitment use.

## Explore

- Filter recorded attack outcomes by experiment and challenge.
- Inspect capture counts, rates and 95% Wilson intervals per attacker model.
- Switch between historical judge replay cohorts and inspect confusion counts,
  precision, recall and F1.
- Download the same aggregate data used by the page.

This is a results explorer, not a live attack interface. It makes no model
requests, accepts no credentials and needs no database or subscription.
Judge replay cohorts are separate from the selected attack experiments.

## Run locally

From the repository root:

```bash
python scripts/build_demo.py --check
python -m http.server 8080 --directory demo
```

Open `http://localhost:8080`. No third-party Python packages, Node installation
or frontend build step are needed to serve the page. The committed `data.js`
also lets the page run directly from `demo/index.html` in a browser.

## Update the data

```bash
python scripts/build_demo.py
python scripts/build_demo.py --check
python -m unittest discover -s tests -p test_demo_data.py -v
```

Commit `demo/data.js` alongside any intentional changes to the source logs.
The exporter explicitly selects aggregate fields and omits prompts, responses
and captured evidence. Its tests reject duplicate cells and invalid counts.
Known snapshot totals protect the original published results from accidental
changes; intentional new snapshots need an explicit test update.

The page recalculates judge metrics from TP, FP, TN and FN rather than the
rounded scores in the summaries. Errors are displayed separately. Undefined
metrics display a dash; no empty denominator is interpreted as perfect performance.

## GitHub Pages

The repository includes `.github/workflows/pages.yml`. After merging it:

1. Open the repository's **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Open **Actions → Publish results explorer → Run workflow** and choose `main`.
4. Wait for the `build` and `deploy` jobs to succeed. Use the deployment URL
   returned by that run as the CV and repository demo link.

Future changes to the demo, exporter or published results trigger publication
on `main`. Pull requests run the regression workflow without publishing.
Publication uploads only `demo/`, not the repository or raw experiment logs.
The Pages build validates the aggregate export and data tests before deployment.

GitHub Pages is free for public repositories. Repository settings must enable
Pages before the deployment job can publish; the workflow does not alter those
settings. See the [official Pages workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Other static hosts

For Cloudflare Pages or Render Static Sites, use `demo` as the published
directory and leave the build command empty. All asset paths are relative,
so the site also works under a repository subpath. No API keys or environment
variables are required by the demo.
