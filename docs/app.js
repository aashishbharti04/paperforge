/* PaperForge — browser app.
 * A JavaScript port of the Python package's humanizer, parser, and renderers,
 * so the whole thing runs client-side on GitHub Pages (no server, no upload).
 *
 * Sections below mirror the Python modules:
 *   HUMANIZER  <- paperforge/humanizer.py
 *   PARSER     <- paperforge/parsers/*  (heuristics + text/docx readers)
 *   LATEX      <- paperforge/renderers/latex_render.py
 *   DOCX       <- paperforge/renderers/docx_render.py  (via docx.js)
 *   UI         <- the Tkinter GUI, as a web page
 */
(function () {
  "use strict";

  /* =======================================================================
   * HUMANIZER
   * ===================================================================== */
  const PHRASE_MAP = [
    ["it is important to note that", ""], ["it is worth noting that", ""],
    ["it should be noted that", ""], ["it is worth mentioning that", ""],
    ["needless to say,", ""], ["as a matter of fact,", ""],
    ["at the end of the day,", ""], ["when it comes to", "for"],
    ["in order to", "to"], ["due to the fact that", "because"],
    ["owing to the fact that", "because"], ["in light of the fact that", "because"],
    ["in the event that", "if"], ["in the event of", "if there is"],
    ["for the purpose of", "to"], ["with the aim of", "to"],
    ["a large number of", "many"], ["a significant number of", "many"],
    ["a wide range of", "many"], ["a plethora of", "many"],
    ["a myriad of", "many"], ["a majority of", "most"],
    ["the vast majority of", "most"], ["a small number of", "a few"],
    ["plays a crucial role in", "is central to"],
    ["plays a vital role in", "is central to"],
    ["plays a key role in", "is central to"],
    ["plays a significant role in", "matters in"],
    ["in the realm of", "in"], ["in the world of", "in"],
    ["with regard to", "about"], ["with respect to", "about"],
    ["in terms of", "for"], ["prior to", "before"], ["subsequent to", "after"],
    ["in conclusion,", ""], ["in summary,", ""], ["to summarize,", ""],
    ["first and foremost,", "first,"], ["last but not least,", "finally,"],
    ["a testament to", "proof of"], ["stands as a testament to", "shows"],
    ["paving the way for", "enabling"], ["paves the way for", "enables"],
    ["the ever-evolving", "the changing"], ["ever-evolving", "changing"],
    ["an integral part of", "a key part of"],
    ["in today's fast-paced world,", ""], ["in today's digital age,", ""],
    ["it goes without saying that", ""],
  ];

  const WORD_MAP = [
    ["utilize", "use"], ["utilizes", "uses"], ["utilized", "used"],
    ["utilizing", "using"], ["utilization", "use"],
    ["leverage", "use"], ["leverages", "uses"], ["leveraging", "using"],
    ["facilitate", "help"], ["facilitates", "helps"], ["facilitated", "helped"],
    ["facilitating", "helping"],
    ["delve", "look"], ["delves", "looks"], ["delving", "looking"],
    ["commence", "start"], ["commences", "starts"], ["commenced", "started"],
    ["endeavor", "try"], ["endeavors", "tries"], ["ascertain", "find out"],
    ["demonstrate", "show"], ["demonstrates", "shows"], ["demonstrated", "showed"],
    ["subsequently", "then"], ["furthermore", "also"], ["moreover", "also"],
    ["additionally", "also"], ["consequently", "so"], ["therefore", "so"],
    ["nevertheless", "still"], ["nonetheless", "still"],
    ["approximately", "about"], ["numerous", "many"], ["myriad", "many"],
    ["plethora", "plenty"], ["pivotal", "key"], ["crucial", "key"],
    ["paramount", "key"], ["robust", "strong"], ["seamless", "smooth"],
    ["seamlessly", "smoothly"], ["comprehensive", "complete"],
    ["intricate", "complex"], ["multifaceted", "complex"],
    ["realm", "area"], ["landscape", "area"], ["underscore", "highlight"],
    ["underscores", "highlights"], ["underscored", "highlighted"],
    ["showcase", "show"], ["showcases", "shows"], ["showcasing", "showing"],
    ["encompass", "include"], ["encompasses", "includes"],
    ["elucidate", "explain"], ["elucidates", "explains"],
    ["ameliorate", "improve"], ["optimal", "best"],
    ["aforementioned", "above"], ["henceforth", "from now on"],
  ];

  const FILLER_WORDS = [
    "very", "really", "quite", "actually", "basically", "essentially",
    "literally", "simply", "just", "definitely", "certainly", "arguably",
    "notably", "interestingly", "importantly",
  ];

  const CONTRACTIONS = [
    ["do not", "don't"], ["does not", "doesn't"], ["did not", "didn't"],
    ["is not", "isn't"], ["are not", "aren't"], ["was not", "wasn't"],
    ["were not", "weren't"], ["has not", "hasn't"], ["have not", "haven't"],
    ["had not", "hadn't"], ["will not", "won't"], ["would not", "wouldn't"],
    ["can not", "can't"], ["cannot", "can't"], ["could not", "couldn't"],
    ["should not", "shouldn't"], ["it is", "it's"], ["that is", "that's"],
    ["there is", "there's"], ["they are", "they're"], ["we are", "we're"],
    ["you are", "you're"], ["we will", "we'll"], ["they will", "they'll"],
    ["we have", "we've"], ["they have", "they've"],
  ];

  function optionsForLevel(level) {
    if (level === "light")
      return { vocab: true, filler: false, contractions: false, split: false };
    if (level === "strong")
      return { vocab: true, filler: true, contractions: true, split: true };
    return { vocab: true, filler: true, contractions: false, split: true };
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function matchCase(original, repl) {
    if (!repl) return repl;
    const c = original.charAt(0);
    if (c === c.toUpperCase() && c !== c.toLowerCase())
      return repl.charAt(0).toUpperCase() + repl.slice(1);
    return repl;
  }

  function applyPhrases(text, counter) {
    for (const [phrase, repl] of PHRASE_MAP) {
      const re = new RegExp(escapeRegex(phrase).replace(/ /g, "\\s+"), "gi");
      text = text.replace(re, (m) => { counter.n++; return repl ? matchCase(m, repl) : ""; });
    }
    return text;
  }

  function applyWords(text, mapping, counter) {
    for (const [word, repl] of mapping) {
      const re = new RegExp("\\b" + escapeRegex(word) + "\\b", "gi");
      text = text.replace(re, (m) => { counter.n++; return matchCase(m, repl); });
    }
    return text;
  }

  function removeFiller(text, counter) {
    for (const word of FILLER_WORDS) {
      const re = new RegExp("\\b" + escapeRegex(word) + "\\b\\s?", "gi");
      text = text.replace(re, () => { counter.n++; return ""; });
    }
    return text;
  }

  function splitLongSentences(text, maxWords, counter) {
    const sentences = text.split(/(?<=[.!?])\s+/);
    const out = [];
    for (let s of sentences) {
      if (s.split(/\s+/).length > maxWords && s.includes("; ")) {
        let parts = s.split("; ").map((p) => p.trim()).filter(Boolean);
        parts = parts.map((p) => (/[.!?]$/.test(p) ? p : p + "."));
        parts = parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1));
        counter.n += parts.length - 1;
        out.push(parts.join(" "));
      } else out.push(s);
    }
    return out.join(" ");
  }

  function cleanup(text) {
    text = text.replace(/[ \t]{2,}/g, " ");
    text = text.replace(/\s+([,.;:!?])/g, "$1");
    text = text.replace(/\(\s+/g, "(").replace(/\s+\)/g, ")");
    text = text.replace(/,\s*,/g, ",");
    text = text.trim();
    text = text.replace(/(^\s*|[.!?]\s+)([a-z])/g, (m, p1, p2) => p1 + p2.toUpperCase());
    return text.trim();
  }

  function humanizeText(text, level, opts) {
    if (text == null) text = "";
    opts = opts || optionsForLevel(level);
    const counter = { n: 0 };
    if (opts.vocab) {
      text = applyPhrases(text, counter);
      text = applyWords(text, WORD_MAP, counter);
    }
    if (opts.contractions) text = applyWords(text, CONTRACTIONS, counter);
    if (opts.filler) text = removeFiller(text, counter);
    if (opts.split) text = splitLongSentences(text, 32, counter);
    text = cleanup(text);
    return { text: text, changes: counter.n };
  }

  /* =======================================================================
   * PARSER  (heuristics + readers)
   * ===================================================================== */
  const ABSTRACT_RE = /^\s*abstract\b[\s:.\-—]*/i;
  const KEYWORDS_RE = /^\s*(keywords|key words|index terms)\b[\s:.\-—]*/i;
  const REFERENCES_RE = /^\s*(references|bibliography)\s*$/i;
  const REFERENCES_START_RE = /^\s*(references|bibliography)\b[\s:.\-—]*/i;
  const AFFIL_KEYWORDS_RE = /\b(university|department|dept\.?|institute|laborator|school|college|faculty|centre|center|academy|hospital|corporation|company|inc\.?|ltd\.?)/i;
  const NUM_HEADING_RE = /^\s*(?:(\d+(?:\.\d+)*)\.?|([IVXLC]+)\.|([A-Z])\.)\s+(\S.*)$/;
  const REF_ITEM_RE = /^\s*(?:\[(\d+)\]|(\d+)\.)\s+/;

  function isTitleCase(s) {
    let foundCased = false, prevCased = false, ok = true;
    for (const ch of s) {
      if (/[a-zA-Z]/.test(ch)) {
        const upper = ch === ch.toUpperCase();
        if (!prevCased) { if (!upper) { ok = false; break; } foundCased = true; }
        else if (upper) { ok = false; break; }
        prevCased = true;
      } else prevCased = false;
    }
    return ok && foundCased;
  }

  function looksLikeHeading(text) {
    const t = (text || "").trim();
    if (!t || t.length > 120) return null;
    const m = NUM_HEADING_RE.exec(t);
    if (m) return m[1] ? (m[1].split(".").length) : 1;
    if (t.split(/\s+/).length <= 10 && !/[.,;:]$/.test(t)) {
      const hasLetter = /[a-zA-Z]/.test(t);
      const isUpper = t === t.toUpperCase() && hasLetter;
      if (hasLetter && (isUpper || isTitleCase(t))) return 1;
    }
    return null;
  }

  function stripHeadingNumber(text) {
    const m = NUM_HEADING_RE.exec(text.trim());
    return m ? m[4].trim() : text.trim();
  }

  function splitReferences(blob) {
    const refs = [];
    let parts;
    if (/\[\d+\]/.test(blob)) parts = blob.split(/(?=\[\d+\])/);
    else parts = blob.split(/(?=^\s*\d+\.\s)/m);
    let i = 0;
    for (let part of parts) {
      part = part.trim();
      if (!part) continue;
      const clean = part.replace(REF_ITEM_RE, "").trim();
      refs.push({ raw: clean, key: "ref" + (++i) });
    }
    return refs;
  }

  function normalizeLevels(sections, depth) {
    for (const sec of sections) {
      sec.level = depth;
      normalizeLevels(sec.children, depth + 1);
    }
  }

  function buildPaper(blocks) {
    const paper = { title: "", authors: [], abstract: "", keywords: [],
                    sections: [], references: [], warnings: [] };
    blocks = blocks.filter((b) => b.text && b.text.trim());
    if (!blocks.length) { paper.warnings.push("No readable text found."); return paper; }

    let i = 0; const n = blocks.length;
    paper.title = blocks[0].text.trim(); i = 1;

    const authorLines = [];
    while (i < n && !ABSTRACT_RE.test(blocks[i].text)) {
      const t = blocks[i].text.trim();
      if (REFERENCES_RE.test(t) || NUM_HEADING_RE.test(t)) break;
      if (authorLines.length && looksLikeHeading(t)) break;
      authorLines.push(t); i++;
      if (authorLines.length >= 4) break;
    }
    if (authorLines.length) {
      const first = authorLines[0];
      let namePart = first, gluedAffil = "";
      const m = AFFIL_KEYWORDS_RE.exec(first);
      if (m) { namePart = first.slice(0, m.index).replace(/[ ,;]+$/, ""); gluedAffil = first.slice(m.index).trim(); }
      for (let nm of namePart.split(/,| and /)) {
        nm = nm.trim();
        if (nm) paper.authors.push({ name: nm, affiliation: "", email: "" });
      }
      const affil = [gluedAffil].concat(authorLines.slice(1)).join(" ").trim();
      if (affil) paper.authors.forEach((a) => (a.affiliation = affil));
    }

    if (i < n && ABSTRACT_RE.test(blocks[i].text)) {
      let abs = blocks[i].text.replace(ABSTRACT_RE, "").trim(); i++;
      while (i < n) {
        const t = blocks[i].text.trim();
        if (KEYWORDS_RE.test(t) || looksLikeHeading(t) || REFERENCES_RE.test(t)) break;
        abs += (abs ? "\n\n" : "") + t; i++;
      }
      paper.abstract = abs.trim();
    }

    if (i < n && KEYWORDS_RE.test(blocks[i].text)) {
      const kw = blocks[i].text.replace(KEYWORDS_RE, "").trim().replace(/\.$/, "");
      paper.keywords = kw.split(/[,;]/).map((k) => k.trim()).filter(Boolean); i++;
    }

    let current = null, parentStack = [], refMode = false; const refBlob = [];
    for (; i < n; i++) {
      const b = blocks[i]; const t = b.text.trim();
      if (!refMode && REFERENCES_START_RE.test(t)) {
        refMode = true;
        const remainder = t.replace(REFERENCES_START_RE, "").trim();
        if (remainder) refBlob.push(remainder);
        continue;
      }
      if (refMode) { refBlob.push(t); continue; }

      const level = (b.level && b.level > 0) ? b.level : looksLikeHeading(t);
      if (level) {
        const sec = { title: stripHeadingNumber(t), level: level, paragraphs: [], children: [] };
        if (level === 1 || !parentStack.length) { paper.sections.push(sec); parentStack = [sec]; }
        else {
          while (parentStack.length && parentStack[parentStack.length - 1].level >= level) parentStack.pop();
          (parentStack.length ? parentStack[parentStack.length - 1].children : paper.sections).push(sec);
          parentStack.push(sec);
        }
        current = sec;
      } else {
        if (!current) { current = { title: "Introduction", level: 1, paragraphs: [], children: [] }; paper.sections.push(current); parentStack = [current]; }
        current.paragraphs.push(t);
      }
    }
    if (refBlob.length) paper.references = splitReferences(refBlob.join("\n"));
    normalizeLevels(paper.sections, 1);

    if (!paper.abstract) paper.warnings.push("No abstract detected.");
    if (!paper.sections.length) paper.warnings.push("No sections detected.");
    if (!paper.references.length) paper.warnings.push("No references detected.");
    return paper;
  }

  // --- readers ---
  function markdownLevel(line) {
    const m = /^(#{1,6})\s+(.*)$/.exec(line);
    return m ? { level: m[1].length, title: m[2].trim() } : null;
  }

  function stripLatex(src) {
    return src
      .replace(/(?<!\\)%.*$/gm, "")
      .replace(/\\(textbf|textit|emph|texttt|section|subsection|title|author)\*?\{([^}]*)\}/g, "$2")
      .replace(/\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?/g, " ")
      .replace(/[{}]/g, " ");
  }

  function textToBlocks(raw, isLatex) {
    if (isLatex) raw = stripLatex(raw);
    const blocks = [];
    for (let chunk of raw.split(/\n\s*\n/)) {
      chunk = chunk.replace(/^\n+|\n+$/g, "");
      if (!chunk.trim()) continue;
      const md = markdownLevel(chunk.trim());
      if (md && !chunk.trim().includes("\n")) { blocks.push({ text: md.title, level: md.level }); continue; }
      const lines = chunk.split("\n");
      const head = markdownLevel(lines[0].trim());
      if (head) {
        blocks.push({ text: head.title, level: head.level });
        const body = lines.slice(1).join("\n").trim();
        if (body) blocks.push({ text: body.replace(/\n/g, " ").trim(), level: 0 });
      } else blocks.push({ text: chunk.replace(/\n/g, " ").trim(), level: 0 });
    }
    return blocks;
  }

  function htmlToBlocks(html) {
    const div = document.createElement("div");
    div.innerHTML = html;
    const blocks = [];
    for (const el of div.children) {
      const text = (el.textContent || "").trim();
      if (!text) continue;
      const tag = el.tagName.toLowerCase();
      const hm = /^h([1-6])$/.exec(tag);
      blocks.push({ text: text, level: hm ? parseInt(hm[1], 10) : 0 });
    }
    if (!blocks.some((b) => b.level)) blocks.forEach((b) => (b.level = 0));
    return blocks;
  }

  async function readFileToPaper(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith(".docx")) {
      const buf = await file.arrayBuffer();
      const res = await mammoth.convertToHtml({ arrayBuffer: buf });
      return buildPaper(htmlToBlocks(res.value));
    }
    const text = await file.text();
    const blocks = textToBlocks(text, name.endsWith(".tex"));
    const paper = buildPaper(blocks);
    if (!paper.title) paper.title = file.name.replace(/\.[^.]+$/, "");
    return paper;
  }

  function extractParagraphs(paper) {
    const out = [];
    if (paper.abstract) out.push(paper.abstract);
    (function walk(secs) {
      for (const s of secs) { s.paragraphs.forEach((p) => out.push(p)); walk(s.children); }
    })(paper.sections);
    return out;
  }

  /* =======================================================================
   * LATEX RENDERER
   * ===================================================================== */
  const TEX_ESCAPES = { "\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "$": "\\$",
    "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}", "~": "\\textasciitilde{}", "^": "\\textasciicircum{}" };
  function texEsc(t) { return (t || "").split("").map((c) => TEX_ESCAPES[c] || c).join(""); }

  function texSections(sections, lines) {
    const cmd = { 1: "section", 2: "subsection", 3: "subsubsection" };
    for (const sec of sections) {
      lines.push("\\" + (cmd[sec.level] || "section") + "{" + texEsc(sec.title) + "}");
      for (const p of sec.paragraphs) { lines.push(texEsc(p)); lines.push(""); }
      if (sec.children.length) texSections(sec.children, lines);
    }
  }

  function renderLatex(paper, publisher) {
    const L = [];
    const bib = (width) => {
      if (!paper.references.length) return;
      L.push("\\begin{thebibliography}{" + width + "}");
      paper.references.forEach((r, i) => L.push("\\bibitem{" + (r.key || "ref" + (i + 1)) + "} " + texEsc(r.raw)));
      L.push("\\end{thebibliography}");
    };
    if (publisher === "ieee") {
      L.push("\\documentclass[conference]{IEEEtran}", "\\IEEEoverridecommandlockouts",
        "\\usepackage{cite,amsmath,amssymb,amsfonts,graphicx,textcomp,xcolor}",
        "\\begin{document}", "\\title{" + texEsc(paper.title) + "}");
      if (paper.authors.length) {
        const blocks = paper.authors.map((a) => {
          let b = "\\IEEEauthorblockN{" + texEsc(a.name) + "}";
          if (a.affiliation) b += "\n\\IEEEauthorblockA{" + texEsc(a.affiliation) + "}";
          return b;
        });
        L.push("\\author{" + blocks.join("\n\\and\n") + "}");
      }
      L.push("\\maketitle");
      if (paper.abstract) L.push("\\begin{abstract}\n" + texEsc(paper.abstract) + "\n\\end{abstract}");
      if (paper.keywords.length) L.push("\\begin{IEEEkeywords}\n" + texEsc(paper.keywords.join(", ")) + "\n\\end{IEEEkeywords}");
      texSections(paper.sections, L); bib("9"); L.push("\\end{document}");
    } else if (publisher === "springer") {
      L.push("\\documentclass[runningheads]{llncs}", "\\usepackage{graphicx,amsmath,amssymb}",
        "\\begin{document}", "\\title{" + texEsc(paper.title) + "}");
      if (paper.authors.length) {
        L.push("\\author{" + paper.authors.map((a) => texEsc(a.name)).join(" \\and ") + "}");
        const affils = [...new Set(paper.authors.map((a) => a.affiliation).filter(Boolean))];
        L.push("\\institute{" + (affils.map(texEsc).join("\\and ") || "Affiliation") + "}");
      }
      L.push("\\maketitle");
      if (paper.abstract) {
        let kw = paper.keywords.length ? "\n\\keywords{" + paper.keywords.map(texEsc).join(" \\and ") + "}" : "";
        L.push("\\begin{abstract}\n" + texEsc(paper.abstract) + kw + "\n\\end{abstract}");
      }
      texSections(paper.sections, L); bib("8"); L.push("\\end{document}");
    } else {
      L.push("\\documentclass[preprint,12pt]{elsarticle}", "\\usepackage{graphicx,amsmath,amssymb,lineno}",
        "\\journal{Journal Name}", "\\begin{document}", "\\begin{frontmatter}",
        "\\title{" + texEsc(paper.title) + "}");
      paper.authors.forEach((a) => { L.push("\\author{" + texEsc(a.name) + "}"); if (a.affiliation) L.push("\\address{" + texEsc(a.affiliation) + "}"); });
      if (paper.abstract) L.push("\\begin{abstract}\n" + texEsc(paper.abstract) + "\n\\end{abstract}");
      if (paper.keywords.length) L.push("\\begin{keyword}\n" + paper.keywords.map(texEsc).join(" \\sep ") + "\n\\end{keyword}");
      L.push("\\end{frontmatter}", "\\linenumbers");
      texSections(paper.sections, L); bib("00"); L.push("\\end{document}");
    }
    return L.join("\n") + "\n";
  }

  /* =======================================================================
   * PDF RENDERER  (print-to-PDF: styled HTML + window.print())
   * ===================================================================== */
  function htmlEsc(t) {
    return (t || "").replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  function pdfSections(sections, numbering, prefix) {
    let html = "";
    sections.forEach((sec, idx) => {
      const num = prefix + (idx + 1);
      if (sec.level === 1) {
        const h = numbering === "roman"
          ? romanize(num) + ".&nbsp;&nbsp;" + htmlEsc(sec.title.toUpperCase())
          : num + "&nbsp;&nbsp;" + htmlEsc(sec.title);
        html += '<h2 class="lvl1">' + h + "</h2>";
      } else {
        html += '<h3 class="lvln">' + num + "&nbsp;&nbsp;" + htmlEsc(sec.title) + "</h3>";
      }
      for (const p of sec.paragraphs) html += '<p class="body">' + htmlEsc(p) + "</p>";
      if (sec.children.length) html += pdfSections(sec.children, numbering, num + ".");
    });
    return html;
  }

  function pdfRefs(refs) {
    if (!refs.length) return "";
    let h = '<h2 class="lvl1 refs-h">REFERENCES</h2><ol class="refs">';
    refs.forEach((r) => (h += "<li>" + htmlEsc(r.raw) + "</li>"));
    return h + "</ol>";
  }

  function renderPdfDoc(paper, publisher, docTitle) {
    const numbering = publisher === "ieee" ? "roman" : "arabic";
    const authors = paper.authors.map((a) => a.name).join(",&nbsp;&nbsp;");
    const affils = [...new Set(paper.authors.map((a) => a.affiliation).filter(Boolean))];

    let css, header, content;
    if (publisher === "ieee") {
      css = `
        @page { size: letter; margin: 0.75in 0.6in; }
        body { font-family:"Times New Roman",Times,serif; font-size:10pt; line-height:1.25; margin:0; }
        .header { text-align:center; margin-bottom:12pt; }
        .title { font-size:20pt; font-weight:bold; margin:0 0 8pt; }
        .authors { font-size:11pt; margin:0 0 2pt; }
        .affil { font-size:10pt; font-style:italic; margin:0 0 2pt; }
        .content { column-count:2; column-gap:0.25in; text-align:justify; }
        .abstract, .keywords { font-style:italic; margin:0 0 6pt; }
        .abstract b, .keywords b { font-weight:bold; font-style:italic; }
        h2.lvl1 { font-size:10pt; font-weight:bold; text-align:center; font-variant:small-caps; margin:8pt 0 4pt; break-after:avoid; }
        h3.lvln { font-size:10pt; font-style:italic; margin:6pt 0 3pt; break-after:avoid; }
        p.body { margin:0 0 6pt; text-indent:0.2in; }
        ol.refs { font-size:9pt; margin:0; padding-left:1.4em; } ol.refs li { margin:0 0 3pt; }
        h2.refs-h { font-variant:normal; }`;
    } else if (publisher === "springer") {
      css = `
        @page { size: A4; margin: 1in 1.2in; }
        body { font-family:"Times New Roman",Times,serif; font-size:10pt; line-height:1.3; margin:0; }
        .header { margin-bottom:10pt; }
        .title { font-size:16pt; font-weight:bold; margin:0 0 8pt; }
        .authors { font-size:11pt; margin:0 0 2pt; }
        .affil { font-size:9pt; font-style:italic; margin:0 0 8pt; }
        .content { text-align:justify; }
        .abstract { font-size:9pt; margin:0 0 4pt 0.4in; padding-right:0.4in; }
        .keywords { font-size:9pt; margin:0 0 10pt 0.4in; }
        h2.lvl1 { font-size:11pt; font-weight:bold; margin:10pt 0 4pt; break-after:avoid; }
        h3.lvln { font-size:10pt; font-weight:bold; font-style:italic; margin:6pt 0 3pt; break-after:avoid; }
        p.body { margin:0 0 6pt; text-indent:0.2in; }
        ol.refs { font-size:9pt; margin:0; padding-left:1.4em; } ol.refs li { margin:0 0 3pt; }`;
    } else {
      css = `
        @page { size: A4; margin: 1in; }
        body { font-family:"Times New Roman",Times,serif; font-size:12pt; line-height:1.4; margin:0; }
        .header { margin-bottom:12pt; }
        .title { font-size:18pt; font-weight:bold; margin:0 0 10pt; }
        .authors { font-size:12pt; margin:0; }
        .affil { font-size:10pt; font-style:italic; margin:0 0 2pt; }
        .abstract { margin:6pt 0; } .abstract b { font-weight:bold; }
        .keywords { margin:0 0 10pt; }
        .content { text-align:justify; }
        h2.lvl1 { font-size:13pt; font-weight:bold; margin:10pt 0 4pt; break-after:avoid; }
        h3.lvln { font-size:12pt; font-weight:bold; margin:6pt 0 3pt; break-after:avoid; }
        p.body { margin:0 0 6pt; }
        ol.refs { font-size:11pt; margin:0; padding-left:1.4em; } ol.refs li { margin:0 0 4pt; }`;
    }

    header = '<div class="header"><p class="title">' + htmlEsc(paper.title) + "</p>";
    if (authors) header += '<p class="authors">' + authors + "</p>";
    affils.forEach((af) => (header += '<p class="affil">' + htmlEsc(af) + "</p>"));
    header += "</div>";

    let body = "";
    if (paper.abstract) {
      const lead = publisher === "ieee" ? "Abstract&mdash;" : (publisher === "springer" ? "Abstract. " : "Abstract<br>");
      body += '<p class="abstract"><b>' + lead + "</b>" + htmlEsc(paper.abstract) + "</p>";
    }
    if (paper.keywords.length) {
      const lead = publisher === "ieee" ? "Index Terms&mdash;" : "Keywords: ";
      body += '<p class="keywords"><b>' + lead + "</b>" + htmlEsc(paper.keywords.join(", ")) + "</p>";
    }
    body += pdfSections(paper.sections, numbering, "");
    body += pdfRefs(paper.references);
    content = '<div class="content">' + body + "</div>";

    return "<!DOCTYPE html><html><head><meta charset='utf-8'><title>" +
      htmlEsc(docTitle) + "</title><style>" + css + "</style></head><body>" +
      header + content +
      "<script>window.onload=function(){setTimeout(function(){window.print();},150);};<\/script>" +
      "</body></html>";
  }

  /* =======================================================================
   * DOCX RENDERER  (docx.js)
   * ===================================================================== */
  function romanize(num) {
    let n = parseInt(String(num).split(".")[0], 10);
    if (isNaN(n)) return String(num);
    const map = [[1000,"M"],[900,"CM"],[500,"D"],[400,"CD"],[100,"C"],[90,"XC"],
      [50,"L"],[40,"XL"],[10,"X"],[9,"IX"],[5,"V"],[4,"IV"],[1,"I"]];
    let out = "";
    for (const [v, s] of map) while (n >= v) { out += s; n -= v; }
    return out;
  }

  function buildDocx(paper, publisher) {
    const D = window.docx;
    const { Document, Packer, Paragraph, TextRun, AlignmentType, SectionType, convertInchesToTwip } = D;
    const FONT = "Times New Roman";

    function para(text, o) {
      o = o || {};
      return new Paragraph({
        alignment: o.align,
        spacing: { after: (o.after != null ? o.after : 6) * 20, before: 0 },
        indent: o.indent,
        children: [new TextRun({ text: text, bold: !!o.bold, italics: !!o.italic,
          size: (o.size || 10) * 2, font: FONT, color: o.color })],
      });
    }

    function refPara(i, raw, size) {
      return new Paragraph({
        spacing: { after: 3 * 20 },
        indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.25) },
        children: [new TextRun({ text: "[" + i + "] " + raw, size: size * 2, font: FONT })],
      });
    }

    function writeSections(sections, bodySize, numbering, prefix, out) {
      sections.forEach((sec, idx) => {
        const num = prefix + (idx + 1);
        if (sec.level === 1) {
          const h = numbering === "roman" ? romanize(num) + ".  " + sec.title.toUpperCase() : num + "  " + sec.title;
          out.push(para(h, { size: bodySize + 1, bold: true, after: 4 }));
        } else {
          out.push(para(num + "  " + sec.title, { size: bodySize, bold: true, italic: true, after: 3 }));
        }
        for (const p of sec.paragraphs)
          out.push(para(p, { size: bodySize, align: AlignmentType.JUSTIFIED, after: 6,
            indent: { firstLine: convertInchesToTwip(0.2) } }));
        if (sec.children.length) writeSections(sec.children, bodySize, numbering, num + ".", out);
      });
    }

    function refs(out, size) {
      if (!paper.references.length) return;
      out.push(para("REFERENCES", { size: size + 1, bold: true, after: 4 }));
      paper.references.forEach((r, i) => out.push(refPara(i + 1, r.raw, size)));
    }

    let sections;
    if (publisher === "ieee") {
      const titleBlock = [];
      titleBlock.push(para(paper.title, { size: 24, align: AlignmentType.CENTER, after: 8 }));
      if (paper.authors.length) {
        titleBlock.push(para(paper.authors.map((a) => a.name).join(",  "), { size: 11, align: AlignmentType.CENTER, after: 2 }));
        [...new Set(paper.authors.map((a) => a.affiliation).filter(Boolean))]
          .forEach((af) => titleBlock.push(para(af, { size: 10, italic: true, align: AlignmentType.CENTER, after: 2 })));
      }
      const body = [];
      if (paper.abstract) body.push(new Paragraph({ spacing: { after: 120 }, children: [
        new TextRun({ text: "Abstract—", bold: true, italics: true, size: 18, font: FONT }),
        new TextRun({ text: paper.abstract, italics: true, size: 18, font: FONT })] }));
      if (paper.keywords.length) body.push(new Paragraph({ children: [
        new TextRun({ text: "Index Terms—", bold: true, italics: true, size: 18, font: FONT }),
        new TextRun({ text: paper.keywords.join(", "), italics: true, size: 18, font: FONT })] }));
      writeSections(paper.sections, 10, "roman", "", body);
      refs(body, 9);
      const margin = { top: 1080, bottom: 1080, left: 900, right: 900 };
      sections = [
        { properties: { page: { size: { width: 12240, height: 15840 }, margin: margin } }, children: titleBlock },
        { properties: { type: SectionType.CONTINUOUS, column: { count: 2, space: 360 }, page: { margin: margin } }, children: body },
      ];
    } else if (publisher === "springer") {
      const out = [];
      out.push(para(paper.title, { size: 16, bold: true, after: 8 }));
      if (paper.authors.length) {
        out.push(para(paper.authors.map((a) => a.name).join(" and "), { size: 11, after: 2 }));
        [...new Set(paper.authors.map((a) => a.affiliation).filter(Boolean))]
          .forEach((af) => out.push(para(af, { size: 9, italic: true, after: 8 })));
      }
      if (paper.abstract) {
        out.push(para("Abstract.", { size: 9, bold: true, after: 0 }));
        out.push(para(paper.abstract, { size: 9, align: AlignmentType.JUSTIFIED, after: 4,
          indent: { left: convertInchesToTwip(0.4), right: convertInchesToTwip(0.4) } }));
      }
      if (paper.keywords.length)
        out.push(para("Keywords: " + paper.keywords.join(" · "), { size: 9, after: 10,
          indent: { left: convertInchesToTwip(0.4), right: convertInchesToTwip(0.4) } }));
      writeSections(paper.sections, 10, "arabic", "", out);
      refs(out, 9);
      sections = [{ properties: { page: { margin: { top: 1440, bottom: 1440, left: 1728, right: 1728 } } }, children: out }];
    } else {
      const out = [];
      out.push(para(paper.title, { size: 18, bold: true, after: 10 }));
      paper.authors.forEach((a) => {
        out.push(para(a.name, { size: 12, after: 0 }));
        if (a.affiliation) out.push(para(a.affiliation, { size: 10, italic: true, after: 2 }));
      });
      if (paper.abstract) { out.push(para("Abstract", { size: 12, bold: true, after: 2 }));
        out.push(para(paper.abstract, { size: 11, align: AlignmentType.JUSTIFIED, after: 6 })); }
      if (paper.keywords.length) out.push(para("Keywords: " + paper.keywords.join(", "), { size: 11, after: 10 }));
      writeSections(paper.sections, 12, "arabic", "", out);
      refs(out, 11);
      sections = [{ properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: out }];
    }

    const doc = new Document({ sections: sections });
    return Packer.toBlob(doc);
  }

  /* =======================================================================
   * UI
   * ===================================================================== */
  function $(id) { return document.getElementById(id); }

  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click();
    document.body.removeChild(a); setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  // tabs
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      $(btn.dataset.tab).classList.add("active");
    });
  });

  // ---- converter ----
  let convPaper = null;

  async function getConvPaper() {
    const file = $("conv-file").files[0];
    if (file) return await readFileToPaper(file);
    const text = $("conv-text").value.trim();
    if (text) { const p = buildPaper(textToBlocks(text, false)); if (!p.title) p.title = "paper"; return p; }
    return null;
  }

  function publisher() { return document.querySelector('input[name="pub"]:checked').value; }
  function convStatus(msg, cls) { const el = $("conv-status"); el.textContent = msg; el.className = "status " + (cls || ""); }

  function paperStem(paper) {
    const file = $("conv-file").files[0];
    let stem = file ? file.name.replace(/\.[^.]+$/, "") : (paper.title || "paper");
    return stem.replace(/[^\w.-]+/g, "_").slice(0, 60) || "paper";
  }

  $("btn-tex").addEventListener("click", async () => {
    try {
      convStatus("Parsing…");
      const paper = await getConvPaper();
      if (!paper) { convStatus("Add a file or paste some text first.", "warn"); return; }
      const tex = renderLatex(paper, publisher());
      download(new Blob([tex], { type: "text/x-tex" }), paperStem(paper) + "_" + publisher() + ".tex");
      convStatus("LaTeX ready. " + summary(paper), "ok");
    } catch (e) { convStatus("Error: " + e.message, "warn"); console.error(e); }
  });

  $("btn-docx").addEventListener("click", async () => {
    try {
      convStatus("Parsing & building Word file…");
      const paper = await getConvPaper();
      if (!paper) { convStatus("Add a file or paste some text first.", "warn"); return; }
      const blob = await buildDocx(paper, publisher());
      download(blob, paperStem(paper) + "_" + publisher() + ".docx");
      convStatus("Word file ready. " + summary(paper), "ok");
    } catch (e) { convStatus("Error: " + e.message, "warn"); console.error(e); }
  });

  $("btn-pdf").addEventListener("click", async () => {
    try {
      convStatus("Parsing & preparing PDF…");
      const paper = await getConvPaper();
      if (!paper) { convStatus("Add a file or paste some text first.", "warn"); return; }
      const name = paperStem(paper) + "_" + publisher();
      const html = renderPdfDoc(paper, publisher(), name);
      const w = window.open("", "_blank");
      if (!w) { convStatus("Pop-up blocked — allow pop-ups for this site to export PDF.", "warn"); return; }
      w.document.open(); w.document.write(html); w.document.close();
      convStatus('PDF ready — choose "Save as PDF" in the print dialog. ' + summary(paper), "ok");
    } catch (e) { convStatus("Error: " + e.message, "warn"); console.error(e); }
  });

  function summary(p) {
    let s = "Authors: " + p.authors.length + ", sections: " + p.sections.length + ", refs: " + p.references.length + ".";
    if (p.warnings.length) s += " Note: " + p.warnings[0];
    return s;
  }

  // ---- humanizer ----
  let humParagraphs = [];

  $("hum-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const paper = await readFileToPaper(file);
      humParagraphs = extractParagraphs(paper);
      const sel = $("hum-para");
      sel.innerHTML = "";
      const optAll = document.createElement("option");
      optAll.value = "all"; optAll.textContent = "All paragraphs";
      sel.appendChild(optAll);
      humParagraphs.forEach((p, idx) => {
        const o = document.createElement("option");
        o.value = String(idx); o.textContent = "Para " + (idx + 1) + ": " + p.slice(0, 50) + "…";
        sel.appendChild(o);
      });
      sel.classList.remove("hidden");
      showSelectedPara();
    } catch (err) { alert("Could not read file: " + err.message); }
  });

  function showSelectedPara() {
    const sel = $("hum-para");
    if (sel.classList.contains("hidden") || !humParagraphs.length) return;
    const v = sel.value;
    $("hum-input").value = v === "all" ? humParagraphs.join("\n\n") : (humParagraphs[parseInt(v, 10)] || "");
  }
  $("hum-para").addEventListener("change", showSelectedPara);

  function humOptions() {
    return { vocab: $("opt-vocab").checked, filler: $("opt-filler").checked,
      contractions: $("opt-contractions").checked, split: $("opt-split").checked };
  }
  document.querySelectorAll('input[name="level"]').forEach((r) =>
    r.addEventListener("change", () => {
      const o = optionsForLevel(r.value);
      $("opt-vocab").checked = o.vocab; $("opt-filler").checked = o.filler;
      $("opt-contractions").checked = o.contractions; $("opt-split").checked = o.split;
    }));

  $("btn-humanize").addEventListener("click", () => {
    const text = $("hum-input").value.trim();
    if (!text) { alert("Enter or load some text first."); return; }
    const level = document.querySelector('input[name="level"]:checked').value;
    const res = humanizeText(text, level, humOptions());
    $("hum-output").value = res.text;
    $("hum-count").textContent = "(" + res.changes + " change" + (res.changes === 1 ? "" : "s") + ")";
  });

  $("btn-copy").addEventListener("click", async () => {
    const t = $("hum-output").value;
    if (!t) return;
    try { await navigator.clipboard.writeText(t); $("btn-copy").textContent = "Copied!"; setTimeout(() => ($("btn-copy").textContent = "Copy"), 1200); }
    catch (e) { $("hum-output").select(); document.execCommand("copy"); }
  });

  $("btn-save-txt").addEventListener("click", () => {
    const t = $("hum-output").value;
    if (!t) { alert("Run Humanize first."); return; }
    download(new Blob([t], { type: "text/plain" }), "humanized.txt");
  });

  // expose for quick console/testing
  window.PaperForge = { humanizeText, buildPaper, textToBlocks, renderLatex, optionsForLevel };
})();
