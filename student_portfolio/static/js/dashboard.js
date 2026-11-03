(function () {
  const root = $("#dash");
  if (!root) return;
  const sid = root.dataset.studentId;
  $("#copy-link").dataset.path = "/p/" + sid;

  const f = {
    name: $("#f-name"), usn: $("#f-usn"), department: $("#f-department"), year: $("#f-year"),
    about: $("#f-about"), github: $("#f-github"), linkedin: $("#f-linkedin"),
    website: $("#f-website"), isPublic: $("#f-public"),
  };
  // Editable lists live here. Text-like values are kept as strings while editing.
  const data = { skills: [], projects: [], certs: [], achievements: [] };
  let student = null;
  let dirty = false;

  const SUGGESTED = ["Python", "Java", "JavaScript", "React", "SQL", "Git", "HTML", "CSS",
    "C++", "Machine Learning", "Node.js", "Flask", "Docker", "Data Structures"];

  const splitList = (text) => String(text).split(",").map((t) => t.trim()).filter(Boolean);
  const markDirty = () => {
    dirty = true;
    $("#save-state").textContent = "You have unsaved changes";
    updateMeter();
  };

  // ------------------------------------------------------------ skills
  function renderSkills() {
    $("#skills-chips").innerHTML = data.skills.map((s, i) =>
      `<span class="chip">${esc(s)}<button type="button" class="x" data-i="${i}" aria-label="Remove ${esc(s)}">&times;</button></span>`
    ).join("");
    $$("#skills-chips .x").forEach((b) => b.addEventListener("click", () => {
      data.skills.splice(Number(b.dataset.i), 1); renderSkills(); markDirty();
    }));
    const lower = data.skills.map((s) => s.toLowerCase());
    $("#skill-suggest").innerHTML = SUGGESTED.filter((s) => !lower.includes(s.toLowerCase())).slice(0, 10)
      .map((s) => `<button type="button" class="chip chip-quiet chip-btn" data-skill="${esc(s)}">+ ${esc(s)}</button>`).join("");
    $$("#skill-suggest [data-skill]").forEach((b) => b.addEventListener("click", () => addSkill(b.dataset.skill)));
  }

  function addSkill(raw) {
    const skill = String(raw).replace(/,/g, " ").replace(/\s+/g, " ").trim();
    if (!skill) return;
    if (data.skills.length >= 30) { toast("You can add up to 30 skills", "danger"); return; }
    if (data.skills.some((s) => s.toLowerCase() === skill.toLowerCase())) return;
    data.skills.push(skill.slice(0, 40));
    renderSkills(); markDirty();
  }

  const skillInput = $("#skill-input");
  skillInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault(); addSkill(skillInput.value); skillInput.value = "";
    } else if (e.key === "Backspace" && !skillInput.value && data.skills.length) {
      data.skills.pop(); renderSkills(); markDirty();
    }
  });
  skillInput.addEventListener("blur", () => { addSkill(skillInput.value); skillInput.value = ""; });

  // ------------------------------------------------------------ repeating blocks
  // spec.fields: [{key, label, kind: "text"|"textarea"|"number", max, hint}]
  function makeRepeater(boxId, listKey, spec) {
    const box = $(boxId);
    function render() {
      const list = data[listKey];
      if (!list.length) {
        box.innerHTML = `<p class="empty-hint">${esc(spec.empty)}</p>`;
        return;
      }
      box.innerHTML = "";
      list.forEach((item, i) => {
        const el = document.createElement("div");
        el.className = "repeat-item";
        el.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-2">
            <strong>${esc(spec.noun)} ${i + 1}</strong>
            <button type="button" class="btn btn-sm btn-link text-danger p-0" data-remove>Remove</button></div>
          <div class="row g-2">${spec.fields.map((fd) => `
            <div class="${fd.col || "col-12"}">
              <label class="form-label small">${esc(fd.label)}</label>
              ${fd.kind === "textarea"
                ? `<textarea class="form-control" rows="3" data-k="${fd.key}" data-path="${spec.path}.${i}.${fd.pathKey || fd.key}" maxlength="${fd.max}"></textarea>`
                : `<input class="form-control" data-k="${fd.key}" data-path="${spec.path}.${i}.${fd.pathKey || fd.key}" maxlength="${fd.max}" ${fd.kind === "number" ? 'inputmode="numeric"' : ""}>`}
              <div class="invalid-feedback"></div>
            </div>`).join("")}</div>`;
        $$("[data-k]", el).forEach((input) => { input.value = item[input.dataset.k] ?? ""; });
        el.addEventListener("input", (e) => {
          const k = e.target.dataset.k;
          if (!k) return;
          item[k] = e.target.value; e.target.classList.remove("is-invalid"); markDirty();
        });
        $("[data-remove]", el).addEventListener("click", () => { list.splice(i, 1); render(); markDirty(); });
        box.appendChild(el);
      });
    }
    return { render, add() { data[listKey].push(spec.blank()); render(); markDirty(); } };
  }

  const projects = makeRepeater("#projects", "projects", {
    noun: "Project", path: "projects", empty: "No projects yet. Add your best one first.",
    blank: () => ({ title: "", description: "", tech: "", link: "" }),
    fields: [
      { key: "title", label: "Title", max: 100 },
      { key: "description", label: "What it does and what you built", kind: "textarea", max: 500 },
      { key: "tech", label: "Technologies (comma separated)", max: 200, col: "col-md-6" },
      { key: "link", label: "Link (GitHub or demo)", max: 300, col: "col-md-6" },
    ],
  });
  const certs = makeRepeater("#certs", "certs", {
    noun: "Certification", path: "certifications", empty: "No certifications yet.",
    blank: () => ({ name: "", issuer: "", year: "", link: "" }),
    fields: [
      { key: "name", label: "Certification name", max: 100, col: "col-md-6" },
      { key: "issuer", label: "Issued by", max: 100, col: "col-md-4" },
      { key: "year", label: "Year", max: 4, col: "col-md-2" },
      { key: "link", label: "Certificate link (optional)", max: 300 },
    ],
  });
  const ach = makeRepeater("#achievements", "achievements", {
    noun: "Achievement", path: "achievements", empty: "No achievements yet.",
    blank: () => ({ text: "" }),
    fields: [{ key: "text", pathKey: "", label: "What you achieved", max: 200 }],
  });
  // achievements are plain strings on the server, so their error path is "achievements.<i>"
  const origAchRender = ach.render;
  ach.render = function () {
    origAchRender();
    $$("#achievements [data-path]").forEach((el) => {
      el.dataset.path = el.dataset.path.replace(/\.text$/, "");
    });
  };
  const achRepeater = { render: ach.render, add: ach.add };

  $("#add-project").addEventListener("click", () => projects.add());
  $("#add-cert").addEventListener("click", () => certs.add());
  $("#add-ach").addEventListener("click", () => {
    data.achievements.push({ text: "" }); achRepeater.render(); markDirty();
  });

  // ------------------------------------------------------------ photo
  function renderPhoto() {
    const box = $("#photo-box");
    box.innerHTML = student.has_photo
      ? `<img src="/photo/${esc(sid)}?v=${Number(student.updated_at) || 0}" alt="Your profile photo">`
      : `<span class="avatar" style="--h:${hue(f.name.value)}">${esc(initials(f.name.value))}</span>`;
    $("#photo-remove").classList.toggle("d-none", !student.has_photo);
  }

  $("#photo-pick").addEventListener("click", () => $("#photo-input").click());
  $("#photo-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { toast("Choose a photo under 2 MB", "danger"); return; }
    const form = new FormData();
    form.append("photo", file);
    try {
      const res = await api(`/api/students/${sid}/photo`, { method: "POST", form });
      student.has_photo = true; student.updated_at = res.updated_at;
      renderPhoto(); updateMeter(); toast("Photo updated");
    } catch (err) { toast(err.message, "danger"); }
  });
  $("#photo-remove").addEventListener("click", async () => {
    try {
      const res = await api(`/api/students/${sid}/photo`, { method: "DELETE" });
      student.has_photo = false; student.updated_at = res.updated_at;
      renderPhoto(); updateMeter(); toast("Photo removed");
    } catch (err) { toast(err.message, "danger"); }
  });

  // ------------------------------------------------------------ profile strength
  function updateMeter() {
    const filled = (list, key) => list.some((x) => String(x[key] || "").trim());
    const checks = [
      ["a profile photo", student && student.has_photo, 10],
      ["a short bio (50+ characters)", f.about.value.trim().length >= 50, 15],
      ["at least 5 skills", data.skills.length >= 5, 15],
      ["a project", filled(data.projects, "title"), 20],
      ["a certification", filled(data.certs, "name"), 10],
      ["an achievement", filled(data.achievements, "text"), 10],
      ["your GitHub link", f.github.value.trim(), 10],
      ["your LinkedIn link", f.linkedin.value.trim(), 10],
    ];
    const score = checks.reduce((sum, [, ok, pts]) => sum + (ok ? pts : 0), 0);
    $("#meter-bar").style.width = score + "%";
    $("#meter-text").textContent = score + "%";
    $("#meter-tips").innerHTML = checks.filter(([, ok]) => !ok).slice(0, 4)
      .map(([label]) => `<li>Add ${esc(label)}</li>`).join("");
  }

  // ------------------------------------------------------------ load / save
  function populate(s) {
    student = s;
    f.name.value = s.name; f.usn.value = s.usn || ""; f.department.value = s.department;
    f.year.value = String(s.year); f.about.value = s.about || "";
    f.github.value = s.links.github || ""; f.linkedin.value = s.links.linkedin || "";
    f.website.value = s.links.website || ""; f.isPublic.checked = !!s.is_public;
    data.skills = [...(s.skills || [])];
    data.projects = (s.projects || []).map((p) => ({ ...p, tech: (p.tech || []).join(", ") }));
    data.certs = (s.certifications || []).map((c) => ({ ...c, year: c.year ?? "" }));
    data.achievements = (s.achievements || []).map((text) => ({ text }));
    $("#about-count").textContent = f.about.value.length;
    renderSkills(); projects.render(); certs.render(); achRepeater.render(); renderPhoto(); updateMeter();
  }

  function prune() {
    const blank = (obj) => Object.values(obj).every((v) => !String(v).trim());
    data.projects = data.projects.filter((x) => !blank(x));
    data.certs = data.certs.filter((x) => !blank(x));
    data.achievements = data.achievements.filter((x) => x.text.trim());
    projects.render(); certs.render(); achRepeater.render();
  }

  function collect() {
    return {
      name: f.name.value, usn: f.usn.value, department: f.department.value, year: Number(f.year.value),
      about: f.about.value, skills: data.skills,
      projects: data.projects.map((p) => ({ title: p.title, description: p.description, tech: splitList(p.tech), link: p.link })),
      certifications: data.certs.map((c) => ({
        name: c.name, issuer: c.issuer, link: c.link,
        year: String(c.year).trim() === "" ? null : Number(c.year),
      })),
      achievements: data.achievements.map((a) => a.text),
      links: { github: f.github.value, linkedin: f.linkedin.value, website: f.website.value },
      is_public: f.isPublic.checked,
    };
  }

  function prettyPath(path) {
    const parts = path.split(".");
    const names = { projects: "Project", certifications: "Certification", achievements: "Achievement", links: "Link" };
    if (parts.length >= 2 && /^\d+$/.test(parts[1])) {
      const rest = parts[2] ? ` ${parts[2]}` : "";
      return `${names[parts[0]] || parts[0]} ${Number(parts[1]) + 1}${rest}`;
    }
    return parts.map((p) => names[p] || p).join(" ");
  }

  function clearErrors() {
    $$(".is-invalid", root).forEach((el) => el.classList.remove("is-invalid"));
    $("#error-box").classList.add("d-none");
  }

  function showErrors(message, fields) {
    const entries = Object.entries(fields || {});
    entries.forEach(([path, msg]) => {
      const el = root.querySelector(`[data-path="${path}"]`);
      if (!el) return;
      el.classList.add("is-invalid");
      const fb = el.parentElement.querySelector(".invalid-feedback");
      if (fb) { fb.textContent = msg; fb.style.display = "block"; }
    });
    const box = $("#error-box");
    box.innerHTML = `<strong>${esc(message)}</strong>` + (entries.length
      ? `<ul class="mb-0 mt-1">${entries.slice(0, 6).map(([p, m]) => `<li>${esc(prettyPath(p))}: ${esc(m)}</li>`).join("")}</ul>` : "");
    box.classList.remove("d-none");
    box.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function save(e) {
    if (e) e.preventDefault();
    clearErrors(); prune();
    const btn = $("#save-btn");
    btn.disabled = true;
    try {
      const saved = await api(`/api/students/${sid}`, { method: "PUT", body: collect() });
      populate(saved);
      dirty = false;
      $("#save-state").textContent = "All changes saved";
      toast("Portfolio saved");
    } catch (err) {
      if (err.status === 401) { window.location.href = "/login"; return; }
      showErrors(err.message, err.fields);
    } finally { btn.disabled = false; }
  }

  $("#portfolio-form").addEventListener("submit", save);
  ["name", "usn", "department", "year", "about", "github", "linkedin", "website"].forEach((k) =>
    f[k].addEventListener("input", () => {
      f[k].classList.remove("is-invalid");
      if (k === "about") $("#about-count").textContent = f.about.value.length;
      if (k === "name" && !student.has_photo) renderPhoto();
      markDirty();
    }));
  f.isPublic.addEventListener("change", markDirty);
  window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });

  api(`/api/students/${sid}`)
    .then(populate)
    .catch((err) => {
      if (err.status === 401) { window.location.href = "/login"; return; }
      showErrors(err.message);
    });
})();
