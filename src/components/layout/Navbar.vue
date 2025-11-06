<script lang="ts" setup>
import { onMounted, ref } from "vue"
import { jwtDecode } from "jwt-decode"
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { AVATAR_SERVER_URL, USER_SERVICE_URL } from '../../config'
import axios from "axios"
interface TokenPayLoad {
    username: string
    roles: number[]
    exp: number
    user_id: number
}

const token = localStorage.getItem("token")
let userInfo: TokenPayLoad | null = null

if (token) {
    try {
        userInfo = jwtDecode<TokenPayLoad>(token);
        if (userInfo.exp * 1000 < Date.now()) {
            localStorage.removeItem('token');
            userInfo = null;
        }
    } catch (error) {
        console.error("Invalid token:", error);
        localStorage.removeItem('token');
    }
}

const signOut = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
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
    await get_profile_by_user()
}
)
</script>



<template>
    <nav class="bg-white shadow-md">
        <div class="mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center mx-10">
                <div class="flex space-x-8 item-center">
                    <h1 class="text-2xl font-logo text-yellow-500 item-center">📚 Social Book</h1>
                    <div class="hidden md:flex space-x-6 items-center">
                        <router-link to="/home" class="text-gray-700 hover:text-yellow-500">Trang chủ</router-link>
                        <router-link :to="{ name: 'StatisticsTab', params: { id: userInfo?.user_id } }"
                            class="text-gray-700 hover:text-yellow-500">Thống kê
                        </router-link>
                        <router-link to="/community" class="text-gray-700 hover:text-yellow-500">Cộng đồng</router-link>
                        <router-link to="/friends" class="text-gray-700 hover:text-yellow-500">Bạn bè</router-link>
                    </div>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                            <font-awesome-icon icon="fa-solid fa-magnifying-glass" />
                        </span>
                        <input type="text" placeholder="Tìm kiếm sách, bạn bè..."
                            class="pl-10 border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-yellow-500 w-full">
                    </div>
                </div>

                <div v-if="userInfo" class="relative">
                    <Menu as="div">
                        <MenuButton
                            class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                            <span class="sr-only">Open user menu</span>
                            <img :src="`${AVATAR_SERVER_URL}/${profile?.avatar_url}`" alt="avatar"
                                class="w-10 h-10 rounded-full border border-gray-300">
                        </MenuButton>

                        <transition enter-active-class="transition ease-out duration-100"
                            enter-from-class="transform opacity-0 scale-95"
                            enter-to-class="transform opacity-100 scale-100"
                            leave-active-class="transition ease-in duration-75"
                            leave-from-class="transform opacity-100 scale-100"
                            leave-to-class="transform opacity-0 scale-95">
                            <MenuItems
                                class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                <div class="px-4 py-2 text-sm text-gray-700 border-b">
                                    <strong class="font-medium">{{ userInfo.username }}</strong>
                                </div>
                                <MenuItem v-slot="{ active }">
                                <router-link :to="{ name: 'profile', params: { id: userInfo.user_id } }"
                                    :class="[active ? 'bg-yellow-100' : '', 'block px-4 py-2 text-sm text-gray-700']">
                                    Hồ sơ của bạn
                                </router-link>
                                </MenuItem>
                                <MenuItem v-slot="{ active }">
                                <router-link :to="{ name: 'Notification' }"
                                    :class="[active ? 'bg-yellow-100' : '', 'block px-4 py-2 text-sm text-gray-700']">
                                    Thông báo
                                </router-link>
                                </MenuItem>
                                <MenuItem v-slot="{ active }">
                                <router-link to="/settings"
                                    :class="[active ? 'bg-yellow-100' : '', 'block px-4 py-2 text-sm text-gray-700']">
                                    Cài đặt
                                </router-link>
                                </MenuItem>
                                <MenuItem v-slot="{ active }">
                                <button @click="signOut"
                                    :class="[active ? 'bg-yellow-100' : '', 'block w-full text-left px-4 py-2 text-sm text-gray-700']">
                                    Đăng xuất
                                </button>
                                </MenuItem>
                            </MenuItems>
                        </transition>
                    </Menu>
                </div>
                <div v-else>
                    <router-link to="/login" class="text-gray-700 hover:text-yellow-500">Đăng nhập</router-link>
                </div>
            </div>
        </div>
    </nav>
</template>
