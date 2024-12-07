document.getElementById("telegram-login").addEventListener("click", () => {
  fetch("/telegram/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      initData: window.Telegram.WebApp.initData,
    }),
  }).then((res) => {
    if (res.ok) {
      window.location.assign(data.url);
    } else {
      toaster.show('Что-то пошло не так', { className: "toast-error" });
    }
  });
});
