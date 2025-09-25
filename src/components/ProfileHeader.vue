<script setup lang="ts">
import { ref } from "vue";
import { jwtDecode } from "jwt-decode"

interface TokenPayLoad {
    username: string;
    roles: number[];
    exp: number;
    user_id: number;
}

const token = localStorage.getItem("token");
let userInfo: TokenPayLoad | null = null;

if (token) {
    try {
        userInfo = jwtDecode < TokenPayLoad > (token);
        if (userInfo.exp * 1000 < Date.now()) {
            localStorage.removeItem("token");
            userInfo = null;
        }
    } catch (error) {
        console.error("Invalid token:", error);
        localStorage.removeItem("token");
    }
}

</script>

<template>
    <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <div class="w-16 h-16 rounded-full bg-gray-300 flex items-center justify-center text-3xl text-white">
                👤
            </div>
            <h2 class="text-2xl font-bold text-teal-700">{{userInfo?.username}}</h2>
            <router-link to="/profile/edit" class="text-gray-400 hover:text-gray-600">
                ✏️
            </router-link>
        </div>
        <div class="flex items-center text-yellow-500 font-medium text-lg">
            ⭐ Favorites ⭐
        </div>
    </div>
</template>