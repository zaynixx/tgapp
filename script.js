// Обработка кнопок
document.getElementById("search-tor").addEventListener("click", () => {
  const query = document.getElementById("search").value;
  if (query) {
    window.open(`/search?query=${encodeURIComponent(query)}`, "_blank");
  } else {
    alert("Введите запрос для поиска.");
  }
});

document.getElementById("open-tiktok").addEventListener("click", () => {
  window.open("/redirect/tiktok", "_blank");
});

document.getElementById("open-instagram").addEventListener("click", () => {
  window.location.assign("/redirect/instagram", "_blank");
});

document.getElementById("open-2ip-tor").addEventListener("click", () => {
  window.open("/redirect/2ip", "_blank"); // Перенаправление на 2ip через TOR
});

document.getElementById("open-2ip-vpn").addEventListener("click", () => {
  window.open("/open_2ip_vpn", "_blank"); // Перенаправление на 2ip через VPN
});
