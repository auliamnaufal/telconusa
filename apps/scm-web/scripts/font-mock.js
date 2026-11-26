// Jawaban Google Fonts palsu agar `next build` dan `next dev` jalan di Next 15.1.6.
// Pemuat font Next versi ini gagal mengurai CSS Google Fonts yang sekarang (galat
// "Cannot read properties of null (reading '1')"). Hanya untuk verifikasi lokal; jangan dipakai di produksi.
const css = (family, weight) =>
  `@font-face { font-family: '${family}'; font-style: normal; font-weight: ${weight}; src: url(https://fonts.gstatic.com/s/mock/v1/mock.woff2) format('woff2'); unicode-range: U+0000-00FF; }`;

module.exports = {
  "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&display=swap": css("Plus Jakarta Sans", "600 800"),
  "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap": css("Inter", "400 700"),
  "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap": css("JetBrains Mono", "400 600"),
};
