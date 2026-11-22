/* Browser-only explorer. No provider requests or credentials. */
(() => {
  "use strict";
  const data = window.REDAGENT_DATA;
  const $ = (id) => document.getElementById(id);
  const escape = (value) => String(value).replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const pct = (n) => n === null ? "—" : `${(n * 100).toFixed(1)}%`;
  const divide = (a, b) => b ? a / b : null;
  const shortName = (model) => model.split("/").at(-1);
  const provider = (model) => model.split("/").slice(0, -1).join(" / ");
  const sourceUrl = (path) => `https://github.com/abdel-saw/redagent/blob/main/${path}`;

  function wilson(k, n) {
    if (!n) return [0, 0];
    const z = 1.96, p = k / n, d = 1 + z * z / n;
    const center = (p + z * z / (2 * n)) / d;
    const half = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d;
    return [Math.max(0, center - half), Math.min(1, center + half)];
  }

  function options(select, items, selected) {
    select.replaceChildren(...items.map(([value, label]) => {
      const option = document.createElement("option");
      option.value = value; option.textContent = label; return option;
    }));
    if (selected && items.some(([value]) => value === selected)) select.value = selected;
  }

  function stat(label, value, detail) {
    return `<div class="stat"><span class="stat-label">${escape(label)}</span><strong>${escape(value)}</strong><small>${escape(detail)}</small></div>`;
  }

  function modelLabel(model) {
    return `<span class="model-name">${escape(shortName(model))}</span><span class="model-provider">${escape(provider(model))}</span>`;
  }

  function renderAttacks() {
    const dataset = data.attacks.find((d) => d.id === $("attack-dataset").value);
    const challenge = $("challenge").value;
    const filtered = dataset.rows.filter((r) => challenge === "all" || r.challenge === challenge);
    const grouped = new Map();
    for (const row of filtered) {
      if (!grouped.has(row.model)) grouped.set(row.model, {model: row.model, runs: 0, captures: 0});
      const result = grouped.get(row.model); result.runs += row.runs; result.captures += row.captures;
    }
    const models = [...grouped.values()];
    const n = models.reduce((s, r) => s + r.runs, 0), k = models.reduce((s, r) => s + r.captures, 0);
    const interval = wilson(k, n);
    $("attack-summary").innerHTML = stat("Completed runs", n, challenge === "all" ? "Pooled across challenges" : challenge)
      + stat("Captured runs", k, `${models.length} attacker models represented`)
      + stat("Capture rate", pct(divide(k, n)), `95% interval: ${pct(interval[0])}–${pct(interval[1])}`);
    $("attack-rows").innerHTML = models.map((row) => {
      const rate = row.captures / row.runs, ci = wilson(row.captures, row.runs);
      return `<tr><td>${modelLabel(row.model)}</td><td>${row.captures} / ${row.runs}</td><td class="rate-cell"><div class="rate-wrap"><span class="mini-track" aria-hidden="true"><span style="width:${rate * 100}%"></span></span><span class="rate-number">${pct(rate)}</span></div></td><td>${pct(ci[0])}–${pct(ci[1])}</td></tr>`;
    }).join("");
    $("attack-source").href = sourceUrl(dataset.source);
  }

  function changeAttackDataset() {
    const dataset = data.attacks.find((d) => d.id === $("attack-dataset").value);
    const previous = $("challenge").value;
    const challenges = [...new Set(dataset.rows.map((r) => r.challenge))].sort();
    options($("challenge"), [["all", "All challenges (pooled)"], ...challenges.map((c) => [c, c])], previous);
    renderAttacks();
  }

  function judgeMetrics(row) {
    const n = row.tp + row.fp + row.tn + row.fn;
    return {n, precision: divide(row.tp, row.tp + row.fp), recall: divide(row.tp, row.tp + row.fn), f1: divide(2 * row.tp, 2 * row.tp + row.fp + row.fn)};
  }

  function renderJudges() {
    const dataset = data.judges.find((d) => d.id === $("judge-dataset").value);
    const row = dataset.rows.find((r) => r.model === $("judge-model").value);
    const m = judgeMetrics(row);
    $("judge-summary").innerHTML = stat("Precision", pct(m.precision), "Positive verdicts matching the oracle")
      + stat("Recall", pct(m.recall), "Oracle captures identified by this judge")
      + stat("F1 score", pct(m.f1), `${m.n} judged responses · ${row.errors} errors`);
    const boxes = [["True positives", row.tp, "Judge positive · oracle capture", false], ["False positives", row.fp, "Judge positive · no oracle capture", true], ["False negatives", row.fn, "Judge negative · oracle capture", true], ["True negatives", row.tn, "Judge negative · no oracle capture", false]];
    $("confusion").innerHTML = boxes.map(([label, value, detail, error]) => `<div class="confusion-box${error ? " error" : ""}"><span>${label}</span><strong>${value}</strong><small>${detail}</small></div>`).join("");
    $("judge-rows").innerHTML = dataset.rows.map((r, i) => {
      const values = judgeMetrics(r);
      return `<tr${r.model === row.model ? ' class="selected-row"' : ""}><td><button type="button" class="judge-inspect" data-judge="${i}" aria-pressed="${r.model === row.model}">${modelLabel(r.model)}</button></td><td>${values.n}</td><td>${pct(values.precision)}</td><td>${pct(values.recall)}</td><td>${pct(values.f1)}</td><td>${r.fp} / ${r.fn}</td><td>${r.errors}</td></tr>`;
    }).join("");
    $("judge-source").href = sourceUrl(dataset.source);
  }

  function changeJudgeDataset() {
    const dataset = data.judges.find((d) => d.id === $("judge-dataset").value);
    const previous = $("judge-model").value;
    options($("judge-model"), dataset.rows.map((r) => [r.model, shortName(r.model)]), previous);
    renderJudges();
  }

  function switchTab(name, focus = false) {
    for (const view of ["attack", "judge"]) {
      const active = view === name;
      $(`${view}-tab`).setAttribute("aria-selected", String(active));
      $(`${view}-tab`).tabIndex = active ? 0 : -1;
      $(`${view}-panel`).hidden = !active;
    }
    if (focus) $(`${name}-tab`).focus();
  }

  if (!data || data.schema !== 1 || !data.attacks.length || !data.judges.length) {
    $("attack-summary").textContent = "The results could not be loaded. Please use the source logs link to view them on GitHub.";
    $("download").disabled = true;
    return;
  }

  options($("attack-dataset"), data.attacks.map((d) => [d.id, d.label]));
  options($("judge-dataset"), data.judges.map((d) => [d.id, d.label]));
  $("attack-dataset").addEventListener("change", changeAttackDataset);
  $("challenge").addEventListener("change", renderAttacks);
  $("judge-dataset").addEventListener("change", changeJudgeDataset);
  $("judge-model").addEventListener("change", renderJudges);
  $("judge-rows").addEventListener("click", (event) => {
    const button = event.target.closest("[data-judge]");
    if (!button) return;
    const dataset = data.judges.find((d) => d.id === $("judge-dataset").value);
    const index = Number(button.dataset.judge);
    $("judge-model").value = dataset.rows[index].model;
    renderJudges();
    $("judge-rows").querySelector(`[data-judge="${index}"]`).focus();
  });
  for (const name of ["attack", "judge"]) {
    $(`${name}-tab`).addEventListener("click", () => switchTab(name));
    $(`${name}-tab`).addEventListener("keydown", (event) => {
      if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        switchTab(event.key === "Home" ? "attack" : event.key === "End" ? "judge" : name === "attack" ? "judge" : "attack", true);
      }
    });
  }
  $("download").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = "redagent-published-aggregates.json";
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  changeAttackDataset();
  changeJudgeDataset();
})();
