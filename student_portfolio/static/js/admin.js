(function () {
  const PALETTE = ["#2347ff", "#0e1b2c", "#f2b705", "#e4572e", "#2a9d8f", "#7b61ff", "#8d99ae", "#c77dff", "#6c757d"];
  const state = { page: 1, deleteId: null };
  const PER_PAGE = 10;
  const modal = new bootstrap.Modal($("#delete-modal"));

  // ---------------------------------------------------------------- stats + charts
  function chart(id, config) {
    if (!window.Chart) { $(id).parentElement.innerHTML = '<p class="text-muted small">Charts need an internet connection to load.</p>'; return; }
    new Chart($(id), config);
  }

  async function loadStats() {
    try {
      const s = await api("/api/admin/stats");
      $("#st-total").textContent = s.total;
      $("#st-public").textContent = s.public;
      $("#st-depts").textContent = s.by_department.length;
      $("#st-projects").textContent = s.projects;

      chart("#chart-dept", {
        type: "bar",
        data: { labels: s.by_department.map((d) => d.label), datasets: [{ data: s.by_department.map((d) => d.count), backgroundColor: PALETTE[0], borderRadius: 4 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
      chart("#chart-skills", {
        type: "bar",
        data: { labels: s.top_skills.map((d) => d.label), datasets: [{ data: s.top_skills.map((d) => d.count), backgroundColor: "#f2b705", borderRadius: 4 }] },
        options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
      chart("#chart-year", {
        type: "doughnut",
        data: { labels: s.by_year.map((d) => d.label), datasets: [{ data: s.by_year.map((d) => d.count), backgroundColor: PALETTE.slice(0, 4), borderWidth: 0 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
      });
    } catch (e) { toast(e.message, "danger"); }
  }

  // ---------------------------------------------------------------- table
  function row(s) {
    return `<tr>
      <td><div class="d-flex align-items-center gap-2">${avatarHtml(s)}
        <div><div class="fw-semibold">${esc(s.name)}</div><div class="small text-muted">${esc(s.email)}</div></div></div></td>
      <td>${esc(s.usn)}</td>
      <td>${esc(s.department)}, Y${Number(s.year)}</td>
      <td class="text-center">${s.skill_count}</td>
      <td class="text-center">${s.project_count}</td>
      <td><div class="form-check form-switch mb-0"><input class="form-check-input" type="checkbox" role="switch"
          data-vis="${esc(s.id)}" ${s.is_public ? "checked" : ""} aria-label="Public portfolio for ${esc(s.name)}"></div></td>
      <td class="text-end text-nowrap">
        <a class="btn btn-sm btn-outline-dark" href="/p/${esc(s.id)}">View</a>
        <a class="btn btn-sm btn-outline-dark" href="/dashboard?id=${esc(s.id)}">Edit</a>
        <button class="btn btn-sm btn-outline-danger" type="button" data-del="${esc(s.id)}" data-name="${esc(s.name)}">Delete</button>
      </td></tr>`;
  }

  async function loadRows() {
    const params = new URLSearchParams({
      q: $("#q").value.trim(), department: $("#dept").value, year: $("#year").value,
      visibility: $("#visibility").value, sort: $("#sort").value, page: state.page, per_page: PER_PAGE,
    });
    try {
      const data = await api("/api/admin/students?" + params);
      $("#rows").innerHTML = data.items.map(row).join("");
      $("#empty").classList.toggle("d-none", data.items.length > 0);
      $("#count").textContent = data.total === 1 ? "1 student" : `${data.total} students`;
      renderPager($("#pager"), data.page, data.total, data.per_page, (p) => { state.page = p; loadRows(); });

      $$("[data-vis]").forEach((box) => box.addEventListener("change", async () => {
        try {
          await api(`/api/admin/students/${box.dataset.vis}/visibility`, { method: "PATCH", body: { is_public: box.checked } });
          toast(box.checked ? "Portfolio is now public" : "Portfolio is now private");
          loadStats_refresh();
        } catch (e) { box.checked = !box.checked; toast(e.message, "danger"); }
      }));
      $$("[data-del]").forEach((b) => b.addEventListener("click", () => {
        state.deleteId = b.dataset.del;
        $("#delete-name").textContent = b.dataset.name;
        modal.show();
      }));
    } catch (e) {
      if (e.status === 401 || e.status === 403) { window.location.href = "/login"; return; }
      toast(e.message, "danger");
    }
  }

  // public count changes when visibility is toggled; the charts do not, so just refresh the number
  async function loadStats_refresh() {
    try { const s = await api("/api/admin/stats"); $("#st-public").textContent = s.public; } catch (e) { /* ignore */ }
  }

  $("#delete-confirm").addEventListener("click", async () => {
    try {
      await api(`/api/admin/students/${state.deleteId}`, { method: "DELETE" });
      modal.hide();
      toast("Student deleted");
      loadRows(); loadStats_refresh();
    } catch (e) { toast(e.message, "danger"); }
  });

  const reload = () => { state.page = 1; loadRows(); };
  $("#q").addEventListener("input", debounce(reload, 250));
  ["#dept", "#year", "#visibility", "#sort"].forEach((id) => $(id).addEventListener("change", reload));
  $("#filters").addEventListener("submit", (e) => { e.preventDefault(); reload(); });

  loadStats();
  loadRows();
})();
