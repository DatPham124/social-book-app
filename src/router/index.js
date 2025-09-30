import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import Profile from "../views/Profile.vue";
import EditProfile from "../components/EditProfile.vue";
import Register from "../components/RegisterForm.vue";
import ViewAllCurrentlyReadingBook from "../components/ViewAllCurrentlyReadingBook.vue";

const routes = [
  { path: "/login", name: "Login", component: Login },
  { path: "/home", name: "Home", component: Home },
  { path: "/register", name: "register", component: Register },
  { path: "/profile", name: "profile", component: Profile },
  { path: "/profile/edit", name: "edit_profilefile", component: EditProfile },
  { path: "/profile/view/curently", name: "'view_currently_reading_book", component: ViewAllCurrentlyReadingBook },

  { path: "/", redirect: "/login" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
