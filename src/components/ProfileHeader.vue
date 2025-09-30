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
        userInfo = jwtDecode<TokenPayLoad>(token);
        if (userInfo.exp * 1000 < Date.now()) {
            localStorage.removeItem("token");
            userInfo = null;
        }
    } catch (error) {
        console.error("Invalid token:", error);
        localStorage.removeItem("token");
    }
}

const favoriteBooks = ref([""]);


</script>

<template>
    <div class="grid grid-cols-[2fr_1fr]">
        <div class="flex items-center space-x-3">
            <div class="w-20 h-20 rounded-full bg-gray-300 flex items-center justify-center text-3xl text-white">
                👤
            </div>
            <h2 class="text-4xl font-bold text-teal-700">{{ userInfo?.username }}</h2>
            <router-link to="/profile/edit" class="text-gray-400 hover:text-gray-600">
                ✏️
            </router-link>
        </div>


        <div class="p-4 rounded-lg relative">
            <!-- Title -->
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-lg font-semibold text-yellow-600 flex items-center mx-auto">
                    ⭐ Favorites
                </h3>
            </div>

            <!-- Shelf (sách yêu thích) -->
            <div class="flex space-x-3 min-h-[80px]">
                <!-- Nếu có sách thì hiển thị -->
                <template v-if="favoriteBooks.length > 0">
                    <div v-for="book in favoriteBooks.slice(0, 5)" :key="book.id"
                        class="w-14 h-20 rounded overflow-hidden shadow hover:scale-105 transition">
                        <img :src="book.cover" :alt="book.title" class="w-full h-full object-cover" />
                    </div>
                </template>
            </div>

            <!-- Thanh kệ -->
            <div class="mt-3 h-2 bg-yellow-200 rounded"></div>
        </div>

    </div>
</template>