<script setup lang="ts">
import { ref } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const router = useRouter();

async function login() {
    try {
        const response = await axios.post("http://localhost:8000/users/token",
            new URLSearchParams({
                username: username.value,
                password: password.value
            }),
            {
                headers: { "Content-Type": "application/x-www-form-urlencoded" }
            }
        );

        console.log("Response:", response.data);

        const { access_token } = response.data;
        localStorage.setItem("token", access_token);

        router.push('/home');
    }
    catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            if (error.response.status === 401 || error.response.status === 400) {
                errorMessage.value = "Tên đăng nhập hoặc mật khẩu không hợp lệ."
            } else {
                errorMessage.value = `Đã xảy ra lỗi: ${error.response.statusText}`;
            }
        } else {
            errorMessage.value = "Không thể kết nối đến máy chủ. Vui lòng thử lại sau.";
        }
        console.error(error);
    }
}
</script>

<template>

    <form @submit.prevent="login" class="space-y-4">
        <input type="text" placeholder="Username" v-model="username"
            class="w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-400" />
        <input type="password" placeholder="Password" v-model="password"
            class="w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-400" />

        <button
            class="w-full py-2 rounded-lg bg-yellow-400 text-gray-900 font-semibold hover:bg-yellow-500 transition duration-200">
            Login
        </button>
        <p v-if="errorMessage" class="text-red-500 text-sm">{{ errorMessage }}</p>
    </form>

</template>
