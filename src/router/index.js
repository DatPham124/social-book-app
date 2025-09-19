import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";

const routes = [
    {path: "/login", name: "Login", component: Login},
    {path: "/home", name: "Home", component: Home},
    {path: "/", redirect: "/login"}
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router;