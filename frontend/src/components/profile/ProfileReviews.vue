<script setup lang="ts">
// ĐẢM BẢO DÒNG IMPORT NÀY CÓ ĐẦY ĐỦ: ref, onMounted, computed, watch
import { ref, onMounted, computed, watch } from 'vue'; 
import axios from 'axios';
import { REVIEW_SERVICE_URL } from '../../config'; 

// Props userID nhận từ component cha
const props = defineProps<{
    userID: number;
}>();

const loading = ref(true);
const error = ref<string | null>(null);
const stats = ref({
    total_reviews: 0,
    distribution: {
        one_star: 0, two_star: 0, three_star: 0, four_star: 0, five_star: 0
    }
});

// Sử dụng computed để tự động tính toán dữ liệu cho biểu đồ
const bars = computed(() => [
    { stars: 1, count: stats.value.distribution.one_star },
    { stars: 2, count: stats.value.distribution.two_star },
    { stars: 3, count: stats.value.distribution.three_star },
    { stars: 4, count: stats.value.distribution.four_star },
    { stars: 5, count: stats.value.distribution.five_star },
]);

const maxCount = computed(() => {
    const counts = bars.value.map(b => b.count);
    const max = Math.max(...counts);
    return max === 0 ? 1 : max; 
});

const MAX_BAR_HEIGHT_PX = 90;

function getBarHeight(count: number) {
    const height = (count / maxCount.value) * MAX_BAR_HEIGHT_PX;
    if (height === 0) return '1px'; 
    return `${height}px`; 
}

async function loadStats() {
    if (!props.userID) return;
    loading.value = true;
    error.value = null; 
    
    try {
        const res = await axios.get(`${REVIEW_SERVICE_URL}review/stats/user-distribution/${props.userID}`);
        stats.value = res.data;
    } catch (err: any) {
        error.value = "Lỗi tải đánh giá";
        stats.value = {
            total_reviews: 0,
            distribution: { one_star: 0, two_star: 0, three_star: 0, four_star: 0, five_star: 0 }
        };
    } finally {
        loading.value = false;
    }
}

onMounted(loadStats);

// Watch để reload khi userID thay đổi
watch(() => props.userID, () => {
    loadStats();
});
</script>

<template>
    <div class="bg-white p-4 rounded-lg shadow border">
        <div class="flex justify-between items-center border-gray-200 pb-2 mb-3">
            <h3 class="text-sm font-semibold text-gray-800 uppercase">REVIEWS</h3>
            <router-link :to="{ name: 'view_all_reviews', params: { id: props.userID } }"
                class="text-sm text-yellow-600 hover:text-yellow-800">
                {{ stats.total_reviews }} &rarr;
            </router-link>
        </div>

        <div v-if="loading" class="text-center text-gray-500 py-4 italic text-sm">
            Đang tải...
        </div>
        <div v-else-if="error" class="text-center text-red-500 py-4 italic text-sm">
            {{ error }}
        </div>
        <div v-else-if="stats.total_reviews === 0" class="text-center text-gray-500 py-4 italic text-sm">
            Chưa có đánh giá nào.
        </div>

        <div v-else class="flex items-end justify-center gap-2 h-24 mt-5">
            <div v-for="bar in bars" :key="bar.stars" 
                 class="flex flex-col items-center w-full relative group">
                <div class="absolute bottom-full mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded-md shadow-lg
                            opacity-0 invisible group-hover:visible group-hover:opacity-100 
                            transition-opacity duration-200 whitespace-nowrap z-10">
                    {{ bar.count }} đánh giá {{ bar.stars }} sao
                    <div class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0
                                border-l-4 border-l-transparent
                                border-r-4 border-r-transparent
                                border-t-4 border-t-gray-900"></div>
                </div>
                <div class="w-3/4 bg-yellow-200 rounded-t transition-all duration-500"
                    :style="{ height: getBarHeight(bar.count) }"></div>
                <span class="text-xs text-gray-400 mt-1">{{ bar.stars }}★</span>
            </div>
        </div>
    </div>
</template>