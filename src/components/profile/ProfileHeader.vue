<script setup lang="ts">
import { onMounted, ref } from "vue";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, USER_SERVICE_URL, AVATAR_SERVER_URL } from "../../config";

const props = defineProps({
    userID: Number
});

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
const profile = ref<any>({});
const friendStatus = ref<string>("none");
let friendID = ref<number | null>(null);
const isLoadingFriendStatus = ref(true);



const hoveringFriend = ref(false);

async function removeFriend() {
    if (!userInfo || !token) {
        alert("Bạn cần đăng nhập để thực hiện thao tác này");
        return;
    }

    if (!confirm("Bạn có chắc muốn xóa bạn bè này không?")) return;

    try {
        const friendId = profile.value.user_id;

        await axios.delete(`${USER_SERVICE_URL}friends/delete/${friendID.value}`, {
            headers: { Authorization: `Bearer ${token}` },
        });

        friendStatus.value = "none";
        alert("Đã xóa bạn bè thành công!");
    } catch (error: any) {
        if (axios.isAxiosError(error)) {
            if (error.response) {
                alert(error.response.data.detail || "Không thể xóa bạn bè");
            } else {
                alert("Không kết nối được đến server");
            }
        } else {
            console.error(error);
        }
    }
}



async function getFavorite(user_id: number) {
    try {
        const response = await axios.get(`${BOOK_SERVICE_URL}books/favorite/${user_id}`);
        return response.data;
    } catch (error: any) {
        console.error("Lỗi lấy favorite:", error);
        return null;
    }
}

async function getBookByID(book_id: number) {
    try {
        const response = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`);
        return response.data;
    } catch (error: any) {
        console.error("Lỗi lấy sách:", error);
        return null;
    }
}

async function fetchFavoriteBook(userId: number) {
    try {
        const favoriteList = await getFavorite(userId);
        if (!favoriteList || favoriteList.length === 0) {
            favoriteBooks.value = [];
            return;
        }
        const books = await Promise.all(favoriteList.map((fav: any) => getBookByID(fav.book_id)));
        favoriteBooks.value = books.filter(b => b);
    } catch (error) {
        console.error("Lỗi khi lấy danh sách sách yêu thích:", error);
        favoriteBooks.value = [];
    }
}

async function get_profile_by_user(userId?: number) {
    try {
        if (userId) {
            const res = await axios.get(`${USER_SERVICE_URL}users/profile/${userId}`);
            profile.value = res.data;
        } else {
            const res = await axios.get(`${USER_SERVICE_URL}users/profile`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            profile.value = res.data;
        }
    } catch (error) {
        console.log("Không thể tải profile: ", error);
    }
}


async function sendFriendRequest() {
    if (!userInfo || !token) {
        alert("Bạn cần đăng nhập để kết bạn");
        return;
    }

    try {
        const friendId = profile.value.user_id;

        const response = await axios.post(
            `${USER_SERVICE_URL}friends/add?friend_id=${friendId}`,
            {},
            {
                headers: { Authorization: `Bearer ${token}` },
            }
        );

        friendStatus.value = "pending";
        alert("Đã gửi lời mời kết bạn!");
    } catch (error: any) {
        if (axios.isAxiosError(error)) {
            if (error.response) {
                alert((error.response.data.detail || "Không thể gửi lời mời"));
            } else {
                alert("Không kết nối được đến server");
            }
        } else {
            console.error(error);
        }
    }
}

async function checkFriendStatus(friendId?: number) {
    if (!token || !userInfo || !friendId) {
        isLoadingFriendStatus.value = false;
        return;
    }

    try {
        const response = await axios.get(
            `${USER_SERVICE_URL}friends/status?friend_id=${friendId}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        friendStatus.value = response.data[0]?.status || "none";
        friendID.value = response.data[0]?.id || null;
    } catch (error) {
        console.error("Không thể kiểm tra trạng thái bạn bè:", error);
    } finally {
        isLoadingFriendStatus.value = false;
    }
}




onMounted(async () => {
    const targetUserID = props.userID ?? userInfo?.user_id;

    if (!targetUserID) {
        console.warn("Không xác định được người dùng.");
        return;
    }

    await get_profile_by_user(props.userID);
    await fetchFavoriteBook(targetUserID);
    await checkFriendStatus(targetUserID);
});
</script>

<template>
    <div class="grid grid-cols-[2fr_1fr]">
        <div class="flex items-center space-x-3">
            <img :src="`${AVATAR_SERVER_URL}/${profile?.avatar_url}`" alt="avatar"
                class="w-20 h-20 rounded-full bg-gray-300 flex items-center justify-center text-3xl text-white" />

            <div class="flex flex-col">
                <div class="flex items-center space-x-2">
                    <h2 class="text-4xl font-bold text-teal-700">
                        {{ profile.username }}
                    </h2>

                    <router-link v-if="profile.user_id === userInfo?.user_id" to="/profile/edit"
                        class="text-gray-400 hover:text-gray-600">
                        ✏️
                    </router-link>
                </div>

                <!-- Ẩn nút khi đang tải -->
                <button
                    v-if="!isLoadingFriendStatus && profile.user_id !== userInfo?.user_id && friendStatus === 'none'"
                    @click="sendFriendRequest"
                    class="mt-2 px-4 py-1 bg-teal-600 text-white rounded-lg shadow hover:bg-teal-700 transition">
                    Kết bạn
                </button>

                <!-- Hoặc hiển thị tạm trạng thái chờ -->
                <div v-if="isLoadingFriendStatus" class="text-gray-400 mt-2">
                    Đang kiểm tra trạng thái...
                </div>


                <button v-else-if="friendStatus === 'pending'" disabled
                    class="mt-2 px-4 py-1 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                    Đã gửi lời mời
                </button>

                <button v-else-if="friendStatus === 'accepted' && profile.user_id !== userInfo?.user_id"
                    @mouseenter="hoveringFriend = true" @mouseleave="hoveringFriend = false" @click="removeFriend"
                    class="mt-2 px-4 py-1 rounded-lg shadow text-white transition-colors duration-300 ease-in-out"
                    :style="{ backgroundColor: hoveringFriend ? '#ef4444' : '#22c55e' }">
                    {{ hoveringFriend ? 'Xóa bạn bè' : 'Bạn bè' }}
                </button>




            </div>
        </div>

        <div class="p-4 rounded-lg relative">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-lg font-semibold text-yellow-600 flex items-center mx-auto">
                    ⭐ Favorites
                </h3>
            </div>

            <div class="flex space-x-3 min-h-[80px]">
                <template v-if="favoriteBooks.length > 0">
                    <div v-for="book in favoriteBooks.slice(0, 5)" :key="book.id"
                        class="w-14 h-20 rounded overflow-hidden shadow hover:scale-105 transition">
                        <router-link :to="{ name: 'book', params: { id: book.id } }">
                            <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
                                class="w-full h-full object-cover" />
                        </router-link>
                    </div>
                </template>
            </div>

            <div class="mt-3 h-2 bg-yellow-200 rounded"></div>
        </div>
    </div>
</template>
