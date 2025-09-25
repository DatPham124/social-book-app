<script setup lang="ts">
import Navbar from "../components/Navbar.vue";
import { onMounted, ref } from "vue";
import axios from "axios";
import { USER_SERVICE_URL } from "../config";
import { jwtDecode } from "jwt-decode";

const errorMessage = ref("");
const profile = ref<any>({ full_name: "", bio: "", avatar_url: "" });
const user = ref<any>({ email: "", username: "" });
const finish_update = ref(false)
const popupMessage = ref(""); 
const isLoading = ref(false);

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

async function get_profile_by_user() {
    try {
        const res = await axios.get(`${USER_SERVICE_URL}users/profile`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        profile.value = res.data;
    } catch (error: unknown) {
        errorMessage.value = "Không thể tải profile";
    }
}

async function get_user() {
    try {
        const res = await axios.get(`${USER_SERVICE_URL}users/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        user.value = res.data;
    } catch (error: unknown) {
        errorMessage.value = "Không thể tải user";
    }
}

async function save_changes() {
    isLoading.value = true

    try {
        await axios.put(`${USER_SERVICE_URL}users/profile/update`, profile.value, {
            headers: { Authorization: `Bearer ${token}` },
        });
        popupMessage.value = "Cập nhật thành công"
        finish_update.value = true
        isLoading.value = false
    } catch (error) {
        errorMessage.value = "Lỗi khi lưu thay đổi";
        isLoading.value = false
    }
}

onMounted(() => {
    get_profile_by_user();
    get_user();
});
</script>

<template>
    <Navbar />

    <div class="max-w-4xl mx-auto mt-5">
        <p class="text-xl font-bold text-yellow-500">Quản lý tài khoản</p>

        <div class="border mt-5 rounded-md shadow-md">
            <p class="text-lg font-semibold border-b px-5 py-3">Thông tin chi tiết</p>

            <form @submit.prevent="save_changes" class="m-5 space-y-5">
                <!-- Email -->
                <div>
                    <label for="email" class="block text-sm font-medium">Email</label>
                    <input id="email" type="email" v-model="user.email"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Nhập email" disabled />
                </div>

                <!-- Username -->
                <div>
                    <label for="username" class="block text-sm font-medium">Tên người dùng</label>
                    <input id="username" type="text" v-model="user.username"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Tên người dùng" disabled />
                </div>

                <!-- Full name -->
                <div>
                    <label for="full_name" class="block text-sm font-medium">Họ và tên</label>
                    <input id="full_name" type="text" v-model="profile.full_name"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Nhập họ tên" />
                </div>

                <!-- Bio -->
                <div>
                    <label for="bio" class="block text-sm font-medium">Tiểu sử</label>
                    <textarea id="bio" rows="3" v-model="profile.bio"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Giới thiệu ngắn gọn về bạn..."></textarea>
                </div>

                <!-- Avatar -->
                <div>
                    <label for="avatar" class="block text-sm font-medium">Avatar URL</label>
                    <input id="avatar" type="text" v-model="profile.avatar_url"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Link ảnh đại diện" />
                </div>

                <!-- Nút lưu -->
                <div class="flex justify-end">
                    <button :disabled="isLoading" type="submit"
                        class="px-5 py-2 rounded-md bg-yellow-500 text-black font-semibold hover:bg-yellow-600 transition">
                        <span v-if="isLoading">⏳ Đang lưu thay đổi .....</span>
                        <span v-else>Lưu thay đổi</span>
                    </button>
                </div>
            </form>

            <!-- Popup -->
            <div v-if="finish_update" class="fixed inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-50">
                <div class="bg-white rounded-lg shadow-lg p-6 w-80 text-center">
                    <p class="text-lg font-semibold text-gray-800">{{ popupMessage }}</p>
                    <button
                        class="mt-4 px-4 py-2 bg-yellow-500 text-black font-semibold rounded-md hover:bg-yellow-600 transition"
                        @click="finish_update = false">
                        Đóng
                    </button>
                </div>
            </div>



        </div>
    </div>
</template>
