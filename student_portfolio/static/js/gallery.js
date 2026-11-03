(function () {
  const grid = $("#grid");
  const state = { page: 1, skill: "" };
  const PER_PAGE = 12;

  function card(s) {
    const chips = s.skills.map((k) => `<span class="chip">${esc(k)}</span>`).join("");
    const photo = s.has_photo
      ? `<img src="/photo/${esc(s.id)}?v=${Number(s.updated_at) || 0}" alt="">`
      : `<span class="avatar" style="--h:${hue(s.name)}">${esc(initials(s.name))}</span>`;
    const n = s.project_count;
    return `<div class="col-sm-6 col-lg-4"><a class="id-card" href="/p/${esc(s.id)}">
      <div class="id-top"></div>
      <div class="id-photo">${photo}</div>
      <div class="id-body">
        <h2 class="id-name">${esc(s.name)}</h2>
        <p class="id-dept">${esc(s.department)}, year ${Number(s.year)}</p>
        <div class="chips">${chips || '<span class="text-muted small">No skills listed yet</span>'}</div>
      </div>
      <div class="id-foot"><span>${n} ${n === 1 ? "project" : "projects"}</span><span>View portfolio</span></div>
    </a></div>`;
  }

  function renderSkillPill() {
    const box = $("#active-skill");
    if (!state.skill) { box.innerHTML = ""; return; }
    box.innerHTML = `<span class="filter-pill">Skill: ${esc(state.skill)}
      <button type="button" aria-label="Clear skill filter">&times;</button></span>`;
    $("button", box).addEventListener("click", () => { state.skill = ""; state.page = 1; load(); });
  }

  async function load() {
    const params = new URLSearchParams({
      q: $("#q").value.trim(), department: $("#dept").value, year: $("#year").value,
      skill: state.skill, sort: $("#sort").value, page: state.page, per_page: PER_PAGE,
    });
    renderSkillPill();
    try {
      const data = await api("/api/public/students?" + params);
      $("#count").textContent = data.total === 1 ? "1 portfolio" : `${data.total} portfolios`;
      if (!data.items.length) {
        grid.innerHTML = `<div class="col-12"><div class="panel text-center py-5">
          <p class="mb-1"><strong>No portfolios match.</strong></p>
          <p class="text-muted mb-0">Try a different skill or clear the filters.</p></div></div>`;
      } else {
        grid.innerHTML = data.items.map(card).join("");
      }
      renderPager($("#pager"), data.page, data.total, data.per_page, (p) => {
        state.page = p; load(); window.scrollTo({ top: 0, behavior: "smooth" });
      });
    } catch (e) {
      grid.innerHTML = `<div class="col-12"><div class="alert alert-danger">${esc(e.message)}</div></div>`;
    }
  }

  const reload = () => { state.page = 1; load(); };
  $("#q").addEventListener("input", debounce(reload, 250));
  ["#dept", "#year", "#sort"].forEach((id) => $(id).addEventListener("change", reload));
  $("#finder").addEventListener("submit", (e) => { e.preventDefault(); reload(); });
  load();
})();
