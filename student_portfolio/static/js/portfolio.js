(function () {
  const btn = $("#pdf-btn");
  const sheet = $("#portfolio-sheet");
  if (!btn || !sheet) return;

  btn.addEventListener("click", () => {
    if (!window.html2pdf) {
      // PDF library blocked or offline: fall back to the browser's print dialog (Save as PDF).
      window.print();
      return;
    }
    const name = (sheet.dataset.name || "portfolio").replace(/[^\w\- ]+/g, "").trim().replace(/\s+/g, "-");
    btn.disabled = true;
    html2pdf()
      .set({
        margin: [10, 10, 10, 10],
        filename: `${name}-portfolio.pdf`,
        image: { type: "jpeg", quality: 0.96 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["css", "legacy"], avoid: [".project", ".sheet-section h2"] },
      })
      .from(sheet)
      .save()
      .catch(() => toast("Could not create the PDF. Use your browser's print dialog instead.", "danger"))
      .finally(() => { btn.disabled = false; });
  });
})();
