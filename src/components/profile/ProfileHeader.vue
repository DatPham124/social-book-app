<script setup lang="ts">
import { onMounted, ref } from "vue";
import { jwtDecode } from "jwt-decode"
import axios from "axios";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, USER_SERVICE_URL, AVATAR_SERVER_URL } from "../../config";


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
const favoriteBooks = ref<any[]>([]);
async function getFavorite(user_id: number) {
    try {
        const response = await axios.get(`${BOOK_SERVICE_URL}books/favorite/${user_id}`);
        return response.data;

    }
    catch (error: any) {
        if (axios.isAxiosError(error)) {
            if (error.response) {
                console.error("Server trả lỗi:", error.response.data);
            } else if (error.request) {
                console.error("Không kết nối được đến server");
            }
        } else {
            console.error("Lỗi không xác định:", error);
        }
        return null;
    }
}

async function getBookByID(book_id: number) {
    try {
        const respone = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`)
        return respone.data
    }
    catch (error: any) {
        if (axios.isAxiosError(error)) {
            if (error.response) {
                console.error("Server trả lỗi:", error.response.data);
            } else if (error.request) {
                console.error("Không kết nối được đến server");
            }
        } else {
            console.error("Lỗi không xác định:", error);
        }
        return null;
    }
}

async function fetchFavoriteBook(userId: number) {
    try {
        // Lấy danh sách book_id từ bảng favorite
        const favoriteList = await getFavorite(userId);

        if (!favoriteList || favoriteList.length === 0) {
            favoriteBooks.value = [];
            return;
        }

        // Gọi API lấy chi tiết sách cho tất cả book_id song song
        const books = await Promise.all(
            favoriteList.map((fav: any) => getBookByID(fav.book_id))
        );

        // Lọc bỏ null (trường hợp API lỗi)
        favoriteBooks.value = books.filter(b => b);
    } catch (error) {
        console.error("Lỗi khi lấy danh sách sách yêu thích:", error);
        favoriteBooks.value = [];
    }
}

const profile = ref<any>(null)

async function get_profile_by_user() {
    try {
        const res = await axios.get(`${USER_SERVICE_URL}users/profile`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        profile.value = res.data;
    } catch (error: unknown) {
        console.log("Không thể tải profile");
    }
}


onMounted(async () => {
    if (userInfo?.user_id) {
        await get_profile_by_user()
        await fetchFavoriteBook(userInfo.user_id);
    }
});



</script>

<template>
    <div class="grid grid-cols-[2fr_1fr]">
        <div class="flex items-center space-x-3">
            <img :src="`${AVATAR_SERVER_URL}/${profile?.avatar_url}`" alt="avatar"
                class="w-20 h-20 rounded-full bg-gray-300 flex items-center justify-center text-3xl text-white">

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
                        <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
                            class="w-full h-full object-cover" />
                    </div>
                </template>
            </div>

            <!-- Thanh kệ -->
            <div class="mt-3 h-2 bg-yellow-200 rounded"></div>
        </div>

    </div>
</template>