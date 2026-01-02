<script setup lang="ts">
import Navbar from "../layout/Navbar.vue";
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import { USER_SERVICE_URL, AVATAR_SERVER_URL } from "../../config";
import { jwtDecode } from "jwt-decode";

const errorMessage = ref("");
const profile = ref<any>({ full_name: "", bio: "", avatar_url: "" });
const user = ref<any>({ email: "", username: "" });
const finish_update = ref(false)
const popupMessage = ref("");
const isLoading = ref(false);

const isPageLoading = ref(true);

const popup = ref({
    show: false,
    message: '',
    type: 'success' as 'success' | 'error'
});

let popupTimeout: number;
function showPopup(message: string, type: 'success' | 'error' = 'success', duration: number = 3000) {
    clearTimeout(popupTimeout);

    popup.value = { show: true, message, type };

    popupTimeout = window.setTimeout(() => {
        popup.value.show = false;
    }, duration);
}

const selectedFile = ref<File | null>(null);
const avatarPreviewUrl = ref<string | null>(null); 
const fileInput = ref<HTMLInputElement | null>(null); 

const avatarDisplayUrl = computed(() => {
    if (avatarPreviewUrl.value) {
        return avatarPreviewUrl.value;
    }
    if (profile.value?.avatar_url) {
        console.log(profile.value?.avatar_url)
        return `${AVATAR_SERVER_URL}/${profile.value.avatar_url}`;
    }
});

const onFileSelected = (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
        const file = input.files[0];
        // Giới hạn kích thước file (ví dụ: 2MB)
        if (file.size > 2 * 1024 * 1024) {
            errorMessage.value = "Kích thước file không được vượt quá 2MB.";
            return;
        }
        selectedFile.value = file;
        // Tạo URL tạm thời để xem trước ảnh
        avatarPreviewUrl.value = URL.createObjectURL(file);
        errorMessage.value = ""; // Xóa thông báo lỗi cũ
    }
};


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
    isLoading.value = true;
    errorMessage.value = "";

    try {
        await axios.put(`${USER_SERVICE_URL}users/profile/update`, {
            full_name: profile.value.full_name,
            bio: profile.value.bio,
        }, { headers: { Authorization: `Bearer ${token}` } });

        if (selectedFile.value) {
            const formData = new FormData();
            formData.append('file', selectedFile.value);
            const res = await axios.put(`${USER_SERVICE_URL}users/me/avatar`, formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            profile.value.avatar_url = res.data.avatar_url;
        }

        // Gọi hàm showPopup khi thành công
        showPopup("Cập nhật thành công!", 'success');

        selectedFile.value = null;
        avatarPreviewUrl.value = null;

    } catch (error: any) {
        const detail = error.response?.data?.detail || "Lỗi khi lưu thay đổi";
        // Hiển thị lỗi bằng popup thay vì errorMessage
        showPopup(detail, 'error');
    } finally {
        isLoading.value = false;
    }
}

onMounted(async () => {
    isPageLoading.value = true;
    errorMessage.value = "";
    try {
        await Promise.all([
            get_profile_by_user(),
            get_user()
        ]);
    } catch (error) {
        console.error("Failed to fetch initial data:", error);
        errorMessage.value = "Không thể tải dữ liệu. Vui lòng thử lại.";
    } finally {
        isPageLoading.value = false;
    }
});
</script>

<template>
    <Navbar />

    <Transition enter-from-class="opacity-0 translate-y-[-20px]" enter-to-class="opacity-100 translate-y-0"
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-300 ease-in" leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-[-20px]">
        <div v-if="popup.show" class="fixed top-5 right-5 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-semibold"
            :class="{
                'bg-green-500': popup.type === 'success',
                'bg-red-500': popup.type === 'error'
            }">
            {{ popup.message }}
        </div>
    </Transition>

    <div class="max-w-4xl mx-auto mt-5">
        <p class="text-xl font-bold text-yellow-500">Quản lý tài khoản</p>

        <div v-if="isPageLoading" class="border mt-5 rounded-md shadow-md p-10 text-center text-gray-500">
            <p>⏳ Đang tải dữ liệu tài khoản...</p>
        </div>


        <div v-else class="border mt-5 rounded-md shadow-md">
            <p class="text-lg font-semibold border-b px-5 py-3">Thông tin chi tiết</p>

            <form @submit.prevent="save_changes" class="m-5 space-y-5">
                <div>
                    <label for="email" class="block text-sm font-medium">Email</label>
                    <input id="email" type="email" v-model="user.email"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Nhập email" disabled />
                </div>

                <div>
                    <label for="username" class="block text-sm font-medium">Tên người dùng</label>
                    <input id="username" type="text" v-model="user.username"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Tên người dùng" disabled />
                </div>

                <div>
                    <label for="full_name" class="block text-sm font-medium">Họ và tên</label>
                    <input id="full_name" type="text" v-model="profile.full_name"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Nhập họ tên" />
                </div>

                <div>
                    <label for="bio" class="block text-sm font-medium">Tiểu sử</label>
                    <textarea id="bio" rows="3" v-model="profile.bio"
                        class="mt-1 block w-full rounded-md border border-gray-600 px-3 py-2 focus:border-yellow-500 focus:ring focus:ring-yellow-500"
                        placeholder="Giới thiệu ngắn gọn về bạn..."></textarea>
                </div>

                <div>
                    <label class="block text-sm font-medium">Ảnh đại diện</label>
                    <div class="mt-2 flex items-center space-x-4">
                        <img :src="avatarDisplayUrl" alt="Avatar"
                            class="w-20 h-20 rounded-full object-cover bg-gray-200 border">
                        <input type="file" accept="image/png, image/jpeg, image/jpg" @change="onFileSelected"
                            ref="fileInput" class="hidden">
                        <button type="button" @click="fileInput?.click()"
                            class="px-4 py-2 rounded-md bg-gray-100 text-sm font-medium hover:bg-gray-200 transition">
                            Thay đổi
                        </button>
                    </div>
                </div>

                <p v-if="errorMessage" class="text-red-500 text-sm">{{ errorMessage }}</p>

                <div class="flex justify-end">
                    <button :disabled="isLoading" type="submit"
                        class="px-5 py-2 rounded-md bg-yellow-500 text-black font-semibold hover:bg-yellow-600 transition">
                        <span v-if="isLoading">⏳ Đang lưu thay đổi...</span>
                        <span v-else>Lưu thay đổi</span>
                    </button>
                </div>
            </form>

            <div v-if="finish_update"
                class="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
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
