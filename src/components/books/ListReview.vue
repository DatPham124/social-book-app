<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import Navbar from "../../components/layout/Navbar.vue";
import { COVER_IMAGE_SERVER_URL, REVIEW_SERVICE_URL, USER_SERVICE_URL, AVATAR_SERVER_URL } from "../../config";
import axios from "axios";
import { useAuth } from "../../composables/useAuth";
import { useBooks } from "../../composables/useBook";

const { userInfo } = useAuth()


const userID_from_token = computed(() => userInfo.value?.user_id);

const { getBookById } = useBooks();
const route = useRoute();

const expanded = ref<Record<number, boolean>>({});
const bookId = Number(route.params.id);
const book = ref<any>(null);
const reviews = ref<any[]>([]);
const profile = ref<any[]>([]);
const average = ref<number>(0);
const loading = ref(true);
const error = ref<string | null>(null);

function renderStars(rating: number) {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

    for (let i = 0; i < fullStars; i++) stars.push("full");
    if (hasHalf) stars.push("half");
    for (let i = 0; i < emptyStars; i++) stars.push("empty");
    return stars;
}

async function getReview(bookId: number) {
    try {
        const response = await axios.get(`${REVIEW_SERVICE_URL}review/book/${bookId}`);
        return response.data;
    }
    catch (error) {
        console.log("Lỗi khi lấy dữ liệu đánh giá: ", error)
    }
}

async function getProfile(userId: number) {
    try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
            `${USER_SERVICE_URL}users/profile/${userId}`,
            {
                headers: { Authorization: `Bearer ${token}` },
            },
        );
        return response.data;
    } catch (error) {
        console.log("Lỗi khi lấy dữ liệu người dùng:", error);
    }
}

onMounted(async () => {
    try {
        loading.value = true;

        book.value = await getBookById(bookId);

        reviews.value = await getReview(bookId);

        const profilePromise = reviews.value.map(r => getProfile(r.user_id));

        const profile = await Promise.all(profilePromise);


        reviews.value = reviews.value.map((r, index) => ({
            ...r,
            user: profile[index]
        }))

        console.log(reviews.value)

        const sum = reviews.value.reduce((acc, r) => acc + r.rating, 0);
        average.value = reviews.value.length ? sum / reviews.value.length : 0;
    } catch (err) {
        console.error(err);
        error.value = "Lỗi khi tải dữ liệu.";
    } finally {
        loading.value = false;
    }
});
</script>


<template>
    <Navbar />

    <div class="max-w-5xl mx-auto px-6 py-10">
        <div v-if="loading" class="text-center text-gray-500 py-12">Đang tải dữ liệu...</div>
        <div v-else-if="error" class="text-center text-red-500 py-12">{{ error }}</div>

        <div v-else>
            <!-- Thông tin sách -->
            <div class="flex items-center gap-6 border-b pb-6 mb-8">
                <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" alt="Bìa sách"
                    class="w-28 h-40 object-cover rounded-md shadow-sm" />

                <div>
                    <p class="text-sm text-gray-500 font-semibold uppercase">
                        {{ reviews.length }} đánh giá cho:
                    </p>
                    <h1 class="text-2xl font-bold text-gray-900">{{ book.title }}</h1>
                    <p class="text-gray-600 mt-1">{{ book.author || "Tác giả không xác định" }}</p>

                    <div class="flex items-center gap-2 mt-3">
                        <span class="text-yellow-500 text-lg">★</span>
                        <span class="text-lg font-semibold text-gray-800">{{ average.toFixed(2) }}</span>
                        <span class="text-gray-500 text-sm">trung bình</span>
                    </div>
                </div>
            </div>

            <!-- Danh sách đánh giá -->
            <div class="space-y-6">
                <div v-for="(review, index) in reviews" :key="index" class="bg-white border rounded-lg p-6 shadow-sm">
                    <div class="flex items-start gap-3 mb-3">
                        <router-link :to="{ name: 'profile', params: { id: review.user_id } }">

                            <div
                                class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm">
                                <template v-if="review.user?.avatar_url">
                                    <img :src="`${AVATAR_SERVER_URL}/${review.user.avatar_url}`" alt="Avatar người dùng"
                                        class="w-full h-full object-cover" />
                                </template>
                                <template v-else>
                                    {{ review.user?.username?.charAt(0)?.toUpperCase() || "U" }}
                                </template>
                            </div>
                        </router-link>

                        <div class="flex flex-col flex-1">
                            <router-link :to="{ name: 'profile', params: { id: review.user_id } }">

                                <p class="font-semibold text-gray-800">
                                    {{ review.user?.username || "Người dùng ẩn danh" }} <span
                                        class="text-gray-500 text-sm font-normal">đánh
                                        giá</span>
                                </p>
                            </router-link>

                            <div class="flex items-center gap-1 text-yellow-500 text-sm mt-1">
                                <template v-for="(type, i) in renderStars(review.rating)" :key="i">
                                    <font-awesome-icon v-if="type === 'full'" icon="fa-solid fa-star" />
                                    <font-awesome-icon v-else-if="type === 'half'" icon="fa-solid fa-star-half-alt" />
                                    <font-awesome-icon v-else icon="fa-regular fa-star" />
                                </template>
                                <span class="text-gray-700 ml-1 text-sm font-medium">{{ review.rating.toFixed(1)}}</span>
                            </div>

                        </div>

                        <router-link :to="{ name: 'DetailReview', params: { bookId: bookId, reviewId: review.id } }"
                            v-if="review.user_id === userID_from_token"
                            class="text-gray-400 hover:text-yellow-500 transition transform hover:scale-110"
                            title="Chỉnh sửa đánh giá">
                            <font-awesome-icon icon="fa-solid fa-circle-arrow-right" class="text-2xl" />
                            </ router-link>
                    </div>
                    <p class="text-gray-700 text-sm leading-relaxed mb-3 transition-all duration-300"
                        :class="!expanded[index] ? 'line-clamp-3' : ''">
                        {{ review.content || "Người dùng này không để lại bình luận nào." }}
                    </p>
                    <!-- Nút xem thêm / ẩn bớt -->
                    <button v-if="review.content?.length > 150"
                        class="text-sm text-yellow-600 hover:text-yellow-700 font-semibold transition-colors"
                        @click="expanded[index] = !expanded[index]">
                        {{ expanded[index] ? 'Ẩn bớt' : 'Xem thêm' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

    <style scoped></style>