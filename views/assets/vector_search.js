// Scroll-driven explainer for embeddings and HNSW search.
//
// The page is rendered with st.html, which can re-run this script on every
// Streamlit rerun. Each .vs root is initialized once and tears itself down
// when Streamlit removes it from the DOM.
//
// Keep this file free of anything that looks like an HTML tag (a less-than
// sign directly followed by a letter or slash), even in comments: the
// sanitizer behind st.html drops the whole script if it finds one.
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const W = 640;
  const H = 480;

  const COLORS = {
    dot: "#A3A8B4",
    dotDim: "#D5D8DE",
    query: "#EB6834",
    near: "#2563EB",
    match: "#1BAF7A",
    layer2: "#2563EB",
    layer1: "#6D9BF1",
    layer0: "#B9C0CC",
    hub2: "#4B5162",
    hub1: "#7D8394",
    brute: "#EB6834",
    plane: "rgba(37, 99, 235, 0.045)",
    planeEdge: "rgba(37, 99, 235, 0.22)",
    ink: "#31333F",
    muted: "rgba(49, 51, 63, 0.62)",
  };

  // --- small helpers ------------------------------------------------------
  const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  // Eased progress of t through the window [a, b].
  const seg = (t, a, b) => ease(clamp((t - a) / (b - a)));
  const dist = (p, q) => Math.hypot(p.x - q.x, p.y - q.y);

  function el(name, attrs, parent) {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }

  function rng(seed) {
    let s = seed;
    return () => {
      s = (s * 16807) % 2147483647;
      return (s - 1) / 2147483646;
    };
  }

  // --- data: a 2-D stand-in for the 384-dimension embedding space ---------
  function buildPoints() {
    const rand = rng(20261111);
    const gauss = () => {
      const u = Math.max(rand(), 1e-9);
      const v = rand();
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    };
    // Cluster 0 holds the story records; the others are background companies.
    const clusters = [
      { x: 0.3, y: 0.56, n: 12, sd: 0.06 },
      { x: 0.13, y: 0.2, n: 13, sd: 0.06 },
      { x: 0.5, y: 0.15, n: 12, sd: 0.06 },
      { x: 0.86, y: 0.22, n: 13, sd: 0.06 },
      { x: 0.7, y: 0.5, n: 12, sd: 0.065 },
      { x: 0.88, y: 0.8, n: 12, sd: 0.06 },
      { x: 0.55, y: 0.86, n: 12, sd: 0.06 },
      { x: 0.1, y: 0.86, n: 10, sd: 0.06 },
    ];
    const pts = [];
    clusters.forEach((c, ci) => {
      for (let i = 0; i < c.n; i++) {
        pts.push({
          x: clamp(c.x + gauss() * c.sd, 0.03, 0.97),
          y: clamp(c.y + gauss() * c.sd, 0.04, 0.96),
          cluster: ci,
          level: 0,
          role: null,
        });
      }
    });
    // Story records, placed deliberately around the query.
    const q = { x: 0.3, y: 0.56 };
    const story = [
      { role: "query", dx: 0, dy: 0 },
      { role: "match", dx: 0.028, dy: -0.03 },
      { role: "suite", dx: -0.034, dy: -0.022 },
      { role: "tenant", dx: 0.012, dy: 0.046 },
    ];
    story.forEach((s, i) => {
      Object.assign(pts[i], { x: q.x + s.dx, y: q.y + s.dy, role: s.role });
    });
    // Push other cluster-0 points out a little so the story records are the
    // nearest neighbours.
    for (let i = story.length; i < clusters[0].n; i++) {
      const p = pts[i];
      const d = dist(p, q);
      if (d < 0.07) {
        const a = Math.atan2(p.y - q.y, p.x - q.x);
        p.x = q.x + Math.cos(a) * (0.07 + rand() * 0.03);
        p.y = q.y + Math.sin(a) * (0.07 + rand() * 0.03);
      }
    }

    // HNSW levels: one hub per background cluster on layer 2 (not the
    // query's cluster, so the search has to travel and descend), and a few
    // extra nodes per cluster on layer 1.
    const byCluster = clusters.map((_, ci) => pts.filter((p) => p.cluster === ci));
    byCluster.forEach((members, ci) => {
      const free = members.filter((p) => !p.role);
      if ([1, 3, 5, 6].includes(ci)) free[0].level = 2;
      const extra = ci === 0 ? 2 : 1;
      for (let k = 1; k <= extra && k < free.length; k++) free[k].level = 1;
    });
    pts.forEach((p, i) => (p.id = i));
    return pts;
  }

  // Edges per layer: k nearest neighbours plus a minimum spanning tree, so
  // every layer is one connected graph (as a real HNSW graph would be).
  function buildEdges(pts, layer, k) {
    const nodes = pts.filter((p) => p.level >= layer);
    const key = (a, b) => (a < b ? `${a}-${b}` : `${b}-${a}`);
    const edges = new Map();
    nodes.forEach((p) => {
      nodes
        .filter((q) => q !== p)
        .sort((a, b) => dist(p, a) - dist(p, b))
        .slice(0, k)
        .forEach((q) => edges.set(key(p.id, q.id), [p.id, q.id]));
    });
    const pairs = [];
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++)
        pairs.push([nodes[i], nodes[j], dist(nodes[i], nodes[j])]);
    pairs.sort((a, b) => a[2] - b[2]);
    const parent = new Map(nodes.map((n) => [n.id, n.id]));
    const find = (x) => (parent.get(x) === x ? x : find(parent.get(x)));
    for (const [a, b] of pairs) {
      const ra = find(a.id);
      const rb = find(b.id);
      if (ra !== rb) {
        parent.set(ra, rb);
        edges.set(key(a.id, b.id), [a.id, b.id]);
      }
    }
    return [...edges.values()];
  }

  // Real greedy HNSW search over the toy graph: hop to the neighbour closest
  // to the target until no hop helps, then drop a layer.
  function greedySearch(pts, adj, target) {
    const entry = pts
      .filter((p) => p.level === 2)
      .sort((a, b) => dist(b, target) - dist(a, target))[0];
    const hops = [];
    let cur = entry;
    for (let layer = 2; layer >= 0; layer--) {
      for (;;) {
        let best = cur;
        for (const nid of adj[layer].get(cur.id) || []) {
          const n = pts[nid];
          if (n === target) continue;
          if (dist(n, target) < dist(best, target)) best = n;
        }
        if (best === cur) break;
        hops.push({ from: cur, to: best, fromLayer: layer, toLayer: layer });
        cur = best;
      }
      if (layer > 0) hops.push({ from: cur, to: cur, fromLayer: layer, toLayer: layer - 1 });
    }
    return { entry, hops };
  }

  // --- geometry -------------------------------------------------------------
  const PLANE_TOP = { 2: 34, 1: 178, 0: 322 };
  const PLANE_H = 112;
  function flatXY(p) {
    return { x: 34 + p.x * (W - 68), y: 24 + p.y * (H - 48) };
  }
  function planeXY(p, layer) {
    return { x: 150 + p.x * 400 - p.y * 110, y: PLANE_TOP[layer] + p.y * PLANE_H };
  }
  function listXY(i) {
    // Step 0: records laid out like rows in a table, under the sample rows.
    const cols = 16;
    const r = Math.floor(i / cols);
    const c = i % cols;
    return { x: 60 + c * 34.5, y: 262 + r * 30 };
  }
  function mix(a, b, t) {
    return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t) };
  }

  // --- labels -----------------------------------------------------------------
  const STORY = {
    query: {
      full: "OKADA FOODS · 458 Okada St, Ste 4",
      short: "OKADA FOODS, Ste 4",
      verdict: "The record we searched from",
      verdictShort: "Search record",
    },
    match: {
      full: "Okada Foods Co., Ltd. · 458 Okada Street, Suite 4",
      short: "Okada Foods Co., Ltd., Suite 4",
      verdict: "✓ Same company, same suite: merge",
      verdictShort: "✓ Merge",
    },
    suite: {
      full: "Okada Foods Co., Ltd. · 458 Okada Street, Suite 12",
      short: "Okada Foods, Suite 12",
      verdict: "✕ Different suite: keep separate",
      verdictShort: "✕ Different suite",
    },
    tenant: {
      full: "Okada Electric · 458 Okada St, Ste 9",
      short: "Okada Electric, Ste 9",
      verdict: "✕ Different company in the same building",
      verdictShort: "✕ Different company",
    },
  };
  const LABEL_ROWS = ["query", "match", "suite", "tenant"];

  function init(root) {
    root.dataset.ready = "1";
    // st.html strips inline SVG markup, so build the SVG element here.
    const slot = root.querySelector(".vs-canvas");
    const steps = Array.from(root.querySelectorAll(".vs-step"));
    if (!slot || !steps.length) return;
    const svg = el("svg", {
      class: "vs-svg",
      viewBox: `0 0 ${W} ${H}`,
      role: "img",
      "aria-label":
        "Animated diagram: records become points in vector space, HNSW builds a layered graph, " +
        "and a greedy search descends the layers to find a record's nearest neighbors.",
    });
    slot.replaceChildren(svg);

    const pts = buildPoints();
    const storyPts = Object.fromEntries(pts.filter((p) => p.role).map((p) => [p.role, p]));
    const query = storyPts.query;
    const edges = { 2: buildEdges(pts, 2, 2), 1: buildEdges(pts, 1, 2), 0: buildEdges(pts, 0, 3) };
    const adj = [0, 1, 2].map((layer) => {
      const m = new Map();
      for (const [a, b] of edges[layer]) {
        if (!m.has(a)) m.set(a, []);
        if (!m.has(b)) m.set(b, []);
        m.get(a).push(b);
        m.get(b).push(a);
      }
      return m;
    });
    const search = greedySearch(pts, adj, query);
    const neighbours = pts
      .filter((p) => p !== query)
      .sort((a, b) => dist(a, query) - dist(b, query))
      .slice(0, 3);
    const ringR = dist(neighbours[neighbours.length - 1], query) * (W - 68) + 14;

    // Layers of the drawing, back to front.
    const gPlanes = el("g", {}, svg);
    const gBrute = el("g", {}, svg);
    const gEdges = el("g", {}, svg);
    const gLinks = el("g", {}, svg);
    const gTargets = el("g", {}, svg);
    const gPath = el("g", {}, svg);
    const gRing = el("g", {}, svg);
    const gDots = el("g", {}, svg);
    const gLabels = el("g", {}, svg);
    const gText = el("g", {}, svg);

    // Planes for the layered view.
    const planes = [2, 1, 0].map((layer) => {
      const g = el("g", {}, gPlanes);
      const corners = [
        { x: 0, y: 0 },
        { x: 1, y: 0 },
        { x: 1, y: 1 },
        { x: 0, y: 1 },
      ].map((c) => planeXY(c, layer));
      el(
        "polygon",
        {
          points: corners.map((c) => `${c.x - 12},${c.y}`).join(" "),
          fill: COLORS.plane,
          stroke: COLORS.planeEdge,
          "stroke-width": 1,
        },
        g,
      );
      const names = {
        2: "Layer 2 · few records, long links",
        1: "Layer 1 · more records",
        0: "Layer 0 · every record, short links",
      };
      const t = el("text", { x: 14, y: PLANE_TOP[layer] - 6, class: "vs-plane-label" }, g);
      t.textContent = names[layer];
      return g;
    });

    // Brute force: lines from the query to every record.
    const brute = pts
      .filter((p) => p !== query)
      .map(() => el("line", { stroke: COLORS.brute, "stroke-width": 0.6 }, gBrute));

    // Graph edges per layer.
    const edgeEls = { 0: [], 1: [], 2: [] };
    const edgeStyle = {
      2: { stroke: COLORS.layer2, w: 1.6 },
      1: { stroke: COLORS.layer1, w: 1.2 },
      0: { stroke: COLORS.layer0, w: 0.9 },
    };
    [0, 1, 2].forEach((layer) => {
      for (const [a, b] of edges[layer]) {
        const line = el(
          "line",
          { stroke: edgeStyle[layer].stroke, "stroke-width": edgeStyle[layer].w, "stroke-linecap": "round" },
          gEdges,
        );
        edgeEls[layer].push({ line, a: pts[a], b: pts[b] });
      }
    });

    // Vertical links between copies of the same record on adjacent layers.
    const links = [];
    pts
      .filter((p) => p.level > 0)
      .forEach((p) => {
        for (let layer = 1; layer <= p.level; layer++) {
          const line = el(
            "line",
            { stroke: COLORS.layer1, "stroke-width": 0.8, "stroke-dasharray": "2 3" },
            gLinks,
          );
          links.push({ line, p, layer });
        }
      });

    // Where the query would sit on each layer: the search heads for it.
    const targets = [2, 1, 0].map((layer) => {
      const g = el("g", {}, gTargets);
      el("circle", { r: 7, fill: "none", stroke: COLORS.query, "stroke-width": 1.4, "stroke-dasharray": "3 2" }, g);
      return { g, layer };
    });

    // Search path.
    const pathSegs = search.hops.map((h) => ({
      h,
      line: el(
        "line",
        {
          stroke: COLORS.query,
          "stroke-width": h.fromLayer === h.toLayer ? 2.4 : 1.6,
          "stroke-linecap": "round",
          "stroke-dasharray": h.fromLayer === h.toLayer ? "" : "3 3",
        },
        gPath,
      ),
    }));
    const probe = el("circle", { r: 5.5, fill: COLORS.query, stroke: "#fff", "stroke-width": 2 }, gPath);
    const entryLabel = el("text", { class: "vs-small", "text-anchor": "middle" }, gPath);
    entryLabel.textContent = "start here";

    // Neighbour ring.
    const ring = el(
      "circle",
      { r: ringR, fill: "rgba(37, 99, 235, 0.06)", stroke: COLORS.near, "stroke-width": 1.4, "stroke-dasharray": "4 3" },
      gRing,
    );
    const ringLabel = el("text", { class: "vs-small", "text-anchor": "middle" }, gRing);
    ringLabel.textContent = "cosine ≥ 0.70";

    // Dots: one base dot per record plus copies on layers 1 and 2.
    const dots = pts.map((p) => {
      const base = el("circle", { r: 3.6, stroke: "#fff", "stroke-width": 1.5 }, gDots);
      const copies = {};
      for (let layer = 1; layer <= p.level; layer++) {
        copies[layer] = el("circle", { r: layer === 2 ? 4.6 : 4, stroke: "#fff", "stroke-width": 1.5 }, gDots);
      }
      return { p, base, copies };
    });
    // Story dots on top.
    LABEL_ROWS.forEach((role) => gDots.appendChild(dots[storyPts[role].id].base));

    // Story labels with leader lines.
    const labels = LABEL_ROWS.map((role, i) => {
      const g = el("g", {}, gLabels);
      const leader = el("line", { stroke: COLORS.muted, "stroke-width": 0.8 }, g);
      const bg = el("rect", { rx: 6, fill: "#fff", stroke: "rgba(49,51,63,0.14)" }, g);
      const swatch = el("circle", { r: 4 }, g);
      const text = el("text", { class: "vs-label" }, g);
      const sub = el("text", { class: "vs-sub" }, g);
      return { role, i, g, leader, bg, swatch, text, sub };
    });

    // Step 0: sample rows drawn as a little table.
    const table = el("g", {}, gText);
    const tableRows = LABEL_ROWS.map((role, i) => {
      const y = 46 + i * 44;
      const g = el("g", {}, table);
      el("rect", { x: 40, y: y - 18, width: 560, height: 34, rx: 7, fill: "#fff", stroke: "rgba(49,51,63,0.14)" }, g);
      const t = el("text", { x: 56, y: y + 4, class: "vs-row" }, g);
      t.textContent = STORY[role].full;
      return { g, t, role };
    });
    const vectorChip = el("text", { x: 320, y: 236, class: "vs-small", "text-anchor": "middle" }, table);
    vectorChip.textContent = "Each row becomes 384 numbers: [0.12, −0.41, 0.07, … , 0.33]";

    const counter = el("text", { x: W / 2, y: 20, class: "vs-counter", "text-anchor": "middle" }, gText);
    counter.textContent = "33,702 records → 567,895,551 possible pairs";

    // --- render one frame for scroll position t --------------------------
    function render(t) {
      const narrow = svg.getBoundingClientRect().width < 520;
      root.classList.toggle("vs-narrow", narrow);

      // Each step's picture is complete by the time its text is centred
      // (t = step index); transitions play while scrolling between steps.
      const toSpace = seg(t, 0.15, 0.85); // rows fly into embedding space
      const tableOn = 1 - seg(t, 0.05, 0.5);
      const bruteOn = seg(t, 1.35, 1.85) * (1 - seg(t, 2.15, 2.4));
      const layered = seg(t, 2.2, 2.75) * (1 - seg(t, 4.25, 4.75));
      const drawL2 = seg(t, 2.5, 2.7);
      const drawL1 = seg(t, 2.6, 2.8);
      const drawL0 = seg(t, 2.7, 2.95);
      const edgeFade = 1 - seg(t, 4.25, 4.55);
      const searchP = clamp((t - 3.25) / (3.95 - 3.25));
      const searchOn = seg(t, 3.15, 3.3) * (1 - seg(t, 4.25, 4.45));
      const ringOn = seg(t, 4.5, 4.95);
      const verdictOn = seg(t, 5.35, 5.85);
      const labelOn = seg(t, 0.6, 0.95) * (1 - seg(t, 1.35, 1.6)) + ringOn;
      const focus = ringOn; // dim background records in the final steps

      table.setAttribute("opacity", tableOn);
      tableRows.forEach((r) => r.g.setAttribute("opacity", tableOn));
      counter.setAttribute("opacity", bruteOn);

      // Planes.
      planes.forEach((g) => g.setAttribute("opacity", layered));

      // Positions.
      const base = new Map();
      pts.forEach((p, i) => {
        const start = listXY(i);
        const flat = flatXY(p);
        const inSpace = mix(start, flat, toSpace);
        base.set(p.id, mix(inSpace, planeXY(p, 0), layered));
      });
      const at = (p, layer) => (layer === 0 ? base.get(p.id) : mix(flatXY(p), planeXY(p, layer), layered));

      // Dots.
      dots.forEach(({ p, base: c, copies }) => {
        const pos = base.get(p.id);
        let fill = COLORS.dot;
        let r = 3.6;
        if (p.role === "query") {
          fill = COLORS.query;
          r = 6;
        } else if (neighbours.includes(p) && ringOn > 0) {
          fill = COLORS.near;
          r = 3.6 + 1.4 * ringOn;
        } else if (focus > 0) {
          fill = COLORS.dotDim;
        }
        if (p.role && p.role !== "query") r = Math.max(r, 4.6);
        if (p.role === "match" && verdictOn > 0) fill = COLORS.match;
        if (p.role && p.role !== "query" && labelOn > 0 && ringOn === 0) fill = COLORS.near;
        c.setAttribute("cx", pos.x);
        c.setAttribute("cy", pos.y);
        c.setAttribute("r", r);
        c.setAttribute("fill", fill);
        for (const [layer, copy] of Object.entries(copies)) {
          const q = at(p, Number(layer));
          copy.setAttribute("cx", q.x);
          copy.setAttribute("cy", q.y);
          copy.setAttribute("fill", Number(layer) === 2 ? COLORS.hub2 : COLORS.hub1);
          copy.setAttribute("opacity", layered);
        }
      });

      // Brute-force lines.
      const qPos = base.get(query.id);
      let bi = 0;
      pts.forEach((p) => {
        if (p === query) return;
        const line = brute[bi++];
        const pos = base.get(p.id);
        line.setAttribute("x1", qPos.x);
        line.setAttribute("y1", qPos.y);
        line.setAttribute("x2", lerp(qPos.x, pos.x, bruteOn));
        line.setAttribute("y2", lerp(qPos.y, pos.y, bruteOn));
        line.setAttribute("opacity", 0.55 * bruteOn);
      });

      // Edges: drawn in as the layers appear, shown flat afterwards for a beat.
      const drawBy = { 2: drawL2, 1: drawL1, 0: drawL0 };
      [0, 1, 2].forEach((layer) => {
        const reveal = drawBy[layer];
        edgeEls[layer].forEach(({ line, a, b }) => {
          const pa = at(a, layer);
          const pb = at(b, layer);
          line.setAttribute("x1", pa.x);
          line.setAttribute("y1", pa.y);
          line.setAttribute("x2", lerp(pa.x, pb.x, reveal));
          line.setAttribute("y2", lerp(pa.y, pb.y, reveal));
          const base = layer === 0 ? 0.75 : 0.85;
          line.setAttribute("opacity", reveal * edgeFade * base * (searchOn > 0 ? 0.55 : 1));
        });
      });

      // Vertical links.
      links.forEach(({ line, p, layer }) => {
        const top = at(p, layer);
        const bottom = at(p, layer - 1);
        line.setAttribute("x1", top.x);
        line.setAttribute("y1", top.y);
        line.setAttribute("x2", bottom.x);
        line.setAttribute("y2", bottom.y);
        line.setAttribute("opacity", layered * 0.7);
      });

      // Target markers.
      targets.forEach(({ g, layer }) => {
        const q = planeXY(query, layer);
        g.setAttribute("transform", `translate(${q.x},${q.y})`);
        g.setAttribute("opacity", layer === 0 ? 0 : layered * searchOn);
      });

      // Search path.
      const n = pathSegs.length;
      const head = searchP * n;
      let probePos = at(search.entry, 2);
      pathSegs.forEach(({ h, line }, i) => {
        const a = at(h.from, h.fromLayer);
        const b = at(h.to, h.toLayer);
        const f = clamp(head - i);
        line.setAttribute("x1", a.x);
        line.setAttribute("y1", a.y);
        line.setAttribute("x2", lerp(a.x, b.x, f));
        line.setAttribute("y2", lerp(a.y, b.y, f));
        line.setAttribute("opacity", f > 0 ? searchOn : 0);
        if (f > 0) probePos = { x: lerp(a.x, b.x, f), y: lerp(a.y, b.y, f) };
      });
      if (head >= n) probePos = at(pathSegs[n - 1].h.to, 0);
      probe.setAttribute("cx", probePos.x);
      probe.setAttribute("cy", probePos.y);
      probe.setAttribute("opacity", searchOn);
      const e = at(search.entry, 2);
      entryLabel.setAttribute("x", e.x);
      entryLabel.setAttribute("y", e.y - 11);
      entryLabel.setAttribute("opacity", searchOn * (1 - seg(searchP, 0.25, 0.45)));

      // Ring.
      ring.setAttribute("cx", qPos.x);
      ring.setAttribute("cy", qPos.y);
      ring.setAttribute("r", ringR * (0.6 + 0.4 * ringOn));
      ring.setAttribute("opacity", ringOn);
      ringLabel.setAttribute("x", qPos.x);
      ringLabel.setAttribute("y", qPos.y + ringR + 15);
      ringLabel.setAttribute("opacity", ringOn * (1 - verdictOn));

      // Story labels: one shared box width, sized to the longest text and
      // kept inside the right edge.
      let textW = 0;
      labels.forEach((L) => {
        const story = STORY[L.role];
        L.text.textContent = narrow ? story.short : story.full;
        L.sub.textContent = narrow ? story.verdictShort : story.verdict;
        L.sub.setAttribute("opacity", verdictOn);
        textW = Math.max(textW, L.text.getComputedTextLength());
        if (verdictOn > 0) textW = Math.max(textW, L.sub.getComputedTextLength());
      });
      const boxW = Math.min(textW + 40, W - 16);
      const lx = Math.max(W - 8 - boxW, 8);
      labels.forEach((L) => {
        const pos = base.get(storyPts[L.role].id);
        const ly = 186 + L.i * (narrow ? 64 : 58);
        L.bg.setAttribute("x", lx);
        L.bg.setAttribute("y", ly - 19);
        L.bg.setAttribute("width", boxW);
        L.bg.setAttribute("height", lerp(30, 48, verdictOn));
        L.swatch.setAttribute("cx", lx + 14);
        L.swatch.setAttribute("cy", ly - 4);
        let sw = L.role === "query" ? COLORS.query : COLORS.near;
        if (L.role === "match" && verdictOn > 0) sw = COLORS.match;
        L.swatch.setAttribute("fill", sw);
        L.text.setAttribute("x", lx + 26);
        L.text.setAttribute("y", ly + 1);
        L.sub.setAttribute("x", lx + 26);
        L.sub.setAttribute("y", ly + 20);
        L.leader.setAttribute("x1", pos.x);
        L.leader.setAttribute("y1", pos.y);
        L.leader.setAttribute("x2", lx);
        L.leader.setAttribute("y2", ly - 4);
        L.g.setAttribute("opacity", clamp(labelOn) * (1 - layered));
      });
    }

    // --- scroll → t --------------------------------------------------------
    // t equals i when step i's centre crosses the middle of the viewport.
    const stage = root.querySelector(".vs-stage");
    const stacked = window.matchMedia("(max-width: 820px)");
    function targetT() {
      // Side by side, steps are read at mid-screen. Stacked (phones), the
      // diagram is pinned on top, so read steps in the space below it.
      let anchor = window.innerHeight * 0.55;
      if (stacked.matches && stage) {
        const bottom = stage.getBoundingClientRect().bottom;
        anchor = bottom + (window.innerHeight - bottom) * 0.45;
      }
      const centers = steps.map((s) => {
        const r = s.getBoundingClientRect();
        return r.top + r.height / 2;
      });
      if (anchor <= centers[0]) return 0;
      for (let i = 0; i < centers.length - 1; i++) {
        if (anchor <= centers[i + 1]) {
          return i + (anchor - centers[i]) / (centers[i + 1] - centers[i]);
        }
      }
      return centers.length - 1;
    }

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let current = targetT();
    let goal = current;
    let frame = 0;
    let activeStep = -1;

    function tick() {
      frame = 0;
      if (!root.isConnected) return teardown();
      current = reduceMotion ? goal : lerp(current, goal, 0.18);
      if (Math.abs(goal - current) < 0.001) current = goal;
      render(current);
      const idx = Math.round(clamp(goal, 0, steps.length - 1));
      if (idx !== activeStep) {
        steps.forEach((s, i) => s.classList.toggle("is-active", i === idx));
        activeStep = idx;
      }
      if (current !== goal) frame = requestAnimationFrame(tick);
    }
    function onScroll() {
      if (!root.isConnected) return teardown();
      goal = targetT();
      if (!frame) frame = requestAnimationFrame(tick);
    }
    function teardown() {
      document.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
    }
    // Streamlit scrolls an inner container, not the window: listen in the
    // capture phase so scrolls on any element reach us.
    document.addEventListener("scroll", onScroll, { capture: true, passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    render(current);
    onScroll();
  }

  // Streamlit can run this script before it attaches the HTML, so retry
  // briefly until the root shows up.
  let tries = 0;
  (function scan() {
    const roots = document.querySelectorAll(".vs:not([data-ready])");
    roots.forEach(init);
    if (!roots.length && tries++ < 100) setTimeout(scan, 50);
  })();
})();
