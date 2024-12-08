let loggedIn;

const getUser = () => {
  return JSON.parse(sessionStorage.getItem("user"));
};

let toaster = new Toast({});

fetch("/me", {
  method: "GET",
})
  .then((response) => response.json())
  .then((data) => {
    if (data.username) {
      loggedIn = true;
      sessionStorage.setItem("user", JSON.stringify(data));
    }
  })
  .catch((error) => {
    sessionStorage.removeItem("user");
    loggedIn = false;
    console.log(error);
  });

const closeLogin = () => {
  const wrapper = document.getElementById("login-drawer");
  const drawer = wrapper.querySelector("div");

  wrapper.style.backdropFilter = "blur(0px)";
  wrapper.style.opacity = 0;
  drawer.style.transform = "translateY(100%)";

  setTimeout(() => {
    wrapper.style.display = "none";
    wrapper.style.backdropFilter = "";
    wrapper.style.opacity = "";
    drawer.style.transform = "";
  }, 300);
};

const openLogin = () => {
  if (typeof loggedIn === "undefined") return;
  const wrapper = document.getElementById("login-drawer");
  const drawer = wrapper.querySelector("div");

  wrapper.style.backdropFilter = "";
  wrapper.style.opacity = "";
  drawer.style.transform = "";

  wrapper.onclick = () => closeLogin();
  drawer.onclick = (e) => e.stopPropagation();

  wrapper.style.display = "block";
};

// Обработка кнопок
document.getElementById("search-tor").addEventListener("click", () => {
  if (!loggedIn) {
    openLogin();
    return;
  }
  const query = document.getElementById("search").value;
  if (query) {
    window.location.assign(`/search?query=${encodeURIComponent(query)}`);
  } else {
    alert("Введите запрос для поиска.");
  }
});

document.getElementById("open-tiktok").addEventListener("click", () => {
  if (!loggedIn) {
    openLogin();
    return;
  }
  const user = getUser();
  if (user.can_use_tiktok === 0) {
    toaster.show("У вас нет доступа к TikTok", { className: "toast-error" });
    return;
  }
  window.location.assign("/redirect/tiktok");
});

document.getElementById("open-instagram").addEventListener("click", () => {
  if (!loggedIn) {
    openLogin();
    return;
  }
  const user = getUser();
  if (user.can_use_tiktok === 0) {
    toaster.show("У вас нет доступа к Instagram", { className: "toast-error" });
    return;
  }
  window.location.assign("/redirect/instagram");
});

document.getElementById("open-2ip-tor").addEventListener("click", () => {
  if (!loggedIn) {
    openLogin();
    return;
  }
  const user = getUser();
  if (user.can_use_tiktok === 0) {
    toaster.show("У вас нет доступа к 2ip", { className: "toast-error" });
    return;
  }
  window.location.assign("/redirect/2ip"); // Перенаправление на 2ip через TOR
});

document.getElementById("open-2ip-vpn").addEventListener("click", () => {
  if (!loggedIn) {
    openLogin();
    return;
  }
  const user = getUser();
  if (user.can_use_tiktok === 0) {
    toaster.show("У вас нет доступа к 2ip", { className: "toast-error" });
    return;
  }
  window.location.assign("/open_2ip_vpn"); // Перенаправление на 2ip через VPN
});

document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll("nav button");

  const tab = new URLSearchParams(window.location.search).get("tab");
  document.body.setAttribute("tab", tab ?? 1);
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      if (!loggedIn) {
        openLogin();
        return;
      }
      document.body.setAttribute("tab", link.getAttribute("data-tab"));
    });
  });
});
